---
title: macOSのメニューバーにHello Worldを表示する
nav_order: 2
summary: SwiftUIのMenuBarExtraで、画面右上のメニューバーにHello World!を表示する小さなアプリを作る
keywords: [メニューバー, ステータスバー, 右上, MenuBarExtra, SwiftUI, App, NSApplication, platforms, Package.swift, swift run, Hello World, macOS]
checked: 2026-11-20
verified: 実機
thirdparty: []
source:
  - 実機で確認(macOS 27.2.1、Xcode 付属の Apple Swift 6.4.2)
  - https://developer.apple.com/documentation/swiftui/menubarextra
---

# macOSのメニューバーにHello Worldを表示する

## 要点

- SwiftUI の **`MenuBarExtra`** を使うと、画面右上のメニューバーに文字を出せる
- Swift Package で作れる。書くファイルは `Package.swift` と `HelloMenuBar.swift` の2つだけ
- `Package.swift` に **`platforms: [.macOS(.v14)]`** を書かないと、ビルドでエラーになる

Swift Package の作り方や `@main` の意味は、[01-hello-world.md](01-hello-world.md) の「方法3」を見てください。

## 手順

### 1. パッケージを作る

```bash
mkdir HelloMenuBar
cd HelloMenuBar
swift package init --type executable
```

自動で作られる `Tests` フォルダは使わないので消しておく(手順2で設定からテストを外すため、残っていても使われない)。

```bash
rm -rf Tests
```

### 2. `Package.swift` を書きかえる

中身を全部消して、次のように書く。

```swift
// swift-tools-version: 6.4

import PackageDescription

let package = Package(
    name: "HelloMenuBar",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "HelloMenuBar"),
    ]
)
```

- いちばん大事なのは **`platforms: [.macOS(.v14)]`** の1行。「このアプリは macOS 14 以降で動かす」という意味
- 1行目の `swift-tools-version` は、`swift package init` で作られた数字をそのまま使う(Swift のバージョンによって変わる)

### 3. `Sources/HelloMenuBar/HelloMenuBar.swift` を書きかえる

```swift
import SwiftUI

@main
struct HelloMenuBar: App {
    var body: some Scene {
        MenuBarExtra("Hello World!") {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        }
    }
}
```

### 4. 実行する

```bash
swift run
```

- 画面右上のメニューバーに「Hello World!」が出る
- 「Hello World!」をクリックすると「終了」が出る。押すとアプリが終わる
- ターミナルで `Ctrl + C` を押しても終わる

## コードの意味

| 書いてあること | 意味 |
|---|---|
| `import SwiftUI` | 画面を作る道具(SwiftUI)を使えるようにする |
| `@main` | 「プログラムはここから始める」という目印([01-hello-world.md](01-hello-world.md) と同じ) |
| `struct HelloMenuBar: App` | `: App` を付けると「これはアプリだよ」という意味になる |
| `var body: some Scene { ... }` | アプリが何を表示するかを書く場所 |
| `MenuBarExtra("Hello World!") { ... }` | メニューバーに「Hello World!」を出す。`{ }` の中が、クリックしたときに出るメニュー |
| `Button("終了") { ... }` | メニューの中のボタン。`{ }` の中が、押したときに実行される |
| `NSApplication.shared.terminate(nil)` | アプリを終わらせる |

[01-hello-world.md](01-hello-world.md) のサンプルにあった `static func main()` は書かない。`: App` を付けると、アプリの始め方は SwiftUI がやってくれる。

## メモ

- `platforms` を書かずにビルドすると、次のエラーになった(`MenuBarExtra` は macOS 13 以降でしか使えないため)

  ```
  error: 'init(_:content:)' is only available in macOS 13.0 or newer
  ```

  エラーの文は「13.0 以降」だが、この記事では `.v14` にした(13 にしても動くかは未確認)
- 「終了」ボタンを付けておかないと、アプリを終わらせるにはターミナルで `Ctrl + C` するしかない
- この作り方は `swift run` で動かすための、練習用の作り方。ダブルクリックで起動できる普通のアプリ(`.app`)にするには、Xcode でプロジェクトを作るなど別の手順が要る(未確認)
