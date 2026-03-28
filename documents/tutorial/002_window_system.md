# 002 - ウィンドウシステム

## 概要

キャラクターの会話表示に使用するメッセージウィンドウシステムを実装した。
既存の `Window` クラスを基底クラス (`BaseWindow`) としてリファクタリングし、用途別に子クラスを作成する設計とした。

## クラス構成

```
BaseWindow（基底クラス）
├── OverlayWindow（汎用オーバーレイ）
└── MessageWindow（メッセージ表示専用）
```

### BaseWindow (`src/ui/window.py`)

すべてのウィンドウに共通する機能を持つ基底クラス。

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `x` | int | - | ウィンドウ左上のx座標 |
| `y` | int | - | ウィンドウ左上のy座標 |
| `width` | int | - | ウィンドウの幅 |
| `height` | int | - | ウィンドウの高さ |
| `bg_color` | int | 1 | 背景色（Pyxelカラーインデックス） |
| `border_color` | int | 7 | 枠線の色 |
| `has_border` | bool | True | 枠線を描画するか |
| `semi_transparent` | bool | False | 背景を半透明にするか |

**半透明の仕組み:** Pyxelの `pyxel.dither()` を使用。`dither(0.5)` で背景を描画し、その後 `dither(1.0)` に戻すことで半透明効果を実現する。

### OverlayWindow (`src/ui/window.py`)

既存の `Window` クラスの機能を継承した汎用オーバーレイウィンドウ。
設定画面やヘルプ表示など、シーン遷移せずに情報を重ねて表示したいときに使う。

```python
from ui.window import OverlayWindow

window = OverlayWindow(x=48, y=48, width=160, height=160)
window.open(lines=["~ OPTION MENU ~", "", "No settings yet."])
```

**後方互換:** `from ui.window import Window` で `OverlayWindow` がインポートされるので、既存コードはそのまま動作する。

### MessageWindow (`src/ui/message_window.py`)

キャラクターの会話やナレーション表示に特化したウィンドウ。

## MessageWindowの使い方

### 基本的な使い方

```python
from ui.message_window import MessageWindow

# インスタンス生成（デフォルトは画面下部に配置）
msg_window = MessageWindow()

# メッセージを表示（文字列のリストを渡す）
msg_window.show([
    "Hello!\nThis is a message\nwindow system.",
    "Second message here.",
])
```

### キャラクター名付きメッセージ

```python
msg_window.show([
    {
        "text": "Nice to meet you!\nI'm Alice.",
        "name": "Alice",
    },
    {
        "text": "Hi Alice!\nI'm Bob.",
        "name": "Bob",
    },
])
```

`name` を指定すると、ウィンドウの左上に名前ウィンドウが表示される。

### 顔グラフィック付きメッセージ

```python
msg_window.show([
    {
        "text": "Greetings!",
        "name": "Alice",
        "face": (0, 0, 0, 40, 40),  # (img, u, v, w, h)
    },
])
```

`face` にタプル `(イメージバンク番号, u, v, w, h)` を渡すと、ウィンドウ左側に顔グラフィックが表示される。
`pyxel.blt()` で描画され、カラーキー0（黒）が透過色として扱われる。

### 自動送りメッセージ

```python
msg_window.show([
    {
        "text": "This will auto-advance.",
        "auto": True,
    },
    "This requires key input.",
])
```

`auto: True` を指定すると、テキスト表示完了後に自動的に次のメッセージへ進む（デフォルト60フレーム待機）。

### テキスト表示速度の変更

```python
from ui.message_window import TEXT_SPEED_FAST, TEXT_SPEED_NORMAL, TEXT_SPEED_SLOW

msg_window.set_text_speed(TEXT_SPEED_FAST)    # 1フレーム/文字
msg_window.set_text_speed(TEXT_SPEED_NORMAL)  # 2フレーム/文字（デフォルト）
msg_window.set_text_speed(TEXT_SPEED_SLOW)    # 4フレーム/文字
```

ゲームオプション画面から速度を変更する場合は、この `set_text_speed()` を呼び出す。

### 混合メッセージ（str と dict の混在）

```python
msg_window.show([
    {"text": "Named message.", "name": "Alice"},
    "Simple string message.",           # 名前・顔グラなし
    {"text": "Auto message.", "auto": True},
])
```

リスト内で `str` と `dict` を混在させることができる。`str` の場合は名前・顔グラなしのシンプルなメッセージとして扱われる。

## シーンへの組み込み方

```python
import pyxel
from scenes.base import Scene
from ui.message_window import MessageWindow

class MyScene(Scene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.msg_window = MessageWindow()

    def update(self):
        # メッセージウィンドウが開いている場合はそちらの入力を優先
        if self.msg_window.is_open:
            self.msg_window.update()
            return

        # 通常のシーン入力処理...
        if some_event_triggered:
            self.msg_window.show([...])

    def draw(self):
        pyxel.cls(0)
        # シーンの通常描画...

        # メッセージウィンドウは最前面に描画
        self.msg_window.draw()
```

**ポイント:**
- `update()` でメッセージウィンドウが開いている間は他の入力を無視する
- `draw()` ではメッセージウィンドウを最後に描画して最前面に表示する
- `msg_window.is_open` / `msg_window.is_busy` でウィンドウの状態を確認できる

## 定数一覧 (`src/ui/message_window.py`)

| 定数名 | 値 | 説明 |
|---|---|---|
| `MSG_WINDOW_X` | 8 | メッセージウィンドウのデフォルトx座標 |
| `MSG_WINDOW_Y` | 192 | メッセージウィンドウのデフォルトy座標 |
| `MSG_WINDOW_WIDTH` | 240 | メッセージウィンドウのデフォルト幅 |
| `MSG_WINDOW_HEIGHT` | 56 | メッセージウィンドウのデフォルト高さ |
| `FACE_SIZE` | 40 | 顔グラフィックのサイズ |
| `MAX_LINES` | 3 | 1メッセージあたりの最大行数 |
| `TEXT_SPEED_FAST` | 1 | 高速表示（1フレーム/文字） |
| `TEXT_SPEED_NORMAL` | 2 | 通常表示（2フレーム/文字） |
| `TEXT_SPEED_SLOW` | 4 | 低速表示（4フレーム/文字） |

## 操作方法

| キー | 動作 |
|---|---|
| Enter / Space | テキスト表示中: 即時表示完了 |
| Enter / Space | テキスト表示完了後: 次のメッセージへ進む |

テキストがすべて表示され、次のメッセージがある場合はウィンドウ右下に `v` アイコンが点滅・上下アニメーションで表示される。

## ファイル構成

```
src/ui/
├── __init__.py
├── window.py            # BaseWindow + OverlayWindow（+ 後方互換 Window）
├── menu.py              # メニューUI
└── message_window.py    # MessageWindow
```
