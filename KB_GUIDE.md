# KB_GUIDE:知識ベースのしくみと作業のルール

このファイルは、**テンプレート `my-notes-template` と、そこから作った各 notes(知識ベース)に共通の説明書**です。
人間も、AI(Claude Code など)も、作業の前にこのファイルを読んでください。

> このファイル自体も「共通の部分」です。各 notes では直さず、テンプレートで直します。

---

## 1. 全体像

```
my-notes-template(テンプレート = 原本)
  │  共通の部分(notes.py、サイトの見た目、このガイドなど)を管理する
  │
  ├── notes.py update で配る ──→ my-discord-notes(notes)
  ├── notes.py update で配る ──→ my-slack-notes(notes)
  └── notes.py update で配る ──→ ...
```

- **テンプレート**:しくみの**原本**。共通の部分を直すのは、ここだけ
- **notes**:題材ごとの知識ベース(例:Discord、Slack)。記事を書くのはこちら。共通の部分は**原本のコピー**として持っていて、`python3 notes.py update` で最新版を取りこむ

---

## 2. 今いるのはどっち?

`_data/kb.json` の `is_template` を見ます。

| `is_template` | ここは | できること・やること |
|---|---|---|
| `true` | **テンプレート(原本)** | 共通の部分を直す。記事は見本(`docs/01-example.md`)だけ |
| `false` | **notes** | 記事を書く・直す。共通の部分は直さない |

`python3 notes.py status` の1行目にも表示されます。

---

## 3. ファイルの3つの分類

| 分類 | ファイル | 直してよい場所 | 直し方 |
|---|---|---|---|
| **共通の部分** | `kb-engine.json` に載っているファイル:`notes.py`、`KB_GUIDE.md`、`kb-engine.json`、`docs/_template.md`、`_layouts/article.html`、`_includes/footer_custom.html`、`_includes/head_custom.html`、`_includes/lunr/custom-index.js` | **テンプレートだけ** | テンプレートで直して push → 各 notes で `update` |
| **自動で作る部分** | `_config.yml`、README の `<!-- kb:ask -->`・`<!-- kb:ai -->`・`<!-- toc -->`・`<!-- kb:manage -->` で囲まれた部分、`index.md` の `<!-- toc -->`・`<!-- kb:ask -->` で囲まれた部分 | どこでも**手で直さない** | `python3 notes.py sync` が作る。中身を変えたいときは、作り方(`notes.py`)をテンプレートで直す |
| **notes ごとの部分** | `_data/kb.json`、記事(`docs/01-…md` など)、README・`index.md` の決まった部分の外側、`CLAUDE.md`、`LICENSE`、`.gitignore` | その notes で自由に | ふつうに直す |

ポイント:
- 共通の部分には、題材の名前(「Discord」など)を**直接書かない**。題材ごとの言葉は `_data/kb.json` に書き、共通の部分はそこから読む(`notes.py` は Python で、サイトのテンプレートは `site.data.kb` で読む)
- そうすることで、共通の部分はどの notes でも**中身がまったく同じ**になり、丸ごと上書きで配れる

---

## 4. 場面ごとのやること

### 4-1. notes で作業しているとき

| こう頼まれたら | やること |
|---|---|
| 記事を書いて/直して | `python3 notes.py new SLUG タイトル 説明` で作る(直すときはそのまま編集)→ `python3 notes.py check` |
| 題材について質問に答えて | README の「AIへの指示」に従う |
| 目次やサイトの設定が古い | `python3 notes.py sync` |
| `notes.py` やサイトの見た目、このガイドを直したい | **ここでは直さない**。下の「4-3. 共通の部分を直したくなったら」 |
| テンプレートの改善を取りこんで | `python3 notes.py update` → `check` → コミット |

### 4-2. テンプレートで作業しているとき

| こう頼まれたら | やること |
|---|---|
| `notes.py` などしくみを直して | 共通の部分を直す。ファイルを足した・減らしたときは `kb-engine.json` も直す |
| 直したので確かめて | 下の「6. テンプレートを直したときの確かめ方」 |
| 直したものを配って | テンプレートを push。各 notes で `update` してもらう(各 notes で作業しているなら、続けて `update` まで行う) |
| 記事を書いて | テンプレートには見本しか置かない。どの notes の記事かを確認する |

### 4-3. 共通の部分を直したくなったら(notes で作業中に思いついたとき)

例:`my-discord-notes` で作業中に「`notes.py status` に記事の数も出したい」と思いついた。

1. **notes の `notes.py` は直さない**。直すと、次の `update` でテンプレートの版に上書きされて消える
2. **テンプレートのフォルダで直す**(例:`~/dev/my-notes-template/notes.py`)。テンプレートの手元のコピーがなければ `gh repo clone <template_repo>` で取ってくる
3. テンプレートで確かめて(「6.」)、コミット・push する
4. notes に戻って `python3 notes.py update` を実行する → 改善が取りこまれる
5. `python3 notes.py check` → notes でもコミット・push する

