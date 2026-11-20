#!/usr/bin/env python3
"""知識ベース(my-notes-template から作った notes)の記事としくみを管理するスクリプト。

このファイルは「共通の部分」です。各 notes では直さず、テンプレートで直して
`python3 notes.py update` で取りこみます(詳しくは KB_GUIDE.md)。

使い方:
    python3 notes.py status [--todo] [--thirdparty]   記事の一覧と、テンプレートの版を表示する
    python3 notes.py check                            記事・自動で作る部分・共通の部分を検査する
    python3 notes.py sync                             README・index.md の決まった部分・目次・_config.yml を作り直す
    python3 notes.py toc                              sync と同じ(以前の名前)
    python3 notes.py new SLUG TITLE [SUMMARY]         テンプレートから新しい記事を作る
    python3 notes.py verify FILE VALUE                記事の verified を変え、checked を今日にする
    python3 notes.py init --name ... --subject ...    テンプレートのコピーを、新しい notes として始める
    python3 notes.py update [--from 場所] [--yes]      テンプレートから共通の部分の最新版を取りこむ

外部ライブラリは使わない(Python 3 の標準機能だけで動く)。update は git を使う。
"""

import argparse
import datetime
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
README = ROOT / "README.md"
INDEX = ROOT / "index.md"  # GitHub Pages のトップページ
TEMPLATE = DOCS / "_template.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
SITE_CONFIG = ROOT / "_config.yml"
KB_JSON = ROOT / "_data" / "kb.json"  # notes ごとの設定(題材の名前など)。サイトからも site.data.kb で読める
MANIFEST = ROOT / "kb-engine.json"  # 共通の部分のファイルの一覧
LOCK = ROOT / ".kb-engine-lock.json"  # 取りこんだテンプレートの版と、共通の部分の中身の記録(update が書く)

REQUIRED = ["title", "summary", "keywords", "checked", "verified", "source"]
# thirdparty も必須だが、空のリスト [] を許すので REQUIRED とは別に検査する
VERIFIED_VALUES = ["実機", "一部実機", "ネットのみ"]
STALE_DAYS = 180  # checked がこれより古ければ警告する

TOC_START = "<!-- toc:start -->"
TOC_END = "<!-- toc:end -->"
AI_START = "<!-- kb:ai:start -->"
AI_END = "<!-- kb:ai:end -->"
MANAGE_START = "<!-- kb:manage:start -->"
MANAGE_END = "<!-- kb:manage:end -->"
ASK_START = "<!-- kb:ask:start -->"
ASK_END = "<!-- kb:ask:end -->"
# 「AIに質問する使い方」を置く見出し。決まった部分(ASK_START〜ASK_END)は、この見出しのすぐ下に置く
INDEX_ASK_HEADING = "## AIに質問する使い方"
README_ASK_HEADING = "## 使い方(人間向け)"

KB_KEYS = ["name", "subject", "owner_org", "support_name", "support_url", "description",
           "github", "author", "template_repo", "is_template"]

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FILENAME_RE = re.compile(r"^(\d{2})-[a-z0-9-]+\.md$")
# YAML では、この文字で始まる値は引用符で囲まないとエラーになる(GitHub Pages のビルドが失敗する)
YAML_RESERVED_START = "@`!&*|>%{}"


# ---------------------------------------------------------------- 設定

def kb():
    """_data/kb.json(notes ごとの設定)を読む。"""
    if not KB_JSON.exists():
        sys.exit(f"エラー: {rel(KB_JSON)} がない。テンプレートから作ったリポジトリか確認する")
    data = json.loads(KB_JSON.read_text(encoding="utf-8"))
    missing = [k for k in KB_KEYS if k not in data]
    if missing:
        sys.exit(f"エラー: {rel(KB_JSON)} に {', '.join(missing)} がない(KB_GUIDE.md の「設定ファイル」を参照)")
    return data


def notice_phrase(conf):
    """外部サービスを扱う記事の注意書きに必ず入れる文言。"""
    return f"{conf['subject']}の公式機能ではありません"


def github_parts(conf):
    """"owner/repo" から (owner, repo) を返す。"""
    owner, _, repo = conf["github"].partition("/")
    return owner, repo


def site_url(conf):
    """GitHub Pages のサイトの URL(末尾に / 付き)。"""
    owner, repo = github_parts(conf)
    return f"https://{owner}.github.io/{repo}/"


# ---------------------------------------------------------------- 読み書き

def unquote(value):
    """前後の引用符("..." または '...')を取り除く。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """記事冒頭の frontmatter を辞書にする。

    このリポジトリで使う書き方だけに対応する:
      key: 値
      key: [a, b, c]
      key:
        - 値
        - 値
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    data = {}
    current = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s*(.*)$", line)
        if item and current is not None:
            if not isinstance(data[current], list):
                data[current] = []
            data[current].append(unquote(item.group(1).strip()))
            continue
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            value = [unquote(v.strip()) for v in value[1:-1].split(",") if v.strip()]
        else:
            value = unquote(value)
        data[key] = value
        current = key
    return data


