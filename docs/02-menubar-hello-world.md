---
title: macOSのメニューバーにHello Worldを表示する
nav_order: 2
summary: SwiftUIのMenuBarExtraで、画面右上のメニューバーにHello World!を表示する小さなアプリを作り、コマンドラインだけで.appにする
keywords: [メニューバー, ステータスバー, 右上, MenuBarExtra, SwiftUI, App, NSApplication, platforms, Package.swift, swift run, Hello World, macOS, .app, アプリ化, Info.plist, LSUIElement, codesign, アドホック署名, Spotlight, アプリケーションフォルダ]
checked: 2026-11-20
verified: 一部実機
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

## コマンドラインだけで .app にする

`swift run` はターミナルから動かす練習用の動かし方。ダブルクリックや Spotlight から起動できる `.app` にするのも、コマンドラインだけでできる。

`.app` は、**実行ファイルと設定ファイル(`Info.plist`)を、決まった形のフォルダに入れたもの**。

```
HelloMenuBar.app/
└── Contents/
    ├── Info.plist          ← アプリの名前などの設定
    └── MacOS/
        └── HelloMenuBar    ← swift build でできた実行ファイル
```

毎回手で打つのは大変なので、手順をスクリプトにまとめる。パッケージのフォルダ(`Package.swift` がある所)に `make-app.sh` を作り、次のように書く。

```bash
#!/bin/bash
# swift build でできた実行ファイルから .app を作って、起動するスクリプト。
# 使い方: このフォルダで ./make-app.sh
set -euo pipefail

# --- 設定(必要ならここだけ直す) ---
EXE_NAME="HelloMenuBar"                     # swift build でできる実行ファイルの名前(ターゲット名)
APP_NAME="HelloMenuBar"                     # 作る .app の名前
BUNDLE_ID="com.example.HelloMenuBar"        # アプリを見分ける ID

cd "$(dirname "$0")"

# 1. 本番用にビルドする
echo "1. ビルド中..."
swift build -c release
BIN_PATH="$(swift build -c release --show-bin-path)/$EXE_NAME"

# 起動中なら終わらせる(古い .app を作り直すため)
pkill -f "$APP_NAME.app/Contents/MacOS/" 2>/dev/null || true

# 2. .app の形のフォルダを作り、実行ファイルを入れる
echo "2. $APP_NAME.app を作成中..."
APP="$APP_NAME.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cp "$BIN_PATH" "$APP/Contents/MacOS/$APP_NAME"

# 3. Info.plist(アプリの設定ファイル)を作る
cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# 4. 自分の Mac で動かすための、かんたんな署名をして起動する
echo "3. Info.plist を作成しました"; echo "4. 署名して起動します"
codesign --force --sign - "$APP"

open "$APP"
echo "できました: $(pwd)/$APP"
```

実行できるようにしてから、実行する。

```bash
chmod +x make-app.sh
./make-app.sh
```

同じフォルダに `HelloMenuBar.app` ができて起動し、右上に「Hello World!」が出る。

| スクリプトの中のもの | 意味 |
|---|---|
| `swift build -c release` | 練習用ではなく、本番用(速く動く)にビルドする |
| `EXE_NAME` | `swift build` でできる実行ファイルの名前。`Package.swift` の `.executableTarget(name: ...)` と同じにする |
| `CFBundleExecutable` | 起動する実行ファイルの名前 |
| `CFBundleIdentifier` | アプリを見分けるための ID。ふつうは逆さのドメイン名で書く |
| `CFBundlePackageType` | `APPL` は「これはアプリです」という意味 |
| `LSUIElement` | `true` にすると Dock にアイコンを出さない。メニューバーだけのアプリ向け |
| `codesign --force --sign -` | 自分の Mac で動かすための、かんたんな署名(アドホック署名) |

### .app の置き場所

- `.app` は、どこに置いてあっても起動できる。パッケージのフォルダに置いたままでも、**Spotlight から起動できた**
- アプリケーションフォルダ(`/Applications`)に置くと、Launchpad や Finder の「アプリケーション」に出る。パッケージのフォルダを整理しても残る

  ```bash
  cp -R HelloMenuBar.app /Applications/
  ```

- コピーしたあとで `./make-app.sh` を実行し直しても、作り直されるのはパッケージのフォルダの方だけ。アプリケーションフォルダの方は古いまま残るので、もう一度コピーする

## メモ

- `platforms` を書かずにビルドすると、次のエラーになった(`MenuBarExtra` は macOS 13 以降でしか使えないため)

  ```
  error: 'init(_:content:)' is only available in macOS 13.0 or newer
  ```

  エラーの文は「13.0 以降」だが、この記事では `.v14` にした(13 にしても動くかは未確認)
- 「終了」ボタンを付けておかないと、アプリを終わらせるにはターミナルで `Ctrl + C` するしかない
- 「.app にする」で実機で確かめたのは、スクリプトでの作成・起動、右上への表示、Spotlight からの起動まで。**Dock にアイコンが出ないこと、Finder のダブルクリックでの起動、アプリケーションフォルダにコピーしての起動は未確認**
- アドホック署名(`--sign -`)の `.app` は、自分の Mac で動かす用。**ほかの Mac に配るには向かない**。配るには Apple の開発者登録をして正式に署名する必要がある(未確認)
- Xcode でプロジェクトを作ると、`.app` を作る作業や正式な署名は Xcode がやってくれる(未確認)