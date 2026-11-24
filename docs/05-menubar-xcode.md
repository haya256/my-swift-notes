---
title: Xcodeでメニューバーアプリを作る
nav_order: 5
summary: 02のメニューバーアプリをXcodeのプロジェクトで作る。Info.plistやシェルスクリプトを書かずに、LSUIElementの設定・実行・.appの取り出しまで
keywords: [Xcode, プロジェクト, 新規プロジェクト, Create New Project, メニューバー, 右上, MenuBarExtra, SwiftUI, WindowGroup, Info.plist, LSUIElement, Application is agent, UIElement, Dock, Sign to Run Locally, 署名, Signing & Capabilities, Show Build Folder in Finder, Archive, Distribute App, .app, swiftc, parse-as-library, パッケージ]
checked: 2026-11-24
verified: 一部実機
thirdparty: []
source:
  - 一般的な知識をもとに書いた(Xcode の手順は実機では未確認)
  - 「.swift ファイル1つで作る」は実機で確認(macOS 27.2.1、Xcode 27.2 付属の swiftc)
  - https://developer.apple.com/documentation/swiftui/menubarextra
---

# Xcodeでメニューバーアプリを作る

## 要点

- [02-menubar-hello-world.md](02-menubar-hello-world.md) のメニューバーアプリを、**Xcode のプロジェクト**で作る
- Xcode なら、`.app` のフォルダ、`Info.plist`、署名を**自動でやってくれる**。シェルスクリプト(`make-app.sh`)はいらない
- Dock にアイコンを出さない設定(`LSUIElement`)は、`Info.plist` を書かずに、画面の「Info」タブで「Application is agent (UIElement)」を「YES」にする

> この記事の Xcode の手順は、**まだ実機で確かめていません**。画面の名前は Xcode のバージョンで違うことがあります。

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

1. Xcode を起動して、「Create New Project…」を選ぶ(メニューの「File」→「New」→「Project…」でも同じ)
2. 上のタブで「macOS」を選び、「App」を選んで「Next」を押す
3. 次のように入力して「Next」を押す

   | 項目 | 入れるもの |
   |---|---|
   | 「Product Name」 | `HelloMenuBar` |
   | 「Team」 | 「None」のままでよい(自分の Mac で動かすだけなら) |
   | 「Organization Identifier」 | `com.example` など。02 の `CFBundleIdentifier` の前半にあたる |
   | 「Interface」 | 「SwiftUI」 |
   | 「Language」 | 「Swift」 |
   | 「Testing System」/「Storage」 | 「None」 |

4. 保存する場所を選んで「Create」を押す

左の一覧に、`HelloMenuBarApp.swift` と `ContentView.swift` ができる。

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
3. 「Custom macOS Application Target Properties」の表の行にマウスを乗せて「+」を押す(または右クリックで「Add Row」)
4. 「Application is agent (UIElement)」を選び、値を「YES」にする

この設定をしないと、メニューバーに加えて Dock にもアイコンが出る(未確認)。

### 4. 実行する

- 左上の ▶ ボタン(または `Cmd + R`)を押すと、ビルドして起動する
- 画面右上のメニューバーに「Hello World!」が出る。クリックすると「終了」が出る
- 止めるときは、メニューの「終了」を押すか、Xcode の ■ ボタン(または `Cmd + .`)を押す

### 5. 署名を見る

「TARGETS」の「HelloMenuBar」→「Signing & Capabilities」タブで見られる。

- 「Team」が「None」のときは、「Signing Certificate」が「Sign to Run Locally」になる。自分の Mac で動かすための署名で、02 の `codesign --sign -`(アドホック署名)にあたる
- ほかの Mac に配るには、Apple の開発者登録をして「Team」を選ぶ([03-app-bundle-and-codesign.md](03-app-bundle-and-codesign.md) の正式な署名)
- 新しいプロジェクトでは「App Sandbox」(アプリにできることを制限するしくみ)がはじめから入っている。メニューバーに文字を出すだけなら、そのままでよい

### 6. できた .app を取り出す

- **試しに動かしたもの**:メニューの「Product」→「Show Build Folder in Finder」で開いたフォルダの、`Products/Debug/HelloMenuBar.app`
- **普段使いにするもの**:メニューの「Product」→「Archive」で、本番用(Release)にビルドする。終わると「Organizer」の画面が開くので、「Distribute App」から書き出す。選べる項目は Xcode のバージョンで変わる。書き出した `.app` を `/Applications` に置く

`Debug` は02の `swift build`、`Release` は `swift build -c release` にあたる。

## メモ

- この記事の Xcode の手順(画面の名前、`LSUIElement` の設定のしかた、`.app` の場所)は、**どれも実機では未確認**。実際にやってみたら直す
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