def yaml_unsafe_values(text):
    """frontmatter の中で、引用符なしで YAML の予約文字から始まる値を返す。"""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    values = []
    for line in m.group(1).splitlines():
        item = re.match(r"^\s+-\s*(.*)$", line)
        kv = re.match(r"^[A-Za-z_]+:\s*(.*)$", line)
        raw = item.group(1) if item else kv.group(1) if kv else ""
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            values += [v.strip() for v in raw[1:-1].split(",")]
        else:
            values.append(raw)
    return [v for v in values if v and v[0] in YAML_RESERVED_START]


def quoted_end(raw, i):
    """raw[i] の引用符で始まる文字列の、閉じる引用符の次の位置を返す。閉じていなければ None。"""
    q = raw[i]
    j = i + 1
    while j < len(raw):
        if q == '"' and raw[j] == "\\":
            j += 2
            continue
        if raw[j] == q:
            if q == "'" and raw[j + 1:j + 2] == "'":  # '' は ' そのもの
                j += 2
                continue
            return j + 1
        j += 1
    return None


def unclosed_problem(raw):
    """値の書き方の崩れ(括弧や引用符の閉じ忘れ)を一言で返す。問題がなければ None。

    値が [ { " ' で始まるときだけ見る。途中の ' や " は(it's など)ふつうの文字なので見ない。
    """
    if not raw or raw[0] not in "[{\"'":
        return None
    if raw[0] in "\"'":
        end = quoted_end(raw, 0)
        if end is None:
            return f"引用符 {raw[0]} が閉じていない"
        rest = raw[end:].strip()
        if rest and not rest.startswith("#"):
            return f"閉じた引用符 {raw[0]} のあとに「{rest}」が続いている"
        return None
    pairs = {"[": "]", "{": "}"}
    stack = []
    at_start = True  # 要素の書き始め(引用符を開く位置)かどうか
    i = 0
    while i < len(raw):
        c = raw[i]
        if c in "\"'" and at_start:
            end = quoted_end(raw, i)
            if end is None:
                return f"引用符 {c} が閉じていない"
            i, at_start = end, False
            continue
        if c in pairs:
            stack.append(pairs[c])
            at_start = True
        elif c in "]}":
            if not stack or stack.pop() != c:
                return f"閉じる {c} に対応する開く括弧がない"
            at_start = False
            if not stack:
                rest = raw[i + 1:].strip()
                if rest and not rest.startswith("#"):
                    return f"閉じた {c} のあとに「{rest}」が続いている"
                return None
        elif c in ",:":
            at_start = True
        elif not c.isspace():
            at_start = False
        i += 1
    return f"{raw[0]} を閉じる {pairs[raw[0]]} がない"


def yaml_syntax_problems(text):
    """frontmatter の各行で、括弧や引用符の閉じ忘れを (行の中身, 問題) の組で返す。"""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    problems = []
    for line in m.group(1).splitlines():
        item = re.match(r"^\s+-\s*(.*)$", line)
        kv = re.match(r"^[A-Za-z_]+:\s*(.*)$", line)
        raw = (item.group(1) if item else kv.group(1) if kv else "").strip()
        problem = unclosed_problem(raw)
        if problem:
            problems.append((line.strip(), problem))
    return problems


def articles():
    """docs/ の記事(_ で始まるファイルを除く)を番号順に返す。"""
    return sorted(p for p in DOCS.glob("*.md") if not p.name.startswith("_"))


def load(path):
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def today():
    return datetime.date.today()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- 自動で作る部分

def build_toc():
    """README 用の目次(ファイル名と説明)。AI がファイル名で記事を探せるようにする。"""
    lines = ["| ファイル | 内容 |", "|---|---|"]
    for path in articles():
        fm = load(path) or {}
        summary = fm.get("summary") or fm.get("title") or ""
        lines.append(f"| `{rel(path)}` | {summary} |")
    return "\n".join(lines)


def build_index_toc():
    """index.md(サイトのトップ)用の目次。記事へのリンク付き。"""
    lines = ["| 記事 | 内容 |", "|---|---|"]
    for path in articles():
        fm = load(path) or {}
        title = fm.get("title") or path.stem
        summary = fm.get("summary") or ""
        lines.append(f"| [{title}]({rel(path)}) | {summary} |")
    return "\n".join(lines)


def build_ai_block(conf):
    """README の「AIへの指示」の中身。題材の名前だけが notes ごとに変わる。"""
    s = conf["subject"]
    return f"""このリポジトリを参照して質問に答えるときは、以下の手順とルールに従ってください。

### 手順

1. 下の「目次」を見て、質問に関係しそうな記事を選ぶ
2. 目次で見つからなければ `docs/` を `grep` でキーワード検索する(各記事の冒頭に `keywords` があります)
3. 該当する記事を読んで回答する

### 回答のルール

- **このリポジトリに書いてあることを優先**して答える。一般知識で補った部分は「マニュアル外の補足」と明記する
- 回答の最後に、**参照した記事のファイル名**を示す
- 回答の最後に、非公式の個人メモであり、正確な情報は公式サポートで確認するよう一言添える
- 各記事の `checked`(確認日)が古い場合、{s}の仕様が変わっている可能性があることを一言添える
- 記事の `verified` が「ネットのみ」の場合は、実機では未確認の情報であることを一言添える
- 記事の `thirdparty` にサービス名がある場合、そのサービスについて答えるときは、**{s}の公式機能ではない外部サービスであること**を必ず伝える。公式機能と誤解される言い方をしない
- マニュアルに書いていない内容は、無理に答えず「マニュアルには記載がない」と伝える
- 日本語で答える。{s}の画面上の名前は「」で囲む"""


