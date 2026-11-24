---
title: Xcodeでメニューバーアプリを作る
nav_order: 5
summary: 02のメニューバーアプリをXcodeのプロジェクトで作る。Info.plistやシェルスクリプトを書かずに、LSUIElementの設定・実行・.appの取り出しまで
keywords: [Xcode, プロジェクト, 新規プロジェクト, New Project, Choose Template, メニューバー, 右上, MenuBarExtra, SwiftUI, WindowGroup, Info.plist, LSUIElement, Application is agent, UIElement, Dock, Team, Add account, Organization Identifier, Bundle Identifier, Sign to Run Locally, 署名, アドホック署名, Signing & Capabilities, Show Build Folder in Finder, Archive, アーカイブ, xcarchive, DerivedData, ビルドフォルダ, .build, Spotlight, mdfind, Organizer, Distribute App, .app, swiftc, parse-as-library, パッケージ]
checked: 2026-11-24
verified: 一部実機
thirdparty: []
source:
  - 実機で確認(macOS 27.2.1、Xcode 27.2)
  - https://developer.apple.com/documentation/swiftui/menubarextra
---

# Xcodeでメニューバーアプリを作る

## 要点

- [02-menubar-hello-world.md](02-menubar-hello-world.md) のメニューバーアプリを、**Xcode のプロジェクト**で作る
- Xcode なら、`.app` のフォルダ、`Info.plist`、署名を**自動でやってくれる**。シェルスクリプト(`make-app.sh`)はいらない
- Dock にアイコンを出さない設定(`LSUIElement`)は、`Info.plist` を書かずに、画面の「Info」タブで「Application is agent (UIElement)」を「YES」にする
- Apple のアカウントがないと「Distribute App」は使えなかった。`.app` は**アーカイブの中から取り出す**

## どの作り方を選ぶか

メニューバーアプリは、3つの作り方で作れる。

| 作り方 | 書くもの | `.app` にするには | 向いているとき |
|---|---|---|---|
| `swiftc` で `.swift` ファイル1つ | `.swift` ファイル1つ | フォルダ・`Info.plist`・署名を自分で用意する | とにかく小さく試したい |
| Swift Package([02](02-menubar-hello-world.md)) | `Package.swift` と `.swift` ファイル | 同じく自分で用意する(02 の `make-app.sh`) | しくみを知りたい、ファイルが増えてきた |
| Xcode のプロジェクト(この記事) | `.swift` ファイル(ほかは画面で設定) | Xcode がやる | ちゃんと使う・配るアプリ |

`.app` の中身と署名のしくみは [03-app-bundle-and-codesign.md](03-app-bundle-and-codesign.md) を見てください。Xcode は、03 に書いたことを裏でやっている。

## 手順

### 1. プロジェクトを作る

1. Xcode を起動する。最初の画面の「New Project」の右の ∨ を押し、「Choose Template…」を選ぶ
   - メニューにはほかに「App」「Command Line Tool」「Package…」「Playground」がある
   - 「App」を直接選ぶと、iOS 用と macOS 用のどちらになるかは未確認。「Choose Template…」なら次の画面で macOS を選べる
2. 上のタブで「macOS」を選び、「App」を選んで「Next」を押す
3. 次のように入力して「Next」を押す

   | 項目 | 入れるもの |
   |---|---|
   | 「Product Name」 | `HelloMenuBar` |
   | 「Team」 | Apple のアカウントを登録していないと「Add account…」のボタンが出る。**押さずにそのままでよい** |
   | 「Organization Identifier」 | `com.example` など、ドメイン名を逆にした形がふつう。02 の `CFBundleIdentifier` の前半にあたる |
   | 「Interface」 | 「SwiftUI」 |
   | 「Language」 | 「Swift」 |
   | 「Testing System」/「Storage」 | 「None」 |

   - 「Bundle Identifier」は「Organization Identifier」と「Product Name」から自動で作られる。「Organization Identifier」に `team haya2` のように空白を入れると、`team-haya2.HelloMenuBar` のように `-` に置きかわった

4. 保存する場所を選んで「Create」を押す

左の一覧に、`HelloMenuBarApp.swift` と `ContentView.swift` ができる。右側には `ContentView.swift` のプレビュー(画面の見本)が出る。画面の右下に `main` と出ていて、Xcode がプロジェクト用の Git も作っていた。

### 2. コードを書きかえる

`HelloMenuBarApp.swift` は、はじめは次のようになっている。

```swift
import SwiftUI

@main
struct HelloMenuBarApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

`WindowGroup { ... }` は「ウィンドウを出す」という意味。これを、02 と同じ `MenuBarExtra` に書きかえる。

```swift
import SwiftUI