> **AI への指示**:ユーザーが notes で作業中に共通の部分の変更を頼んだら、notes 側のファイルを直さずに、上の 2〜5 を行ってください。テンプレートの場所が分からなければ `_data/kb.json` の `template_repo` を見て、手元にあるかユーザーに確認してください。テンプレートへの push は、ユーザーの了解を得てから行ってください。

### 4-4. うっかり notes で共通の部分を直してしまったら

`python3 notes.py check` が「共通の部分が、このリポジトリで直されている」と知らせます(前回 `update` したときの中身と比べています)。

- その変更を残したい → テンプレートに同じ変更を入れて push → notes で `update`
- その変更は要らない → `python3 notes.py update --force` でテンプレートの版に戻す

`update` は、直された共通の部分があると、`--force` なしでは上書きしません(変更が消えるのを防ぐため)。

---

## 5. 新しい notes の作り方

作り方は2つあります。**まず手元だけで作り、あとで GitHub に公開する**(5-1)か、**最初から GitHub にリポジトリを作る**(5-2)かです。どちらも、作ったあとの手順(5-3)は同じです。

> **AI への指示**:新しい notes を頼まれたら、題材の名前・リポジトリ名・提供元・公式サポートの URL をユーザーに確認してください。GitHub にリポジトリを作る・公開するのは、ユーザーの了解を得てからにしてください。

### 5-1. 手元だけで作る(GitHub はあとで)

```bash
# 1. テンプレートの最新版を手元に取ってくる
cd ~/dev
git clone --depth 1 https://github.com/haya256/my-notes-template.git my-slack-notes
cd my-slack-notes

# 2. テンプレートの履歴を切りはなして、新しいリポジトリにする
c=$(git rev-parse HEAD)   # 元にしたテンプレートの版を控えておく
rm -rf .git
git init -b main

# 3. notes として始める
python3 notes.py init \
  --name my-slack-notes \
  --subject Slack \
  --owner-org "Slack Technologies" \
  --support-url https://slack.com/help \
  --github haya256/my-slack-notes \
  --template-commit "$c"

# 4. 確認して、最初のコミット
python3 notes.py check
git add -A
git commit -m "my-notes-template から notes を作る"
```

- **手順2の `.git` の削除は必ず行う**。消さないと、テンプレートの履歴と push 先(テンプレートのリポジトリ)が残り、うっかり push するとテンプレートを書きかえてしまう
- `--github` には、まだ GitHub に作っていないリポジトリ名を書いてよい(サイトの URL や README のリンクを作るのに使うだけ)。あとで変えるときは `_data/kb.json` の `github` を直して `python3 notes.py sync`
- `--template-commit` で元にした版を記録しておくと、`status` に表示される(省略してもよい。次に `update` したときに記録される)
- 手元に `~/dev/my-notes-template` があるなら、`git clone` の代わりにそこからコピーしてもよい。その場合も `.git` は消す。テンプレートの手元のコピーに未コミットの変更がないか、先に確かめる

あとで GitHub に公開するとき:

```bash
gh repo create my-slack-notes --public --source=. --push
gh api -X POST repos/haya256/my-slack-notes/pages -f "source[branch]=main" -f "source[path]=/"
```

### 5-2. 最初から GitHub にリポジトリを作る

```bash
gh repo create my-slack-notes --template haya256/my-notes-template --public --clone
cd my-slack-notes
python3 notes.py init \
  --name my-slack-notes \
  --subject Slack \
  --owner-org "Slack Technologies" \
  --support-url https://slack.com/help \
  --github haya256/my-slack-notes
```

テンプレートリポジトリから作ると、履歴は最初から切りはなされている(`.git` を消す必要はない)。

### 5-3. 作ったあと(どちらの作り方でも)

`init` で、`_data/kb.json`(`is_template: false`)、README・`index.md`・`CLAUDE.md` が作られ、見本の記事が消え、共通の部分の今の中身が記録されます。

1. README と `index.md` の紹介文を題材に合わせて直す(決まった部分の外側)
2. `python3 notes.py new SLUG タイトル 説明` で記事を書く → `python3 notes.py check`
3. コミットする。GitHub に公開したら、GitHub Pages を有効にする(「10. サイト」)

### 5-4. 「AIに質問する使い方」について

README の「使い方(人間向け)」と `index.md` の「AIに質問する使い方」の中身は、`sync` が作る決まった部分(`<!-- kb:ask:start -->` 〜 `<!-- kb:ask:end -->`)です。