def build_manage_block(conf):
    """README の「記事の管理」の中身。"""
    return """記事の追加や確認には、プロジェクトルートの `notes.py` を使います。Python 3 だけで動きます(追加のインストールは不要)。

| コマンド | やること |
|---|---|
| `python3 notes.py status` | 記事の一覧を、`verified` と `checked` 付きで表示する(`--todo` で未確認の記事だけ、`--thirdparty` で外部サービスの記事だけ) |
| `python3 notes.py check` | 記事の書き方、自動で作る部分、共通の部分が手で直されていないかを検査する |
| `python3 notes.py sync` | README の決まった部分・目次、`index.md` の記事一覧と「AIに質問する使い方」、`_config.yml` を作り直す |
| `python3 notes.py new SLUG タイトル [説明]` | テンプレートから新しい記事を作り、目次にも追加する |
| `python3 notes.py verify ファイル 値` | 記事の `verified` を変えて、`checked` を今日の日付にする |
| `python3 notes.py update` | テンプレートから共通の部分(`notes.py` など)の最新版を取りこむ |

**このリポジトリのしくみ、記事の書き方のルール、作業のルール(人間・AIとも)は [KB_GUIDE.md](KB_GUIDE.md) にあります。** 記事を書く・直す前に読んでください。"""


def build_ask_block(conf, for_readme=False):
    """「AIに質問する使い方」の中身(index.md と README の「使い方(人間向け)」)。

    簡単な方法(ウェブを読める AI チャットに、サイトの URL と質問を渡す)を先に書く。
    サイトだけを読んだ AI は README の「AIへの指示」を知らないので、index.md には短い回答のルールも載せる。
    """
    s = conf["subject"]
    url = site_url(conf)
    # 質問の例。_data/kb.json の ask_example(省略できる)があれば、それを使う
    q = conf.get("ask_example") or "(聞きたいこと)"
    simple = f"""ウェブのページを読める AI チャットに、{'サイト' if for_readme else 'このサイト'}の URL と質問を渡すだけで、記事をもとに答えてもらえます。

> 次のページをもとに教えて。{q}  
> {url}

- リンクを貼ったときに出るページ名だけでは、AI には伝わりません。**URL(https:// で始まる文字)を必ず書きます**
- AI が記事を読みちがえることもあります。大事なことは、答えに出てきた記事を開いて確かめてください"""

    rules = f"""

### AIへのお願い(このページを読んだ AI へ)

このサイトをもとに質問に答えるときは、次のルールに従ってください。

- 上の「記事一覧」から質問に関係する記事を選んで読み、**記事に書いてあることを優先**して答える。一般知識で補った部分は「サイト外の補足」と明記する
- 回答の最後に、**参照した記事のタイトルと URL** を示す
- 回答の最後に、非公式の個人メモであり、正確な情報は{conf['support_name']}で確認するよう一言添える
- 記事の「確認日」が古いときは、{s}の仕様が変わっている可能性があることを一言添える
- 記事が「実機では未確認(ネットの情報のみ)」のときは、実機では未確認の情報であることを一言添える
- 外部サービスについて答えるときは、**{s}の公式機能ではない外部サービスであること**を必ず伝える。公式機能と誤解される言い方をしない
- サイトに書いていないことは、無理に答えず「このサイトには記載がない」と伝える
- 日本語で答える"""

    _, repo = github_parts(conf)
    # notes の CLAUDE.md(init が作る)に「README の『AIへの指示』に従う」とあるので、フォルダで起動して質問するだけでよい
    detail = f"""

### もっとくわしく調べたいとき(Claude Code)

Claude Code を使うと、AI がすべての記事を検索して答えます。

**1. 最初に1回だけ:リポジトリをクローンする**

```
git clone https://github.com/{conf['github']}.git
```

**2. 質問するとき:フォルダに入って Claude Code を起動し、質問する**

```
cd {repo}
claude
```

> {q}

- リポジトリの `CLAUDE.md` が読まれるので、「お願い」の文を書かなくても、README の「AIへの指示」に従って答えます
- 記事は増えたり直ったりします。ときどき `git pull` で最新にしてください"""

    return simple + ("" if for_readme else rules) + detail


def insert_ask_markers(text, heading, append_if_missing):
    """「AIに質問する使い方」の決まった部分のマーカーがない(以前の init で作った)ファイルに、マーカーを入れる。

    heading の下の本文(次の見出し・区切り線 --- まで)をマーカーに置きかえる。見出しは残す。
    見出しがないときは、append_if_missing なら末尾に見出しとマーカーを足し、そうでなければ None を返す。
    """
    if ASK_START in text:
        return text
    lines = text.split("\n")
    try:
        i = lines.index(heading)
    except ValueError:
        if not append_if_missing:
            return None
        return text.rstrip("\n") + f"\n\n{heading}\n\n{ASK_START}\n{ASK_END}\n"
    j = i + 1
    while j < len(lines) and not (lines[j].startswith("## ") or lines[j].strip() == "---"):
        j += 1
    tail = lines[j:]
    new = lines[:i + 1] + ["", ASK_START, ASK_END] + ([""] + tail if tail else [""])
    return "\n".join(new)