@main
struct HelloMenuBarApp: App {
    var body: some Scene {
        MenuBarExtra("Hello World!") {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        }
    }
}
```

- 02 との違いは `struct` の名前だけ(`HelloMenuBar` → `HelloMenuBarApp`。Xcode が付けた名前のままでよい)
- `ContentView.swift` は使わなくなる。残しておいても動く
- コードの意味は [02-menubar-hello-world.md](02-menubar-hello-world.md) の「コードの意味」と同じ
- パッケージのときに必要だった `platforms: [.macOS(.v14)]` にあたる設定は、Xcode では「どの macOS から動かすか」(Minimum Deployments)として、はじめから入っている(未確認)

### 3. Dock にアイコンを出さない(`LSUIElement`)

02 では `Info.plist` に `LSUIElement` を手で書いた。Xcode では画面で設定する。

1. 左の一覧のいちばん上(青いアイコンの「HelloMenuBar」)をクリックする
2. 「TARGETS」の「HelloMenuBar」を選び、上の「Info」タブを開く
3. 「Custom macOS Application Target Properties」の表の行にマウスを乗せて「+」を押す
4. 「Application is agent (UIElement)」を選ぶ。「Type」が「Boolean」になるので、「Value」を「YES」にする

この表が、`Info.plist` の中身そのもの。02 で手で書いた項目は、次の行にあたる。

| この表の「Key」 | 02 の `Info.plist` |
|---|---|
| 「Executable file」 | `CFBundleExecutable` |
| 「Bundle identifier」 | `CFBundleIdentifier` |
| 「Bundle name」 | `CFBundleName` |
| 「Bundle OS Type code」 | `CFBundlePackageType` |
| 「Application is agent (UIElement)」 | `LSUIElement` |

値が `$(PRODUCT_NAME)` のようになっているのは、「ほかの設定から値を持ってくる」という意味。ビルドするときに、Xcode が本当の値に置きかえる。

### 4. 実行する

- 左上の ▶ ボタン(または `Cmd + R`)を押すと、ビルドして起動する
- 画面右上のメニューバーに「Hello World!」が出た。**Dock にはアイコンが出なかった**
- クリックすると「終了」が出る
- 止めるときは、メニューの「終了」を押すか、Xcode の ■ ボタン(または `Cmd + .`)を押す

### 5. 署名を見る

「TARGETS」の「HelloMenuBar」→「Signing & Capabilities」タブで見られる。

- 「Team」がないときは、「Signing Certificate」が「Sign to Run Locally」になる(未確認)。自分の Mac で動かすための署名で、02 の `codesign --sign -`(アドホック署名)にあたる。手順6で作った `.app` を調べると、実際に `Signature=adhoc` だった
- ほかの Mac に配るには、Apple の開発者登録をして「Team」を選ぶ([03-app-bundle-and-codesign.md](03-app-bundle-and-codesign.md) の正式な署名)
- 新しいプロジェクトでは「App Sandbox」(アプリにできることを制限するしくみ)がはじめから入っている(未確認)。メニューバーに文字を出すだけなら、そのままでよい

### 6. できた .app を取り出す

`/Applications` に置いて普段使いにするには、本番用(Release)にビルドした `.app` を取り出す。

1. メニューの「Product」→「Archive」を選ぶ。本番用のビルドが終わると「Organizer」の画面が開き、「Archives」に `HelloMenuBar` が出る
2. 右上に「Distribute App」があるが、**「Team」がないと押せなかった**(Apple のアカウントがある前提の機能のよう。理由は未確認)
3. かわりに、アーカイブの中から `.app` を取り出す。アーカイブは次の場所にできていた

   ```
   ~/Library/Developer/Xcode/Archives/(日付)/HelloMenuBar (日付), (時刻).xcarchive/
   └── Products/Applications/HelloMenuBar.app
   ```

   - **Finder で**:「Organizer」でアーカイブを右クリック →「Show in Finder」。出てきた `.xcarchive` を右クリック →「パッケージの内容を表示」→ `Products/Applications/` の `HelloMenuBar.app` を `/Applications` にコピーする
   - **ターミナルで**:`cp -R` で `/Applications` にコピーする(パスに空白と `,` があるので、`"` で囲む)

     ```bash
     cp -R "$HOME/Library/Developer/Xcode/Archives/2026-11-24/HelloMenuBar 2026-11-24, 23.50.xcarchive/Products/Applications/HelloMenuBar.app" /Applications/
     ```

試しに動かしただけの `.app`(Debug)は、メニューの「Product」→「Show Build Folder in Finder」で開いたフォルダの `Products/Debug/` にある(未確認)。`Debug` は02の `swift build`、`Release` は `swift build -c release` にあたる。

## どこに何ができるか

最後に使うのは `.app` 1つだけ。ほかは、それを作るための**材料**と**作業場**。Xcode は作業場と保管箱を `~/Library/Developer/Xcode/` の下に置くので、ファイルがあちこちにできたように見える。

