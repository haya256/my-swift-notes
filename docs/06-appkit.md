---
title: AppKitとは
nav_order: 6
summary: AppKitはMacのアプリの画面を作る昔からの道具。SwiftUIとの違い(手順を書く/できあがりを書く)、NSで始まる名前、04の時計をAppKitで書き直して比べる
keywords: [AppKit, SwiftUI, UIKit, Cocoa, NeXTSTEP, Objective-C, オブジェクティブC, 言語, selector, "#selector", NSButton.h, 歴史, オプショナル, Optional, オプショナルチェーン, nil, "?", "!", アンラップ, NS, NSApplication, NSStatusBar, NSStatusItem, NSMenu, NSMenuItem, setActivationPolicy, accessory, Timer, scheduledTimer, DateFormatter, MainActor, assumeIsolated, Swift 6, 命令的, 宣言的, フレームワーク, メニューバー, 時計]
checked: 2026-11-25
verified: 一部実機
thirdparty: []
source:
  - 実機で確認(macOS 27.2.1、Xcode 27.2 付属の swiftc)
  - https://developer.apple.com/documentation/appkit
  - https://developer.apple.com/documentation/swiftui
---

# AppKitとは

## 要点

- **AppKit** は、Mac のアプリの画面(ウィンドウ、ボタン、メニュー、メニューバーなど)を作るための、Apple の昔からの道具のセット(フレームワーク)
- AppKit は「**手順を書く**」書き方、SwiftUI は「**できあがりを書く**」書き方。表示が変わるとき、AppKit は自分で書きかえ、SwiftUI は自動で書きかわる
- `NS` で始まる名前(`NSApplication`、`NSMenu` など)は AppKit のもの。02 の SwiftUI 版でも、アプリを終わらせる `NSApplication.shared.terminate(nil)` だけは AppKit を使っている
- AppKit は「Swift より」ではなく「**SwiftUI より**」下の層の道具。Swift は言語で、AppKit と SwiftUI はどちらも Swift から使う道具。AppKit はもともと、Swift の前の言語 **Objective-C** のために作られた

## 言語と道具

```
言語:     Swift(昔は Objective-C)
            ↓ どちらも Swift から使える
道具:     SwiftUI(新しい・できあがりを書く)
            ↓ Mac では、この上に乗っている
          AppKit(昔から・手順を書く)
```

- **Swift** はプログラミング**言語**。**AppKit** と **SwiftUI** は、画面を作るための**道具のセット**(フレームワーク)。この記事の AppKit 版のコードも、Swift で書いている
- AppKit は古いが、今も Apple が更新を続けている現役の道具。Mac のアプリの多くが使っている

### Objective-C とのつながり

**Objective-C** は、Swift が出る前の Apple の開発言語。AppKit は Objective-C で、Objective-C のために作られた。

| 時代 | 言語 | 画面の道具 |
|---|---|---|
| 1980年代後半〜(NeXT 社) | Objective-C | AppKit のもと(NeXTSTEP) |
| 2001年〜(Mac OS X) | Objective-C | AppKit |
| 2014年〜 | **Swift** が登場 | AppKit を Swift から使う |
| 2019年〜 | Swift | **SwiftUI** が登場 |

- Swift は、Objective-C で書かれた道具をそのまま呼び出せるように作られている。そのため、AppKit を作り直さずに Swift から使い続けられた
- **実機で見えた証拠**:下の「メモ」の時計のエラーを出したとき、エラーの中に AppKit の中身(`NSButton.h`)が出てきた。次の行は Swift ではなく Objective-C の書き方。Swift からは `item.button?.title = ...` と使っている `title` が、もともとはこう書かれている

  ```
  @property (copy) NSString *title;
  ```

- Swift のコードに残っている、Objective-C のなごり

  | なごり | 理由 |
  |---|---|
  | `NS` で始まる名前 | Objective-C には、名前を入れ物で分けるしくみ(Swift のモジュールのようなもの)がない。名前がぶつからないように、頭に `NS` を付けた |
  | `#selector(...)` | Objective-C には、「このメソッドを呼んで」と名前で頼むしくみがある。AppKit のメニューはこのしくみで動くので、Swift でも `#selector` で名前を渡す |

- Objective-C は今も動き、古いアプリなどには残っている。新しく書くなら Swift がふつう。読めなくても困らないが、`NS` や `#selector` を見たら「Objective-C 生まれの道具を使っている」と分かれば十分
- 年や歴史は一般的な知識で、この記事では確かめていない