def build_site_config(conf):
    """GitHub Pages(Jekyll)の設定 _config.yml の全文。"""
    owner, repo = github_parts(conf)
    return f"""# GitHub Pages(Jekyll)の設定。
# このファイルは notes.py sync が _data/kb.json から作る。手で直さない(直したいときは KB_GUIDE.md を参照)。
title: {json.dumps(conf['name'], ensure_ascii=False)}
description: {json.dumps(conf['description'], ensure_ascii=False)}
lang: ja
url: https://{owner}.github.io
baseurl: /{repo}

remote_theme: just-the-docs/just-the-docs@v0.12.0
plugins:
  - jekyll-remote-theme
  - jekyll-relative-links
  - jekyll-seo-tag

relative_links:
  enabled: true
  collections: false

search_enabled: true
heading_anchors: true
back_to_top: true
back_to_top_text: ページの先頭へ

aux_links:
  GitHub: https://github.com/{conf['github']}
aux_links_new_tab: true

gh_edit_link: false

# サイトに出さないファイル
exclude:
  - README.md
  - CLAUDE.md
  - KB_GUIDE.md
  - LICENSE
  - notes.py
  - kb-engine.json
  - pmo/
  - config/
  - data/
  - Gemfile
  - Gemfile.lock
  - vendor/

defaults:
  - scope:
      path: ""
    values:
      layout: default
  - scope:
      path: docs
    values:
      layout: article

# index.md の {{: .warning }} などの枠
callouts:
  warning:
    title: 注意
    color: red
  note:
    title: 外部サービスについて
    color: blue
"""


def replace_block(text, start, end, body):
    """text の start〜end の間を body に置きかえた全文を返す。マーカーが無ければ None。

    マーカー(HTMLコメント)と中身のあいだに空行を入れる。空行がないと GitHub Pages(kramdown)で表が崩れる。
    """
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        return None
    block = f"{start}\n\n{body}\n\n{end}"
    return pattern.sub(lambda _: block, text, count=1)


def generated(conf):
    """自動で作る部分。{パス: (今あるべき全文 or None, 問題の説明のリスト)} を返す。"""
    result = {}
    blocks = {
        README: [(AI_START, AI_END, build_ai_block(conf)),
                 (TOC_START, TOC_END, build_toc()),
                 (MANAGE_START, MANAGE_END, build_manage_block(conf))],
        INDEX: [(TOC_START, TOC_END, build_index_toc()),
                (ASK_START, ASK_END, build_ask_block(conf))],
    }
    if not conf["is_template"]:
        blocks[README].append((ASK_START, ASK_END, build_ask_block(conf, for_readme=True)))
    for path, items in blocks.items():
        if not path.exists():
            result[path] = (None, ["ファイルがない"])
            continue
        text = path.read_text(encoding="utf-8")
        # 以前の init で作ったファイルには「AIに質問する使い方」のマーカーがないので、ここで入れる(sync で反映される)
        if path == INDEX:
            text = insert_ask_markers(text, INDEX_ASK_HEADING, append_if_missing=True)
        elif path == README and not conf["is_template"]:
            text = insert_ask_markers(text, README_ASK_HEADING, append_if_missing=False) or text
        problems = []
        for start, end, body in items:
            updated = replace_block(text, start, end, body)
            if updated is None:
                # テンプレート自身の README には、決まった部分を置かなくてよい
                if not (conf["is_template"] and path == README):
                    problems.append(f"マーカー({start} / {end})がない")
                continue
            text = updated
        result[path] = (text, problems)
    result[SITE_CONFIG] = (build_site_config(conf), [])
    return result


# ---------------------------------------------------------------- 共通の部分(エンジン)

def engine_files(root=ROOT):
    """共通の部分のファイルの一覧(kb-engine.json)。"""
    manifest = root / MANIFEST.name
    if not manifest.exists():
        return []
    return json.loads(manifest.read_text(encoding="utf-8"))["files"]


def read_lock():
    if not LOCK.exists():
        return None
    return json.loads(LOCK.read_text(encoding="utf-8"))


def write_lock(template, commit, files, source=None):
    data = {
        "_説明": "notes.py update が書く。手で直さない。取りこんだテンプレートの版と、共通の部分の中身(sha256)の記録",
        "template": template,
        "source": source or template,
        "commit": commit,
        "updated": today().isoformat(),
        "files": {f: sha256(ROOT / f) for f in files if (ROOT / f).exists()},
    }
    LOCK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def locally_edited():
    """前回取りこんだときから、手で直された共通の部分のファイルを返す。"""
    lock = read_lock()
    if not lock:
        return []
    edited = []
    for f, digest in lock["files"].items():
        path = ROOT / f
        if not path.exists():
            edited.append(f"{f}(消されている)")
        elif sha256(path) != digest:
            edited.append(f)
    return edited


# ---------------------------------------------------------------- サードパーティ

