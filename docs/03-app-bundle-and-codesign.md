---
title: .appのしくみと署名
nav_order: 3
summary: .appの正体(決まった形のフォルダ)、macOSが起動するまでの流れ、コード署名(アドホック署名と正式な署名・公証)のしくみ
keywords: [.app, アプリ, バンドル, bundle, パッケージの内容を表示, Info.plist, CFBundleExecutable, CFBundleIdentifier, Launch Services, lsregister, mdls, Spotlight, 署名, コード署名, codesign, アドホック署名, adhoc, CDHash, CodeDirectory, ハッシュ, 改ざん, 証明書, 秘密鍵, 公開鍵, Developer ID, Team ID, Apple Developer Program, 公証, ノータリゼーション, notarization, Gatekeeper, linker-signed, Apple シリコン]
checked: 2026-11-22
verified: 一部実機
thirdparty: []
source:
  - 実機で確認(macOS 27.2.1、Xcode 付属の Apple Swift 6.4.2。02-menubar-hello-world.md で作った HelloMenuBar.app を調べた)
  - https://developer.apple.com/library/archive/technotes/tn2206/_index.html
  - https://developer.apple.com/developer-id/
---

# .appのしくみと署名

## 要点

- `.app` は、**実行ファイルと `Info.plist` を決まった形で入れたフォルダ**。macOS は名前が `.app` で終わるフォルダをアプリとして扱い、`Info.plist` を読んでどの実行ファイルを起動するかを知る
- **コード署名**は、中身のハッシュをとっておき、起動するときに照合するしくみ。1文字でも書きかえると見破られる
- `codesign --sign -` の**アドホック署名**は「書きかえられていない」ことだけを証明する、自分の Mac 用の署名。**正式な署名**は、Apple が発行した証明書で「誰が作ったか」も証明する

ここで調べた `HelloMenuBar.app` の作り方は [02-menubar-hello-world.md](02-menubar-hello-world.md) の「コマンドラインだけで .app にする」を見てください。

## .app の中身

`make-app.sh` で作った `HelloMenuBar.app` の中身は、次のとおりだった。

```
HelloMenuBar.app/
└── Contents/
    ├── Info.plist                  ← 設定ファイル(自分で書いた)
    ├── MacOS/
    │   └── HelloMenuBar            ← 実行ファイル(swift build でできたもの)
    └── _CodeSignature/
        └── CodeResources           ← 署名したときに codesign が作った
```

- Finder でアプリを右クリック →「パッケージの内容を表示」で、この中身を見られる
- ふつうのアプリは、ほかに `Contents/Resources/`(アイコンや画像などを入れる場所)がある(今回は作っていない)

## フォルダなのに1つのアイコンに見えるわけ

macOS は、ファイルやフォルダが何者なのかを「種類」(UTI)で見分けている。`mdls` で `HelloMenuBar.app` の種類を調べると、次のように出た(主なものだけ)。

```bash
mdls -name kMDItemContentTypeTree HelloMenuBar.app
```

| 種類 | 意味 |
|---|---|
| `com.apple.application-bundle` | アプリのバンドル |
| `com.apple.package` | 中身を見せずに、1つのものとして見せるフォルダ |
| `public.directory` | 中身はフォルダ |

名前の最後が `.app` なので「アプリのフォルダ」と判断され、Finder は中に入らずに1つのアイコンとして見せる。

## ダブルクリックしてから起動するまで

1. Finder が「これはアプリだ」と判断する
2. macOS の、アプリを起動する担当(Launch Services)が `Contents/Info.plist` を読む
3. `CFBundleExecutable` に書かれた名前を見て、`Contents/MacOS/HelloMenuBar` を起動する
4. 起動する前に、署名を確かめる(下の「署名」)

`CFBundleExecutable` が「このフォルダのどれを起動するか」を決める鍵。ここを書きまちがえると起動できない。

## Spotlight から起動できるわけ