## AppKit と SwiftUI

| | AppKit | SwiftUI |
|---|---|---|
| いつから | 2001年の Mac OS X から。そのもとの NeXTSTEP から数えると、もっと前から | 2019年から |
| 書き方 | **手順を書く**:「場所をもらう → 文字を入れる → メニューを作る → くっつける」 | **できあがりを書く**:「メニューバーに、この文字と、このメニュー」 |
| 表示の更新 | 変わるたびに、自分で書きかえる | `@State` が変わると、自動で書きかわる |
| 名前の目印 | `NS` で始まる(NS は NeXTSTEP の略) | `MenuBarExtra`、`Button`、`Text` など |
| 使える所 | Mac だけ | Mac でも iPhone でも、同じ書き方で使える |

- iPhone 用で AppKit にあたるものは **UIKit**(`UIButton` のように `UI` で始まる)
- Mac では、SwiftUI は AppKit の上に乗って動いている。SwiftUI は「AppKit を楽に使うための、新しい書き方」と考えると分かりやすい。`MenuBarExtra` も、裏では AppKit の `NSStatusItem` を使っているはず(未確認)
- SwiftUI にない機能は、AppKit を借りて使う。02 の `NSApplication.shared.terminate(nil)` がその例
- 「いつから」や「Mac では SwiftUI が AppKit の上で動いている」は一般的な知識で、この記事では確かめていない

## 同じものを2つの書き方で比べる

### Hello World

[02-menubar-hello-world.md](02-menubar-hello-world.md) の SwiftUI 版:

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

AppKit 版([05-menubar-xcode.md](05-menubar-xcode.md) の「AppKit で書く」と同じ):

```swift
import AppKit

let app = NSApplication.shared
app.setActivationPolicy(.accessory)  // Dockに出さない(LSUIElementの代わり)

let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
item.button?.title = "Hello World!"

let menu = NSMenu()
menu.addItem(NSMenuItem(title: "終了",
                        action: #selector(NSApplication.terminate(_:)),
                        keyEquivalent: "q"))
item.menu = menu

app.run()
```

- SwiftUI 版は「メニューバーに "Hello World!"、中に"終了"ボタン」と、**できあがりの形**だけを書いている
- AppKit 版は、上から順に**作業の手順**を書いている。メニューバーに場所をもらい(`statusItem`)、文字を入れ(`title`)、メニューを作り(`NSMenu`)、くっつける(`item.menu = menu`)。最後に `app.run()` でアプリを動かし続ける

#### `item.button?` の `?`(オプショナル)

`item.button?.title = ...` の `?` は、「**ボタンがあれば** `title` を書きかえる。なければ何もしない」という意味(**オプショナルチェーン**)。

- `item.button` の型は `NSStatusBarButton?`。型の後ろの `?` は「**オプショナル**」の印で、「中身が入っているかもしれないし、空(`nil`)かもしれない」という意味
- 空かもしれないものの中身を、いきなり触ることはできない。`?` を外して `item.button.title = "Hello"` と書くと、ビルドで次のエラーになった

  ```
  error: value of optional type 'NSStatusBarButton?' must be unwrapped to refer to member 'title' ...
  note: chain the optional using '?' to access member 'title' only for non-'nil' base values
  note: force-unwrap using '!' to abort execution if the optional value contains 'nil'
  ```

- エラーの `note:` が、直し方を2つ教えてくれている

  | 書き方 | 意味 | 空だったら |
  |---|---|---|
  | `item.button?.title = ...` | あれば書きかえる(オプショナルチェーン) | 何もしない |
  | `item.button!.title = ...` | 必ずあるはずなので、そのまま書きかえる | **アプリが落ちる** |

  ふつうは、安全な `?` を使う
- 「空かもしれない」は Objective-C から来ている。Objective-C では、どんなものも空(`nil`)になりえた。Swift はそれを型ではっきりさせて、空かもしれないものには `?` を付ける決まりにした。AppKit は Objective-C 生まれなので、Swift から使うと `?` がよく出てくる(この段落は一般的な知識)
- メニューバーのボタンは、実際にはまず空にならないが、型の上では「空かもしれない」とされている

### 時計([04-menubar-clock.md](04-menubar-clock.md))

違いがいちばんよく分かるのは、**表示が変わるとき**。04 の時計を AppKit で書くと、次のようになる。

