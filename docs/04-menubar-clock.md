---
title: メニューバーに今の時刻を表示する
nav_order: 4
summary: 02のメニューバーアプリを、1秒ごとに進む時刻表示に変える。label:の書き方、.dateTimeの意味、@StateとTimerで表示を更新するしくみを、3段階の編集で学ぶ
keywords: [メニューバー, 時計, 時刻, 現在時刻, MenuBarExtra, label, View, Text, Date, format, dateTime, FormatStyle, formatted, 型名の省略, ドット, "@State", Timer, Timer.publish, onReceive, autoconnect, Combine, 1秒ごと, 更新, 再描画, ログイン項目, 自動起動, SMAppService]
checked: 2026-11-22
verified: 一部実機
thirdparty: []
source:
  - 実機で確認(macOS 27.2.1、Xcode 付属の Apple Swift 6.4.2)
  - https://developer.apple.com/documentation/swiftui/menubarextra
  - https://developer.apple.com/documentation/foundation/date/formatstyle
  - https://developer.apple.com/documentation/foundation/timer
---

# メニューバーに今の時刻を表示する

## 要点

- [02-menubar-hello-world.md](02-menubar-hello-world.md) で作ったアプリを、メニューバーに**1秒ごとに進む時刻**を出すアプリに変える
- メニューバーに出す部分は、`MenuBarExtra { ... } label: { ... }` と書くと、**好きな View** で作れる
- 時刻を進めるには、**`@State` の変数に時刻をしまい、タイマーで1秒ごとに書きかえる**。データが変わると、SwiftUI が表示を作り直す

## 全体の変更内容

ファイルは `Sources/HelloMenuBar/HelloMenuBar.swift` です。

### 変える前(02 の完成形)

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

### 変えた後(この記事の完成形)

```swift
import SwiftUI
import Combine

@main
struct HelloMenuBar: App {
    @State private var now = Date()
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some Scene {
        MenuBarExtra {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        } label: {
            Text(now, format: .dateTime.hour().minute().second())
                .onReceive(timer) { date in
                    now = date
                }
        }
    }
}
```

`./make-app.sh`([02-menubar-hello-world.md](02-menubar-hello-world.md) の「コマンドラインだけで .app にする」)で作り直して起動すると、メニューバーに `23:25:30` のような時刻が出て、1秒ごとに進む。

一度に書きかえると分かりにくいので、下の3段階に分けて編集する。各段階で `./make-app.sh` を実行して、動きを確かめながら進める。

## ステップ1:メニューバーに出す部分を View で書く

### 編集

```swift
// 変える前
        MenuBarExtra("Hello World!") {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        }
```

```swift
// 変えた後
        MenuBarExtra {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        } label: {
            Text("Hello World!")
        }
```

変えるのは2か所。

1. `MenuBarExtra("Hello World!") {` の `("Hello World!")` を消して、`MenuBarExtra {` にする
2. 最後の `}` の後ろに、`} label: { Text("Hello World!") }` を足す

`MenuBarExtra { ... }` の `{ }` には**クリックしたときに出るメニュー**を書き、`label: { ... }` には**メニューバーに出る部分**を書く。

### 確かめ方

見た目は前と変わらない。`Text` の中の文字を変えてみて、メニューバーの表示もその文字に変われば、`label:` の中身が使われていると分かる。

### 何が変わったのか

**View とは**:SwiftUI で、画面に出る部品のこと。

| 書き方 | 画面に出るもの |
|---|---|
| `Text("こんにちは")` | 文字 |
| `Image(systemName: "star")` | アイコン |
| `Button("終了") { ... }` | ボタン |
| `HStack { ... }` | 中に入れた部品を横に並べる箱 |

View の中に別の View を入れて、組み合わせることもできる。

**前と今の違い**

- 前の `MenuBarExtra("Hello World!")` は、**ただの文字列**を渡していた。表示のしかたは `MenuBarExtra` が決めるので、文字しか出せない
- 今の `label: { Text(...) }` は、**View(部品)** を渡している。部品をこちらで作って渡すので、`Text` 以外の部品も入れられる

たとえば、`label:` の中を次のようにすると、アイコンと文字を並べられる(ビルドが通ることは確認した。メニューバーでの見え方は未確認)。

```swift
} label: {
    HStack {
        Image(systemName: "star.fill")
        Text("Hello World!")
    }
}
```

**簡易的な書き方と、汎用的な書き方**

`MenuBarExtra("Hello World!") { ... }` は、`label: { Text("Hello World!") }` と書くのを短くした書き方。中では同じように `Text` が作られている。だから、ステップ1で書きかえても見た目は変わらない。

- **簡易的な書き方**:文字だけで済むときに楽に書ける
- **汎用的な書き方**:`label:` の中に好きな View を入れられる