macOS は、見つけたアプリを「アプリの名簿」(Launch Services のデータベース)に登録している。名簿の中身は次のコマンドで見られる(とても長いので `grep` で絞る)。

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -dump | grep -A12 "com.example.HelloMenuBar"
```

`HelloMenuBar.app` は、アプリケーションフォルダに置いていなくても登録されていた。

```
name:        HelloMenuBar
identifier:  com.example.HelloMenuBar      ← Info.plist の CFBundleIdentifier
executable:  Contents/MacOS/HelloMenuBar   ← Info.plist の CFBundleExecutable
```

- Spotlight はこの名簿を使ってアプリを探すので、アプリケーションフォルダの外に置いたアプリでも見つかる
- 同じ `CFBundleIdentifier` の `.app` を別の場所にも作ったら、名簿に2つ登録されていた。本当に配るアプリなら、ほかと重ならない ID にする

## 実行ファイルだけでも動く

本体の `Contents/MacOS/HelloMenuBar` は普通の実行ファイルなので、`swift run` のように `.app` がなくても動く。`.app` に入れると、次のことができるようになる。

- ダブルクリックや Spotlight から起動できる
- 名前や ID などを `Info.plist` で macOS に伝えられる
- 署名で、`Info.plist` も含めたフォルダ全体が書きかえられていないことを確かめられる

## 署名:ハッシュで「書きかえられていない」ことを確かめる

署名の中身は `codesign -dvvv` で見られる。

```bash
codesign -dvvv HelloMenuBar.app
```

主なところは次のとおりだった。

```
Identifier=com.example.HelloMenuBar
CodeDirectory v=20400 size=337 flags=0x2(adhoc) hashes=4+3 location=embedded
Hash type=sha256 size=32
CDHash=fc7fac4f2d601184886142578cf8645191317216
Signature=adhoc
Info.plist entries=5
TeamIdentifier=not set
```

| 書いてあること | 意味 |
|---|---|
| `Hash type=sha256` | ハッシュの計算方法 |
| `hashes=4+3` | 実行ファイルを区切ったぶんのハッシュ(`4`)と、`Info.plist` など実行ファイル以外の大事なもののハッシュ(`+3`)。この一覧を CodeDirectory という |
| `CDHash` | CodeDirectory をまとめてハッシュにしたもの。このアプリの「指紋」 |
| `Signature=adhoc` | アドホック署名(証明書なし) |
| `TeamIdentifier=not set` | 「誰が作ったか」が書かれていない |

ファイル全体のハッシュを1つとるのではなく、実行ファイルを区切ってハッシュをとっている。macOS は実行ファイルを少しずつメモリに読みこむので、読みこんだ部分ごとに照合できるようにしていると考えられる(未確認。自分の理解)。

### 書きかえると見破られるか試した

`HelloMenuBar.app` のコピーを書きかえて、`codesign -v`(署名を確かめるコマンド)にかけた。

| 書きかえたもの | 結果 |
|---|---|
| (書きかえる前) | 何も出ない(問題なし) |
| `Info.plist` の `CFBundleIdentifier` を1文字変えた | `invalid Info.plist (plist or signature have been modified)` |
| 実行ファイルの最後に1バイト足した | `main executable failed strict validation` |

どちらも「書きかえられている」と見破られた。

### swift build でできた実行ファイルも、最初から署名されている

`.app` に入れる前の、`swift build` でできた実行ファイルも調べると、署名が付いていた。

```
CodeDirectory v=20400 size=583 flags=0x20002(adhoc,linker-signed) hashes=15+0 location=embedded
Signature=adhoc
```

- Apple シリコンの Mac では、署名のない実行ファイルは動かせない決まりになっている。そのため、ビルドの最後にリンカー(プログラムを組み立てる道具)が自動でアドホック署名を付ける(`linker-signed`)。`swift run` がそのまま動くのはこのため
- `.app` にしたあとで `codesign` し直すのは、`Info.plist` などフォルダ全体をハッシュの対象に入れるため。`hashes=15+0` → `4+3` のように、実行ファイル以外のハッシュ(`+3`)が加わる
- 実行ファイル側の数(`15` → `4`)が変わったのは、区切る大きさがちがうから。`codesign -dvvvv` で見ると、リンカーの署名は `Page size=4096`(4KB ごと)、`codesign` の署名は `Page size=16384`(16KB ごと)だった。実行ファイルは約58KBなので、4KB ごとなら15個、16KB ごとなら4個になる
- `codesign` し直すと署名が中に書きこまれるので、`.build/release/` の実行ファイルと `.app` の中の実行ファイルは、同じものではなくなる(`cmp` で比べると「differ」)

## アドホック署名と正式な署名のちがい

ハッシュだけだと、悪い人がアプリを書きかえたあとに、ハッシュをとり直せば通ってしまう。正式な署名では、そこに「誰が作ったか」の証明を乗せる。

| | アドホック署名(`--sign -`) | 正式な署名 |
|---|---|---|
| 中身が書きかえられていない | 証明できる | 証明できる |
| 誰が作ったか | 証明しない | Apple が発行した証明書で証明する |
| 向いている使い道 | 自分の Mac で動かす | ほかの人に配る |

### 正式な署名の紐付け

ここから下は、ネットの情報と自分の理解でまとめたもの(**正式な署名・公証は試していない**)。

1. **Apple Developer Program に登録する**(年会費が必要)。このとき Apple が身元を確認する。ログインには Apple ID を使う
2. **自分の Mac で、秘密鍵と公開鍵のペアを作る**(Xcode やキーチェーンアクセスが作る)。秘密鍵は自分の Mac(キーチェーン)にだけ置き、Apple には渡さない。**Apple ID から作られるものではない**
3. **公開鍵だけを Apple に送る**
4. **Apple が証明書を発行する**。「この公開鍵は、身元を確認したこの開発者(チーム)のもの」という保証書で、チームを表す番号(Team ID)が入る
5. **自分の Mac で、秘密鍵を使ってアプリに署名する**。アプリには証明書も一緒に入る

```
Apple(いちばん上の保証人)
  └─ 証明書:「この公開鍵は、開発者〇〇(Team ID: XXXX)のもの」と Apple が保証
        └─ アプリの署名:〇〇の秘密鍵で作られている → 証明書の公開鍵で確かめられる
              └─ ハッシュ:中身が書きかえられていない
