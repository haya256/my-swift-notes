---
title: macOSでSwiftのHello World
nav_order: 1
summary: macOSでSwiftをインストールしてHello Worldを表示する3つの方法(スクリプト実行・swiftc・Swift Package)
keywords: [Hello World, はじめて, インストール, swift, swiftc, swift run, swift package init, Command Line Tools, xcode-select, Xcode, macOS]
checked: 2026-11-20
verified: 一部実機
thirdparty: []
source:
  - 実機で確認(macOS 27.2.1、Xcode 付属の Apple Swift 6.4.2)
  - https://www.swift.org/install/macos/
  - https://www.swift.org/getting-started/
---

# macOSでSwiftのHello World

## 要点

- macOS では **Xcode か Command Line Tools を入れると `swift` コマンドが使える**。`swift --version` で確かめる
- いちばん手軽なのは、`print("Hello, World!")` と書いたファイルを `swift hello.swift` で実行する方法
- ちゃんとしたプログラムを作るなら、`swift package init --type executable` でパッケージを作り、`swift run` で実行する

## 準備:Swift が使えるか確かめる

ターミナルで次を実行します。

```bash
swift --version
```

次のように `Apple Swift version ...` と出れば準備はできています(数字は環境によって変わります)。

```
swift-driver version: 1.168.6 Apple Swift version 6.4.2 (swiftlang-6.4.2.1.9 clang-2100.4.1.1)
Target: arm64-apple-macosx27.2.0
```

出ないときは、次のどちらかを入れます。

- **Xcode**:App Store からインストールする。iPhone・Mac のアプリも作るならこちら
- **Command Line Tools**(Xcode より小さい):ターミナルで次を実行し、出てきたダイアログでインストールする

  ```bash
  xcode-select --install
  ```

## 方法1:ファイルをそのまま実行する(いちばん手軽)

1. `hello.swift` というファイルを作り、次の1行を書く

   ```swift
   print("Hello, World!")
   ```

2. ファイルのあるフォルダで実行する

   ```bash
   swift hello.swift
   ```

3. `Hello, World!` と表示される

`main` 関数などは要りません。ファイルの上から順に実行されます。

## 方法2:swiftc でコンパイルしてから実行する

```bash
swiftc hello.swift -o hello
./hello
```

`hello` という実行ファイルができます。一度作れば、次からは `./hello` だけで動きます。

## 方法3:Swift Package を作って実行する(おすすめ)

ファイルが増えたり、ライブラリを使ったりするなら、Swift Package Manager でパッケージを作ります。

1. フォルダを作って、その中でパッケージを作る

   ```bash
   mkdir HelloWorld
   cd HelloWorld
   swift package init --type executable
   ```

   次のファイルができます。

   ```
   HelloWorld/
   ├── Package.swift                          ← パッケージの設定
   ├── Sources/HelloWorld/HelloWorld.swift    ← プログラム本体
   └── Tests/HelloWorldTests/HelloWorldTests.swift
   ```

2. `Sources/HelloWorld/HelloWorld.swift` には、最初から Hello World が書かれている

   ```swift
   @main
   struct HelloWorld {
       static func main() {
           print("Hello, world!")
       }
   }
   ```

   1行版より長いが、文字を表示しているのは `print("Hello, world!")` の1行だけ。まわりは「プログラムをここから始める」という目印の枠。

   | 書いてあること | 意味 |
   |---|---|
   | `print("Hello, world!")` | 文字を表示する。方法1の1行と同じ |
   | `static func main() { ... }` | `main` という名前の処理。`{ }` の中が、起動したときに上から順に実行される |
   | `struct HelloWorld { ... }` | `main` を入れておく入れ物(構造体)に、`HelloWorld` という名前を付けている |
   | `@main` | 「プログラムはこの入れ物の `main` から始める」という目印 |

   方法1はファイルが1つなので、Swift は「上から順に実行すればいい」と分かり、1行で動く。パッケージはファイルが増える前提なので、どこから始めるかを `@main` ではっきり書く決まりになっている。

   はじめのうちは、**`static func main() { }` の中に書いた文が上から順に実行される**とだけ覚えればよい。たとえば次のように `print` を2行にすると、2行表示される。

   ```swift
       static func main() {
           print("Hello, world!")
           print("こんにちは")
       }
   ```

   `struct` や `static` の意味は、Swift に慣れてからで十分。

3. ビルドして実行する

   ```bash
   swift run
   ```

   ビルドのメッセージのあとに `Hello, world!` と表示される。

## メモ

- 実機で確かめたのは、Swift がすでに入っている環境(Xcode あり)での方法1〜3。**Command Line Tools を新しく入れる手順は未確認**(公式の案内をもとに書いた)
- 方法3でできるファイル名や中身は、Swift のバージョンによって変わる。Swift 6.4.2 では `main.swift` ではなく、`@main` の付いた `HelloWorld.swift` ができた
- 方法3で表示される `Hello, world!`(`w` が小文字)は、`swift package init` が自動で作るサンプルのコードに最初から書かれている文字。方法1・2の `Hello, World!` とは大文字・小文字がちがうだけで、意味や動きは同じ
- 方法3のサンプルを自分のプログラムにするには、`HelloWorld.swift` の `print("Hello, world!")` の文字を好きなものに変えて、もう一度 `swift run` する
- 方法3の初回の `swift run` は、ビルドに数秒かかる(試した環境では約6秒)。2回目からは速い
- 標準入力からも実行できる:`echo 'print("Hi")' | swift -`
- Xcode のアプリで作りたいときは、Xcode の「File」→「New」→「Package...」でもパッケージを作れる(未確認)