SwiftUI には、このように両方の書き方が用意されているものが多い。たとえば `Button("終了") { ... }` にも、`Button { ... } label: { ... }` という書き方がある。

### 疑問:`MenuBarExtra(Date())` とは書けないの?

**そのままでは書けない**。短い書き方が受け取れるのは**文字列だけ**で、`Date()`(日時)は別の種類の値だから。実際にビルドすると、次のエラーになった。

```
error: initializer 'init(_:content:)' requires that 'Date' conform to 'StringProtocol'
```

日時を**文字列に直してから**渡せば、短い書き方でも書ける(ビルドが通ることを確認した)。

```swift
MenuBarExtra(Date().formatted(date: .omitted, time: .standard)) { ... }
```

- `.formatted(...)` で、日時を `"23:25:30"` のような文字列にする
- `date: .omitted` は日付を出さない、`time: .standard` は時刻を秒まで出す、という意味

| 書き方 | 渡しているもの |
|---|---|
| `MenuBarExtra(Date().formatted(...))` | 自分で文字列に変えてから、文字列を渡す |
| `label: { Text(Date(), format: ...) }` | 日時のまま `Text` に渡し、文字にするのは `Text` に任せる |

時刻を出すだけならどちらでもよい。アイコンと並べるなど、文字以外のものも出したいときは `label:` の書き方が必要になる。

## ステップ2:起動したときの時刻を出す

### 編集

```swift
// 変える前
        } label: {
            Text("Hello World!")
        }
```

```swift
// 変えた後
        } label: {
            Text(Date(), format: .dateTime.hour().minute().second())
        }
```

`label:` の中の `Text("Hello World!")` を、`Text(Date(), format: ...)` に書きかえるだけ。

| 部分 | 意味 |
|---|---|
| `Date()` | 今の日時 |
| `format:` | どんな形で文字にするかの指定 |
| `.dateTime` | 日時の形にする |
| `.hour().minute().second()` | 時・分・秒を出す |

`.hour()` などは、出したいものを並べて書く。`.second()` を消せば秒が出なくなり、`.month().day()` を足せば日付も出る。

### 確かめ方

メニューバーに時刻が出れば成功。ただし、出るのは**起動したときの時刻**で、そのまま止まっている。これはこの段階では正しい動き。`./make-app.sh` を実行し直すと、そのたびに時刻が変わる。

### 疑問:`.dateTime` の頭の `.` は何?

**型の名前を省略している**。省略しないで書くと、次のようになる(これでもビルドが通ることを確認した)。

```swift
Text(Date(), format: Date.FormatStyle.dateTime.hour().minute().second())
```

- `Date.FormatStyle` は「日時を文字にするときの形」を表す型。`dateTime` は、その型が用意している「日時の形」という決まった値
- 日時を渡しているので、`format:` に入るのは日時用の形(`Date.FormatStyle`)だと Swift には分かっている
- 入る型が分かっている場所では、**型の名前を省略して `.` から書き始めてよい**、というのが Swift の決まり

SwiftUI では、この書き方がよく出てくる。

```swift
.foregroundStyle(.red)      // Color.red の省略
.font(.title)               // Font.title の省略
.padding(.top)              // Edge.Set.top の省略
```

なお、`.dateTime.hour().minute().second()` の中の点には、意味が2種類ある。

- **最初の `.`**:型の名前の省略
- **`.hour()` などの `.`**:前の値に続けて指示する、ふつうのメソッド呼び出し。「日時の形 → 時を足す → 分を足す → 秒を足す」と順につないでいる

### なぜ時刻が止まっているのか

`Date()` が呼ばれるのは、SwiftUI がこの部分の表示を作るとき。SwiftUI は**何かが変わったときにだけ**表示を作り直す。今のコードには変わるものが何もないので、`Date()` が呼ばれるのは起動したときの1回だけになる。

時刻を進めるには、次の2つが必要。

1. **時刻をしまっておく場所**:中身が変わったら、SwiftUI が表示を作り直してくれるもの(ステップ3-1)
2. **1秒ごとに、その中身を新しくするしくみ**(ステップ3-2)

## ステップ3-1:時刻をしまっておく場所を作る

### 編集

```swift
// 変える前
@main
struct HelloMenuBar: App {
    var body: some Scene {
        MenuBarExtra {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        } label: {
            Text(Date(), format: .dateTime.hour().minute().second())
        }
    }
}
```

```swift
// 変えた後
@main
struct HelloMenuBar: App {
    @State private var now = Date()

    var body: some Scene {
        MenuBarExtra {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        } label: {
            Text(now, format: .dateTime.hour().minute().second())
        }
    }
}
```

変えるのは2か所。

1. `struct HelloMenuBar: App {` のすぐ下に、`@State private var now = Date()` を足す
2. `Text` の中の `Date()` を `now` に変える