```swift
import AppKit

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

let formatter = DateFormatter()
formatter.dateFormat = "HH:mm:ss"

let timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
    MainActor.assumeIsolated {
        item.button?.title = formatter.string(from: Date())
    }
}
timer.fire()

let menu = NSMenu()
menu.addItem(NSMenuItem(title: "終了",
                        action: #selector(NSApplication.terminate(_:)),
                        keyEquivalent: "q"))
item.menu = menu

app.run()
```

`clock.swift` という名前で保存して、`swift clock.swift` で動かす。

| 書いてあること | 意味 |
|---|---|
| `DateFormatter()` / `dateFormat = "HH:mm:ss"` | 時刻を `23:25:30` のような文字にする道具と、その形 |
| `Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { ... }` | 1秒ごとに `{ }` の中を実行するタイマー |
| `item.button?.title = ...` | メニューバーの文字を、**自分で書きかえる**(`?` の意味は上の「オプショナル」) |
| `MainActor.assumeIsolated { ... }` | 「ここは画面を担当する場所(メインスレッド)で動いている」とコンパイラーに伝える(下の「メモ」) |
| `timer.fire()` | タイマーを今すぐ1回動かす。これがないと、起動してから1秒間は何も出ない |

**比べると分かること**

- SwiftUI 版(04)は、`@State` の変数 `now` を新しい時刻にするだけ。`Text(now, ...)` の表示は SwiftUI が**自動で**作り直す
- AppKit 版は、1秒ごとに**自分で** `title` に新しい文字を入れている。どこを書きかえるかを、全部自分で決める
- 小さいアプリならどちらも同じくらいの長さ。画面の部品が増えるほど、「書きかえ忘れ」が起きにくい SwiftUI の方が楽になる

## どちらを使えばいいか

- **これから Mac のアプリを作るなら SwiftUI** を基本にする。Mac でも iPhone でも同じ書き方で使え、このリポジトリの記事(02、04、05)も SwiftUI で書いている
- SwiftUI にない機能や、細かい調整が必要なときだけ、AppKit を借りる(`NSApplication.shared.terminate(nil)` のように)
- **AppKit を知っておくとよい理由**:ネットの情報や古いサンプルには AppKit のコードが多い。`NS` で始まる名前を見たら「AppKit だ」と分かると、読みやすくなる
- ファイル1つで `swift hello.swift` だけで動かしたいときは、AppKit 版が手軽(`@main` がないので、`-parse-as-library` もいらない。[05-menubar-xcode.md](05-menubar-xcode.md) の「どの作り方を選ぶか」)

## メモ

- 実機で確かめたこと
  - Hello World の AppKit 版:`swift hello.swift` で、右上に「Hello World!」が出て、Dock にアイコンが出なかった
  - 時計の AppKit 版:`swiftc` でビルドでき、`swift clock.swift` で起動して動き続けた。**右上に時刻が出て1秒ごとに進むかは、目で見ていない**
- **時計の AppKit 版は、はじめ `MainActor.assumeIsolated` なしで書いたら、Swift 6 のモードでエラーになった**

  ```bash
  swiftc -swift-version 6 clock.swift -o clock
  ```

  ```
  error: main actor-isolated let 'item' can not be referenced from a nonisolated context
  ```

  - 画面の部品(ここでは `item`)は、**メインスレッド**(画面を担当する場所)からしか触ってはいけない決まりがある。Swift 6 は、この決まりをコンパイルのときに検査する
  - タイマーの `{ }` の中は、「どこで動くか分からない場所」と見なされるので、エラーになる。実際には、メインスレッドで作ったタイマーはメインスレッドで動く(一般的な知識)。そこで `MainActor.assumeIsolated { }` で「ここはメインスレッドだ」と伝える
  - `swiftc` や `swift` をオプションなしで使うと Swift 5 のモードになり、この検査はゆるい。Xcode の新しいプロジェクトが Swift 6 のモードかどうかは未確認
  - 関数 `update()` に `@MainActor` を付ける書き方も試したが、今度は Swift 5 のモードでエラーになった。上のコードは、Swift 5 と 6 のどちらのモードでもビルドできることを確かめた
- 04 の SwiftUI 版は `.dateTime.hour().minute().second()` で、Mac の設定に合わせた形で時刻を出す。AppKit 版の `"HH:mm:ss"` は、いつも `23:25:30` の形になる