```

### 誰が何を保証するか

| 何を保証するか | 誰が・何が保証するか |
|---|---|
| 中身が書きかえられていない | 署名の計算(ハッシュと秘密鍵)。Apple が保証するのではない |
| 作ったのは〇〇さんだ | Apple が発行した証明書 |
| 危ないプログラムではなさそう | 公証(下で説明) |

### 公証(ノータリゼーション)

- App Store の外で Mac アプリを配るときは、署名のあとにアプリを Apple に送って、**自動チェック(公証)**を受ける。Apple がマルウェアなどが入っていないかを機械で調べ、問題なければ「チェック済み」の印を出す
- インターネットからダウンロードしたアプリには、macOS が「ネットから来た」という印を付ける。印の付いたアプリを起動するとき、macOS(Gatekeeper)が正式な署名と公証を確かめ、なければ止める
- 悪いことをしたアプリが見つかったら、Apple はその開発者の証明書を無効にできる

### 証明書の種類

| 証明書 | 使い道 |
|---|---|
| Apple Development | 開発中に自分の機器で試す用。無料の Apple ID でも作れる |
| Developer ID Application | App Store の外(自分のサイトなど)で Mac アプリを配る用。有料登録が必要 |
| Apple Distribution | App Store に出す用。有料登録が必要 |

## メモ

- 実機で確かめたのは、`.app` の中身、`mdls` での種類、Launch Services への登録、`codesign -dvvv` の表示、書きかえたときに見破られること、`swift build` の実行ファイルが `linker-signed` になっていること
- 正式な署名・公証・証明書の種類、Gatekeeper が止めるしくみは**未確認**(ネットの情報と自分の理解)。年会費の金額や細かい条件は Apple Developer の公式ページで確かめる
- 自分の Mac でビルドしたアプリには「ネットから来た」印が付かないので、アドホック署名のままで起動できる。ほかの Mac に渡したときに止められるかは未確認