def check_thirdparty_notice(text, names, phrase):
    """外部サービスを扱う記事の注意書きを検査する。問題があればその説明、なければ None。

    注意書きは、見出し(# ...)の直後の引用(> ...)に置き、
    phrase と、thirdparty に書いたサービス名をすべて含める。
    """
    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines or not lines[0].startswith("# "):
        return "本文の最初の行を「# タイトル」にする"
    notice = []
    for line in lines[1:]:
        if not line.startswith(">"):
            break
        notice.append(line)
    notice = " ".join(notice)
    if phrase not in notice:
        return f"外部サービスを扱う記事は、タイトルの直後に「{phrase}」を含む注意書き(> で始まる行)を置く"
    missing = [n for n in names if n not in notice]
    if missing:
        return f"注意書きに thirdparty のサービス名がない: {', '.join(missing)}"
    return None


# ---------------------------------------------------------------- コマンド

def cmd_status(args):
    conf = kb()
    if conf["is_template"]:
        print("[ここはテンプレート(原本)です]")
    else:
        lock = read_lock()
        version = (lock or {}).get("commit") or "不明"
        if version != "不明":
            version = version[:7] + ("(未コミットの変更あり)" if "+" in version else "")
        print(f"[{conf['name']} / テンプレート {conf['template_repo']} の版: {version}]")
    rows = []
    for path in articles():
        fm = load(path) or {}
        verified = fm.get("verified", "?")
        if args.todo and verified == "実機":
            continue
        thirdparty = fm.get("thirdparty") or []
        if args.thirdparty and not thirdparty:
            continue
        extra = f"  [外部: {', '.join(thirdparty)}]" if thirdparty else ""
        rows.append((path.name, verified, fm.get("checked", "?"), fm.get("title", "?") + extra))
    if not rows:
        print("該当する記事はありません。")
        return 0
    w0 = max(len(r[0]) for r in rows)
    w1 = max(len(r[1]) for r in rows)
    for name, verified, checked, title in rows:
        # 全角文字を含むので、列ぞろえは目安
        print(f"{name.ljust(w0)}  {verified.ljust(w1, '　')}  {checked}  {title}")
    return 0


def cmd_check(args):
    conf = kb()
    errors, warnings = [], []
    names = set()
    template = load(TEMPLATE) or {}
    phrase = notice_phrase(conf)

    for path in articles():
        name = rel(path)
        if not FILENAME_RE.match(path.name):
            errors.append(f"{name}: ファイル名は「2桁の番号-英小文字.md」にする(例: 06-voice-robotic.md)")
        else:
            num = path.name[:2]
            if num in names:
                errors.append(f"{name}: 番号 {num} がほかの記事と重複している")
            names.add(num)

        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{name}: 冒頭に frontmatter(--- で囲んだ部分)がない")
            continue

        for key in REQUIRED:
            if not fm.get(key):
                errors.append(f"{name}: {key} がない、または空")

        if FILENAME_RE.match(path.name):
            expected = str(int(path.name[:2]))
            if fm.get("nav_order") != expected:
                errors.append(f"{name}: nav_order はファイル名の番号と同じ {expected} にする(サイトのメニューの並び順)")

        for line, problem in yaml_syntax_problems(text):
            errors.append(f"{name}: frontmatter の「{line}」で、{problem}。YAML として読めず、サイトのビルドが失敗したりおかしな値になったりする")

        for v in yaml_unsafe_values(text):
            errors.append(f"{name}: 「{v}」は記号で始まるので引用符で囲む(例: \"{v}\")。囲まないとサイトのビルドが失敗する")

        if "thirdparty" not in fm:
            errors.append(f"{name}: thirdparty がない(外部サービスを扱わないなら thirdparty: [] と書く)")
        else:
            thirdparty = fm["thirdparty"]
            if not isinstance(thirdparty, list):
                errors.append(f"{name}: thirdparty は [Craig, Patreon] のようにリストで書く")
            elif thirdparty:
                problem = check_thirdparty_notice(text, thirdparty, phrase)
                if problem:
                    errors.append(f"{name}: {problem}")

        for key in ("title", "summary", "keywords", "source"):
            if fm.get(key) and fm.get(key) == template.get(key):
                errors.append(f"{name}: {key} がテンプレートのまま")

        verified = fm.get("verified")
        if verified and verified not in VERIFIED_VALUES:
            errors.append(f"{name}: verified は {' / '.join(VERIFIED_VALUES)} のどれか(今は「{verified}」)")

        checked = fm.get("checked")
        if checked:
            try:
                d = datetime.date.fromisoformat(checked)
                age = (today() - d).days
                if age > STALE_DAYS:
                    warnings.append(f"{name}: checked が {age} 日前({checked})。内容を見直す")
                if age < 0:
                    errors.append(f"{name}: checked が未来の日付({checked})")
            except ValueError:
                errors.append(f"{name}: checked は YYYY-MM-DD 形式にする(今は「{checked}」)")

    # 自動で作る部分
    for path, (expected, problems) in generated(conf).items():
        if problems:
            errors += [f"{rel(path)}: {problem}" for problem in problems]
        elif not path.exists() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"{rel(path)}: 自動で作る部分が最新でない、または手で直されている → python3 notes.py sync で直せる")

    # 共通の部分
    if not conf["is_template"]:
        if not read_lock():
            warnings.append(f"{rel(LOCK)} がない。python3 notes.py update を一度実行する")
        for f in locally_edited():
            errors.append(f"{f}: 共通の部分が、このリポジトリで直されている。"
                          f"直したい内容はテンプレート({conf['template_repo']})で直し、ここでは update で取りこむ"
                          f"(KB_GUIDE.md の「共通の部分を直したくなったら」を参照)")
    else:
        for f in engine_files():
            if not (ROOT / f).exists():
                errors.append(f"kb-engine.json: {f} が見つからない")

    for w in warnings:
        print(f"注意: {w}")
    for e in errors:
        print(f"エラー: {e}")
    if not errors and not warnings:
        print(f"OK: 記事 {len(articles())} 本、問題なし")
    elif not errors:
        print(f"OK(注意 {len(warnings)} 件)")
    return 1 if errors else 0