- いちばん簡単な使い方として、**ウェブのページを読める AI チャットに、サイトの URL と質問を渡す**方法を先に書く。サイトだけを読んだ AI は README の「AIへの指示」を知らないので、`index.md` には短い回答のルールも載せる。Claude Code でクローンして質問する手順は「もっとくわしく調べたいとき(Claude Code)」として後ろに書く(クローンしたフォルダで `claude` を起動すると、notes の `CLAUDE.md` の「README の『AIへの指示』に従う」が読まれるので、質問を打つだけでよい。`init` が作る `CLAUDE.md` のこの一文は消さない)
- 質問の例は、`_data/kb.json` の `ask_example` で notes ごとに決められる(例:`"ask_example": "Orbs ってなに？"`)。決まった部分の中の「(聞きたいこと)」(サイトの URL を渡す頼み方と、Claude Code で質問する例の2か所)が、README・`index.md` の両方でこの文になる。決めたら `python3 notes.py sync`
- 見出し(`## 使い方(人間向け)`・`## AIに質問する使い方`)は決まった部分の外にある。決まった部分の外なら、題材ごとの質問の例などを自由に書き足してよい
- 決まった部分がなかったころに作った notes では、`update`(または `sync`)のときに、見出しの下の本文(次の見出しか `---` まで)が決まった部分に置きかわる。そこに手で書いていた質問の例などは消えるので、質問の例は `ask_example` に、ほかに残したいものは決まった部分の外に書き直す

---

## 6. テンプレートを直したときの確かめ方

テンプレートの中だけでなく、**notes に取りこんだときに動くか**を確かめます。

1. テンプレートで `python3 notes.py check`(見本の記事で検査が通るか)
2. 試しの notes を作って取りこむ(手元のフォルダから取りこめる)
   ```bash
   cp -r ~/dev/my-notes-template /tmp/kb-test && cd /tmp/kb-test
   python3 notes.py init --name kb-test --subject テスト --owner-org テスト社 --support-url https://example.com/ --github you/kb-test
   # テンプレートを直したあとで:
   python3 notes.py update --from ~/dev/my-notes-template --diff
   python3 notes.py check
   ```
3. 実際の notes で `python3 notes.py update --from ~/dev/my-notes-template --diff` を実行し、`check` が通るか見る(push 前でも、手元のテンプレートから取りこめる)

---

## 7. コマンド一覧

| コマンド | やること |
|---|---|
| `python3 notes.py status [--todo] [--thirdparty]` | 記事の一覧(`verified`・`checked`・外部サービス)と、取りこんだテンプレートの版 |
| `python3 notes.py check` | 記事の書き方、自動で作る部分が最新か、共通の部分が手で直されていないか |
| `python3 notes.py sync` | 自動で作る部分を作り直す(`toc` は同じコマンドの以前の名前) |
| `python3 notes.py new SLUG タイトル [説明]` | 記事を作る。番号・`nav_order`・`checked` は自動 |
| `python3 notes.py verify ファイル 値` | `verified` を変え、`checked` を今日にする |
| `python3 notes.py init --name … --subject … --owner-org … --support-url … --github …` | テンプレートのコピーを notes として始める |
| `python3 notes.py update [--from 場所] [--diff] [--yes] [--force]` | テンプレートから共通の部分を取りこむ。`--from` を省くと `_data/kb.json` の `template_repo`(GitHub)から |

---

## 8. 記事の書き方

### ファイル名

- `docs/` に「2桁の番号-英小文字.md」(例:`06-voice-robotic.md`)。`notes.py new` が番号を付ける
- `_` で始まるファイルは記事として扱わない(`_template.md` など)

### frontmatter(記事の冒頭)

| 項目 | 内容 |
|---|---|
| `title` | 記事のタイトル |
| `nav_order` | サイトの左メニューの並び順。ファイル名の番号と同じ数字(`new` が入れる) |
| `summary` | 目次に載せる一行の説明 |
| `keywords` | grep で見つけやすくするための語句 |
| `checked` | 最後に内容を見直した日(YYYY-MM-DD)。180日より古いと `check` が注意を出す |
| `verified` | `実機`(すべて実機で確認)/ `一部実機`(どこを確認したかはメモに書く)/ `ネットのみ`(未確認) |
| `thirdparty` | 記事で扱う外部サービスの名前(例:`[Craig]`)。題材本体の機能だけなら `[]` |
| `source` | 参考にしたURLや「実機で確認」。複数あるときは `- ` で始まる行を並べる |

### ルール