| 場所 | 中身 | 役割 | 消してよい? |
|---|---|---|---|
| 手順1で選んだ保存場所の `HelloMenuBar/` | `.swift` ファイル、`HelloMenuBar.xcodeproj`、`.git` | **材料(原本)**。自分で書いたコードと設定 | 消さない |
| `~/Library/Developer/Xcode/DerivedData/HelloMenuBar-(ランダムな文字)/` | ▶ で作った `Build/Products/Debug/HelloMenuBar.app`、途中のファイル(今回は 101MB) | **作業場**。▶ を押すたびに Xcode が使う | いつ消してもよい。次に ▶ を押せば作り直される |
| `~/Library/Developer/Xcode/Archives/(日付)/HelloMenuBar ….xcarchive` | 本番用の `HelloMenuBar.app` | **できあがりの保管箱**。「Archive」するたびに1つ増える | `.app` を取り出したら消してよい |
| `/Applications/HelloMenuBar.app` | `.app` だけ | **使うもの** | — |

- 自分で触るのは、**材料のフォルダ**と **`/Applications` の `.app`** の2か所だけでよい
- `~/Library/Developer/Xcode/` の下は Xcode の持ち物。容量が気になったら `DerivedData` は丸ごと消せる(消してよいことは一般的な知識。実機では未確認)

### Spotlight には、どの .app も出てくる

`/Applications` にコピーしなくても、Spotlight から `HelloMenuBar` を起動できた。Spotlight は、`.app` がどこにあっても見つける(02 で、パッケージのフォルダに置いたまま起動できたのと同じ)。

ただし、`mdfind` で調べると、同じ名前の `HelloMenuBar.app` が3つ見つかった。

```bash
mdfind "kMDItemFSName == 'HelloMenuBar.app'"
```

| 見つかった場所 | どれか |
|---|---|
| 02 のパッケージのフォルダ | 02 の `make-app.sh` で作ったもの |
| `~/Library/Developer/Xcode/DerivedData/…/Debug/` | ▶ で作った Debug 版 |
| `~/Library/Developer/Xcode/Archives/…/Products/Applications/` | 「Archive」で作った本番用 |

- Spotlight で出てきたのが、このうちのどれかは分からない。今はどれも同じ表示なので違いが見えないが、コードを直していくと「直したはずなのに古いまま」ということが起きうる
- **普段使うものは `/Applications` にコピーして、それを使う**と決めておく。作業場(`DerivedData`)や保管箱(`Archives`)の中のものは、Spotlight で出てきても起動しない
- Spotlight の結果のどれが起動したかを確かめる方法は未確認

パッケージ([02](02-menubar-hello-world.md))でも同じことが起きている。全部が1つのフォルダの中なので目立たないだけ。

| 役割 | パッケージ(02) | Xcode(この記事) |
|---|---|---|
| 材料 | `Package.swift` と `Sources/` | 保存場所の `HelloMenuBar/` |
| 作業場 | パッケージのフォルダの中の `.build/`(隠しフォルダ) | `~/Library/Developer/Xcode/DerivedData/` |
| できあがり | `make-app.sh` が作った `HelloMenuBar.app` | アーカイブの中の `HelloMenuBar.app` |

## メモ

- 実機で確かめたのは次のとおり
  - プロジェクトの作成(手順1)、`LSUIElement` の設定(手順3)、実行して右上に表示されること・Dock にアイコンが出ないこと(手順4)
  - 「Archive」でアーカイブができること、「Distribute App」が押せないこと、アーカイブの中の `.app` がアドホック署名であること(手順6)
- **未確認のこと**:取り出した `.app` を `/Applications` から起動できるか、「Signing & Capabilities」タブの表示、「Show Build Folder in Finder」の場所、Minimum Deployments
- **`.swift` ファイル1つで作る方法**は実機で確かめた。02 の手順3と同じ中身の `HelloMenuBar.swift` を、次のようにビルドした

  ```bash
  swiftc -parse-as-library HelloMenuBar.swift -o hello
  ./hello
  ```

  - `-parse-as-library` を付けないと、次のエラーになった。`swiftc` はファイルが1つだと「上から順に実行するスクリプト」として読むので、`@main` と食い違うため

    ```
    error: 'main' attribute cannot be used in a module that contains top-level code
    ```

  - パッケージのときの `platforms` にあたるものは書かなくても、ビルドできた
  - 02 と同じ形のフォルダに実行ファイルと `Info.plist` を入れ、`codesign --sign -` で署名すると、`.app` にもできた(`swiftc -O` が `swift build -c release` にあたる)
  - 確かめたのは、ビルド・署名・起動して動き続けることまで。**右上に表示されたかは目で見ていない**