def cmd_sync(args):
    conf = kb()
    status = 0
    for path, (expected, problems) in generated(conf).items():
        if problems:
            for problem in problems:
                print(f"エラー: {rel(path)}: {problem}")
            status = 1
            continue
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == expected:
            print(f"{rel(path)} は最新です。")
        else:
            path.write_text(expected, encoding="utf-8")
            print(f"{rel(path)} を更新しました。")
    return status


def cmd_new(args):
    if not re.match(r"^[a-z0-9-]+$", args.slug):
        print("エラー: SLUG は英小文字・数字・ハイフンだけにする(例: voice-chat)")
        return 1
    numbers = [int(p.name[:2]) for p in articles() if FILENAME_RE.match(p.name)]
    num = max(numbers, default=0) + 1
    path = DOCS / f"{num:02d}-{args.slug}.md"
    if path.exists():
        print(f"エラー: {rel(path)} はすでにある")
        return 1

    text = TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"^title: .*$", f"title: {args.title}", text, count=1, flags=re.M)
    text = re.sub(r"^nav_order: .*$", f"nav_order: {num}", text, count=1, flags=re.M)
    if args.summary:
        text = re.sub(r"^summary: .*$", f"summary: {args.summary}", text, count=1, flags=re.M)
    text = re.sub(r"^checked: .*$", f"checked: {today().isoformat()}", text, count=1, flags=re.M)
    text = re.sub(r"^verified: .*$", "verified: ネットのみ", text, count=1, flags=re.M)
    text = text.replace("# (記事タイトル)", f"# {args.title}", 1)
    path.write_text(text, encoding="utf-8")
    print(f"{rel(path)} を作りました。")

    cmd_sync(args)
    print("keywords・source などを書いたら、python3 notes.py check で確認してください。")
    return 0


def cmd_verify(args):
    if args.value not in VERIFIED_VALUES:
        print(f"エラー: VALUE は {' / '.join(VERIFIED_VALUES)} のどれか")
        return 1
    path = Path(args.file)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        # ファイル名だけ(例: 04-webhooks.md)でも受け付ける
        path = DOCS / Path(args.file).name
    if not path.exists():
        print(f"エラー: {args.file} が見つからない")
        return 1

    text = path.read_text(encoding="utf-8")
    if load(path) is None:
        print(f"エラー: {rel(path)} に frontmatter がない")
        return 1
    m = FRONTMATTER_RE.match(text)
    head = m.group(0)
    head = re.sub(r"^verified: .*$", f"verified: {args.value}", head, count=1, flags=re.M)
    head = re.sub(r"^checked: .*$", f"checked: {today().isoformat()}", head, count=1, flags=re.M)
    path.write_text(head + text[m.end():], encoding="utf-8")
    print(f"{rel(path)}: verified を「{args.value}」、checked を {today().isoformat()} にしました。")
    print("source に「実機で確認」を書いたか確認してください。")
    return 0


# ---------------------------------------------------------------- init

def initial_readme(conf):
    s = conf["subject"]
    return f"""# {conf['name']}(自分用{s}メモ)

> これは個人が作成した非公式のメモです。{conf['owner_org']} とは関係ありません。正確な情報は公式サポートを確認してください。

{s}の使い方・設定方法を、自分用にまとめた知識ベースです。
人間が読んでもいいし、AIに読ませて質問に答えてもらう使い方を想定しています。

**サイトで読む:** {site_url(conf)} (GitHub Pages)

### カバー範囲

- {s}本体の機能と、{s}と一緒によく使う**外部サービス**を扱います
- 外部サービスは**{s}の公式機能ではありません**。外部サービスを扱う記事には、冒頭にその旨の注意書きがあります
- 外部サービスは紹介するだけで、推奨や保証はしません。使うかどうかは、各サービスの規約などを確認したうえで判断してください

{README_ASK_HEADING}

{ASK_START}
{ASK_END}

---

## AIへの指示

{AI_START}
{AI_END}

### 目次

{TOC_START}
{TOC_END}

## 記事の管理(メンテナンス用)

{MANAGE_START}
{MANAGE_END}

## ライセンス

記事の文章は [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja) で公開しています(著作権者:{conf['author']})。
"""