- 値が `@` などの記号で始まるときは `"@everyone"` のように引用符で囲む(囲まないとサイトのビルドが失敗する。`check` が検査する)
- `[` で始めたら `]` で、引用符で始めたら同じ引用符で閉じる(閉じ忘れは `check` が検査する)
- `thirdparty` が空でない記事は、タイトル(`# ...`)の直後に `>` で始まる注意書きを置く。注意書きには「(題材)の公式機能ではありません」という文言(`_data/kb.json` の `subject` から作る)と、`thirdparty` のサービス名をすべて含める
- ほかの記事への参照は `[05-developer-mode.md](05-developer-mode.md)` のようにリンクで書く(GitHub でもサイトでもリンクになる)
- 目次や決まった部分は手で直さない。記事の `summary` などを直して `python3 notes.py sync`
- 確かめていないことは「未確認」と書く。ネットの情報と実機で確かめたことを分けて書く
- 記事を直したら `python3 notes.py check`

---

## 9. 設定ファイル `_data/kb.json`

| 項目 | 内容 | 例 |
|---|---|---|
| `name` | リポジトリ名・サイトのタイトル | `my-discord-notes` |
| `subject` | 題材の名前。注意書きや AI への指示に使う | `Discord` |
| `owner_org` | 題材の提供元。「〇〇とは関係ありません」に使う | `Discord Inc.` |
| `support_name` / `support_url` | 公式サポートの名前と URL | `Discord公式サポート` / `https://support.discord.com/` |
| `description` | サイトの説明 | |
| `github` | この notes の GitHub リポジトリ | `haya256/my-discord-notes` |
| `author` | 著作権者の名前 | `haya256` |
| `template_repo` | 元にしたテンプレートのリポジトリ。`update` がここから取ってくる | `haya256/my-notes-template` |
| `is_template` | テンプレートなら `true`、notes なら `false` | |
| `ask_example` | (省略できる)「AIに質問する使い方」に出す質問の例。省略すると「(聞きたいこと)」 | `Orbs ってなに？` |

直したら `python3 notes.py sync`(`_config.yml` などに反映される)。

`_data/kb.json` の値は、次の所で使われます。
- `notes.py sync` が作る部分(`_config.yml`、README の「AIへの指示」、README と `index.md` の「AIに質問する使い方」など)→ `sync` で反映
- サイトのフッターと、`init` が作る `index.md` の注意書き(`{{ site.data.kb.… }}` で読む)→ サイトのビルドのときに自動で反映
- `init` が作る README の紹介文 → 作ったときに文字として書きこまれるので、**値を変えたら手で直す**

---

## 10. サイト(GitHub Pages)

- `main` ブランチの `/`(ルート)から配信する。push すると数分でサイトが作り直される
- 有効にする:`gh api -X POST repos/<ユーザー名>/<リポジトリ名>/pages -f "source[branch]=main" -f "source[path]=/"`
- テーマは [Just the Docs](https://just-the-docs.com/)(`_config.yml` で版を固定)
- ビルドの結果:`gh api repos/<ユーザー名>/<リポジトリ名>/pages/builds/latest`(`status` が `built` なら成功、`errored` なら `error.message` を見る)

| ファイル | 内容 | 分類 |
|---|---|---|
| `_config.yml` | サイトの設定。サイトに出さないファイルもここで指定 | 自動で作る部分 |
| `index.md` | サイトのトップページ | notes ごと(記事一覧と「AIに質問する使い方」は自動) |
| `_layouts/article.html` | 記事のページ。確認日・確認方法・外部サービスを本文の上に、`source` を「参考」として本文の下に出す | 共通 |
| `_includes/footer_custom.html` | 全ページの下の注意書きとライセンス(`_data/kb.json` から作る) | 共通 |
| `_includes/head_custom.html` | 見た目の細かい調整(CSS) | 共通 |
| `_includes/lunr/custom-index.js` | サイト内検索の日本語対応(2文字ずつに区切る、すべて含むページだけ出す、ひらがな・カタカナと全角・半角を区別しない、ハイライトの重なりをまとめる) | 共通 |

### 過去にハマったこと

- frontmatter の値が `@` で始まると YAML のエラーでビルドが失敗する → 引用符で囲む(`check` が検査)
- frontmatter の `keywords: [a, b` のように `]` や引用符を閉じ忘れても気づきにくい(YAML としては読めず、ビルドの失敗やおかしな値のもと) → `check` が `[` `{` `"` `'` の閉じ忘れを検査
- HTML コメント(`<!-- toc:start -->`)の直後に表を書くと、表が崩れる → `sync` は空行を入れて作る
- テーマの検索(lunr)は日本語を消してしまう → `_includes/lunr/custom-index.js` で対応済み

---

## 11. Git のルール

- コミット・push は、ユーザーに頼まれたときだけ行う
- テンプレートの更新を notes に取りこんだときのコミットメッセージの例:「テンプレートの更新を取りこむ(abc1234)」
- `.kb-engine-lock.json` は `update` が書くファイル。手で直さず、ほかの変更と一緒にコミットする