| 部分 | 意味 |
|---|---|
| `var now` | `now` という名前の変数を作る |
| `= Date()` | 最初の中身は、起動したときの日時 |
| `@State` | この変数の中身が変わったら、SwiftUI が表示を作り直す |
| `private` | この変数は、この `struct` の中だけで使う、という印 |

### 確かめ方

**ステップ2と同じく、起動したときの時刻で止まっていれば正しい**。`now` の中身を変えるものがまだないので、表示も変わらない。

見た目は同じだが、中身は変わっている。

- **ステップ2**:`Text` が自分で `Date()` を呼んで、日時を取っていた
- **ステップ3-1**:日時は `now` にしまってあり、`Text` はそれを見せているだけ。`now` の中身を変えれば、表示も変わる

## ステップ3-2:1秒ごとに時刻を新しくする

### 編集

```swift
// 変えた後(ファイル全体)
import SwiftUI
import Combine

@main
struct HelloMenuBar: App {
    @State private var now = Date()
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some Scene {
        MenuBarExtra {
            Button("終了") {
                NSApplication.shared.terminate(nil)
            }
        } label: {
            Text(now, format: .dateTime.hour().minute().second())
                .onReceive(timer) { date in
                    now = date
                }
        }
    }
}
```

変えるのは3か所。

1. 2行目に `import Combine` を足す
2. `@State private var now = Date()` の下に、`let timer = ...` の行を足す
3. `Text(...)` のすぐ下に、`.onReceive(timer) { ... }` の3行を足す

### 書いたものの意味

**`let timer = Timer.publish(...).autoconnect()`**:1秒ごとに合図を出すタイマー

| 部分 | 意味 |
|---|---|
| `every: 1` | 1秒ごとに合図を出す |
| `on: .main` | 画面と同じ場所(メインスレッド)で合図を出す |
| `in: .common` | メニューを開いている間も止めずに合図を出す |
| `.autoconnect()` | すぐに動き始める |

**`.onReceive(timer) { date in now = date }`**:タイマーの合図を受け取ったら、中の処理をする

- `date` には、合図が出たときの日時が入る
- それを `now` に入れる → `now` は `@State` なので、SwiftUI が表示を作り直す

**`import Combine`**:`Timer.publish` は Combine というしくみの一部。これを書かないと、ビルドのときに次のような警告が出た。

```
warning: cannot use generic class 'Autoconnect' in a property declaration member of a type not marked '@_implementationOnly'; 'Combine' was not imported by this file
```

### 流れのまとめ

タイマーが1秒ごとに合図を出す → `onReceive` が受け取って `now` を新しくする → `now` は `@State` なので表示が作り直される → 時刻が進む

| 部品 | 役目 |
|---|---|
| `@State private var now` | 時刻をしまっておく。中身が変わると表示が作り直される |
| `Timer.publish(...)` | 1秒ごとに合図を出す |
| `.onReceive(timer)` | 合図を受け取って `now` を新しくする |

SwiftUI では、表示を直接書きかえることはしない。**データを変えると、表示は SwiftUI が作り直してくれる**。この時刻表示は、そのしくみのいちばん小さな例。

## Mac の起動時に自動で起動するには(未確認)

ここは実機で試していない。

**いちばん簡単なのは「システム設定」で登録する方法**。コードの書きかえは要らない。

1. 「システム設定」を開く
2. 「一般」→「ログイン項目と機能拡張」(macOS のバージョンによっては「ログイン項目」)を開く
3. 「ログイン時に開く」の下の「+」を押す
4. 作った `.app` を選ぶ

- `./make-app.sh` は、毎回 `.app` を消して作り直す。作り直したあとで一覧から消えていたり、起動しなくなったりしたら、登録し直す
- `.app` を別の場所に動かしたときも、登録し直す

ほかの方法:

- **アプリの中から登録する**:`SMAppService` という Apple のしくみを使うと、メニューに「ログイン時に起動」のような切りかえを作れる。アドホック署名のままでうまく動くかは未確認
- **LaunchAgent を使う**:決まったフォルダに設定ファイル(plist)を置いて、macOS に起動してもらう方法

## メモ

- 実機で確かめたこと:各ステップのコードがビルドできること、完成形でメニューバーに時刻が出て1秒ごとに進むこと。テスト用のコピーで、メニューバーの表示が1秒ごとに作り直されることもログで確かめた
- `MenuBarExtra(Date())` がエラーになること、`.formatted(...)` の版・`HStack` の版・`Date.FormatStyle.dateTime` と省略しない版がビルドできることは確かめた。`HStack` の版のメニューバーでの見え方は未確認
- 自動起動の方法は、すべて未確認
- 時刻を1秒ごとに進める書き方は、ほかにもある(`@Observable` のクラスと `Task` で書く方法など)。この記事では、いちばん部品が少ない `Timer.publish` と `onReceive` を使った