def initial_index(conf):
    # 注意書きの提供元・公式サポートは {{ site.data.kb.… }} で _data/kb.json から読む。
    # _data/kb.json を直せば、サイトのビルドのときに反映される(index.md を直さなくてよい)
    s = conf["subject"]
    return f"""---
title: ホーム
nav_order: 0
layout: default
permalink: /
---

# {conf['name']}

{s}の使い方・設定方法を、自分用にまとめたメモです。
{s}本体の機能のほか、{s}と一緒によく使う外部サービスも扱います。

{{: .warning }}
これは個人が作成した**非公式**のメモです。{{{{ site.data.kb.owner_org }}}} とは関係ありません。
{{{{ site.data.kb.subject }}}}の仕様はよく変わります。各記事の「確認日」と「実機で確認したか」を見て、正確な情報は [{{{{ site.data.kb.support_name }}}}]({{{{ site.data.kb.support_url }}}}) で確認してください。

{{: .note }}
外部サービスは**{{{{ site.data.kb.subject }}}}の公式機能ではありません**。紹介するだけで、推奨や保証はしません。

## 記事一覧

{TOC_START}
{TOC_END}

{INDEX_ASK_HEADING}

{ASK_START}
{ASK_END}
"""


def notes_claude_md(conf):
    return f"""# このリポジトリについて(Claude Code 向け)

このリポジトリは、{conf['subject']}の知識ベースです。テンプレート `{conf['template_repo']}` から作った **notes** です。

- 質問に答えるときは、README.md の「AIへの指示」に従ってください。
- 記事を書く・直す、`notes.py` を使う、しくみについて判断する前に、**KB_GUIDE.md** を読んでください。
- **共通の部分(`kb-engine.json` に載っているファイル。`notes.py`、`_layouts/`、`_includes/`、`KB_GUIDE.md` など)は、このリポジトリで直さないでください。**
  直したくなったら、テンプレート `{conf['template_repo']}` の方を直してから、ここで `python3 notes.py update` を実行して取りこみます(KB_GUIDE.md の「共通の部分を直したくなったら」)。
- README の `<!-- kb:...:start -->` などで囲まれた部分、目次、`_config.yml` は `python3 notes.py sync` が作ります。手で直さないでください。
"""


def cmd_init(args):
    conf = json.loads(KB_JSON.read_text(encoding="utf-8")) if KB_JSON.exists() else {}
    if conf and not conf.get("is_template") and not args.force:
        print("エラー: このリポジトリはすでに notes として始めてある(_data/kb.json の is_template が false)。")
        print("やり直すときは --force を付ける(README・index.md・CLAUDE.md が作り直される)。")
        return 1
    if not re.match(r"^[^/\s]+/[^/\s]+$", args.github):
        print("エラー: --github は「ユーザー名/リポジトリ名」の形にする(例: haya256/my-slack-notes)")
        return 1

    new_conf = {
        "name": args.name,
        "subject": args.subject,
        "owner_org": args.owner_org,
        "support_name": args.support_name or f"{args.subject}公式サポート",
        "support_url": args.support_url,
        "description": args.description or f"{args.subject}の使い方・設定方法をまとめた、自分用の非公式メモ",
        "github": args.github,
        "author": args.author or args.github.split("/")[0],
        "template_repo": conf.get("template_repo", "haya256/my-notes-template"),
        "is_template": False,
    }
    KB_JSON.parent.mkdir(exist_ok=True)
    KB_JSON.write_text(json.dumps(new_conf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{rel(KB_JSON)} を書きました。")

    # テンプレートの見本の記事を消す
    for path in DOCS.glob("*-example.md"):
        path.unlink()
        print(f"見本の記事 {rel(path)} を消しました。")

    README.write_text(initial_readme(new_conf), encoding="utf-8")
    INDEX.write_text(initial_index(new_conf), encoding="utf-8")
    CLAUDE_MD.write_text(notes_claude_md(new_conf), encoding="utf-8")
    print("README.md・index.md・CLAUDE.md を、この notes 用に作りました。")

    write_lock(new_conf["template_repo"], args.template_commit, engine_files())
    print(f"{rel(LOCK)} を書きました(共通の部分の今の中身を記録)。")

    cmd_sync(args)
    print()
    print("次にやること:")
    print("  1. README.md と index.md の紹介文を、題材に合わせて直す(決まった部分の外側は自由に直してよい)")
    print("  2. python3 notes.py new SLUG タイトル で最初の記事を作る")
    print("  3. python3 notes.py check で確認して、コミットする")
    return 0


# ---------------------------------------------------------------- update

def git(*cmd, cwd):
    return subprocess.run(["git", *cmd], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def fetch_template(source, workdir):
    """テンプレートを用意して、(フォルダ, コミットID) を返す。source はローカルのフォルダか「ユーザー名/リポジトリ名」。"""
    local = Path(source).expanduser()
    if local.is_dir():
        commit = None
        try:
            commit = git("rev-parse", "HEAD", cwd=local)
            if git("status", "--porcelain", cwd=local):
                commit += "+未コミットの変更あり"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return local.resolve(), commit
    dest = Path(workdir) / "template"
    url = source if "://" in source else f"https://github.com/{source}.git"
    print(f"テンプレートを取ってきます: {url}")
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", url, str(dest)], check=True)
    return dest, git("rev-parse", "HEAD", cwd=dest)


def cmd_update(args):
    conf = kb()
    if conf["is_template"]:
        print("エラー: ここはテンプレート(原本)なので、update は使わない。")
        return 1

    edited = locally_edited()
    if edited and not args.force:
        print("エラー: 次の共通の部分が、このリポジトリで直されています。上書きすると、その変更は消えます。")
        for f in edited:
            print(f"  - {f}")
        print(f"直した内容を残したいときは、先にテンプレート({conf['template_repo']})に同じ変更を入れてから、もう一度 update します。")
        print("このリポジトリでの変更を捨ててよいときは --force を付けます。")
        return 1

    source = args.source or conf["template_repo"]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            src, commit = fetch_template(source, tmp)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"エラー: テンプレートを取ってこられませんでした({e})")
            return 1
        new_files = engine_files(src)
        if not new_files:
            print(f"エラー: {src} に kb-engine.json がない。テンプレートの場所を確認する")
            return 1
        lock = read_lock() or {}
        old_files = set(lock.get("files", {})) | set(engine_files())

        added, changed, removed = [], [], sorted(old_files - set(new_files))
        for f in new_files:
            mine = ROOT / f
            if not mine.exists():
                added.append(f)
            elif mine.read_bytes() != (src / f).read_bytes():
                changed.append(f)

        label = "不明"
        if commit:
            label = commit[:7] + ("(未コミットの変更あり)" if "+" in commit else "")
        if not (added or changed or removed):
            print(f"共通の部分は最新です(テンプレートの版: {label})。")
            write_lock(conf["template_repo"], commit, new_files, source)
            return 0

        print(f"テンプレートの版 {label} から、次の共通の部分を取りこみます。")
        for f in added:
            print(f"  追加: {f}")
        for f in changed:
            print(f"  変更: {f}")
        for f in removed:
            print(f"  削除: {f}(テンプレートの共通の部分から外れた)")
        if args.diff:
            for f in changed:
                a = (ROOT / f).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                b = (src / f).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                sys.stdout.writelines(difflib.unified_diff(a, b, f"いま/{f}", f"テンプレート/{f}"))
        else:
            print("(変更の中身は --diff を付けると表示されます)")

        if not args.yes:
            answer = input("取りこみますか? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("やめました。何も変えていません。")
                return 1

        for f in added + changed:
            (ROOT / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / f, ROOT / f)
        for f in removed:
            if (ROOT / f).exists():
                (ROOT / f).unlink()
        write_lock(conf["template_repo"], commit, new_files, source)

    print("取りこみました。自動で作る部分を、新しい notes.py で作り直します。", flush=True)
    subprocess.run([sys.executable, str(ROOT / "notes.py"), "sync"], check=False)
    print()
    print("次にやること: python3 notes.py check で確認して、コミットする")
    print(f"  コミットメッセージの例: テンプレートの更新を取りこむ({label})")
    return 0


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="知識ベースの記事としくみを管理する(詳しくは KB_GUIDE.md)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="記事の一覧と、テンプレートの版を表示する")
    p.add_argument("--todo", action="store_true", help="verified が「実機」でない記事だけ表示する")
    p.add_argument("--thirdparty", action="store_true", help="外部サービス(thirdparty)を扱う記事だけ表示する")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("check", help="記事・自動で作る部分・共通の部分を検査する")
    p.set_defaults(func=cmd_check)

    for name in ("sync", "toc"):
        p = sub.add_parser(name, help="README の決まった部分・目次、index.md の記事一覧と「AIに質問する使い方」、_config.yml を作り直す")
        p.set_defaults(func=cmd_sync)

    p = sub.add_parser("new", help="テンプレートから新しい記事を作る")
    p.add_argument("slug", help="ファイル名の英語部分(例: voice-chat)")
    p.add_argument("title", help="記事のタイトル")
    p.add_argument("summary", nargs="?", help="目次に載せる一行の説明")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("verify", help="verified を変えて checked を今日にする")
    p.add_argument("file", help="記事のファイル(例: docs/04-webhooks.md)")
    p.add_argument("value", help=" / ".join(VERIFIED_VALUES))
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("init", help="テンプレートのコピーを、新しい notes として始める")
    p.add_argument("--name", required=True, help="リポジトリ名・サイトのタイトル(例: my-slack-notes)")
    p.add_argument("--subject", required=True, help="題材の名前(例: Slack)")
    p.add_argument("--owner-org", required=True, help="題材の提供元。「〇〇とは関係ありません」に使う(例: Slack Technologies)")
    p.add_argument("--support-url", required=True, help="公式サポートのURL")
    p.add_argument("--support-name", help="公式サポートの名前(省略すると「題材の名前+公式サポート」)")
    p.add_argument("--github", required=True, help="GitHub のリポジトリ(例: haya256/my-slack-notes)")
    p.add_argument("--author", help="著作権者の名前(省略すると GitHub のユーザー名)")
    p.add_argument("--description", help="サイトの説明(省略すると決まった文)")
    p.add_argument("--template-commit", help="元にしたテンプレートのコミットID(分かれば)")
    p.add_argument("--force", action="store_true", help="すでに始めてある notes でも、作り直す")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("update", help="テンプレートから共通の部分の最新版を取りこむ")
    p.add_argument("--from", dest="source", help="テンプレートの場所(ローカルのフォルダ、または「ユーザー名/リポジトリ名」)。省略すると _data/kb.json の template_repo")
    p.add_argument("--yes", action="store_true", help="確認せずに取りこむ")
    p.add_argument("--diff", action="store_true", help="変更の中身を表示する")
    p.add_argument("--force", action="store_true", help="このリポジトリで直された共通の部分があっても、上書きする")
    p.set_defaults(func=cmd_update)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
