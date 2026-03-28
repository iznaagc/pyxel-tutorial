# 004: カスタムフォントと解像度変更

## 概要

ゲーム画面を **256x256** から **480x270（16:9）** に変更し、
カスタムフォント **madoufmg.ttf** を **16px** で使用するように全体を改修した。

---

## 背景・目的

- デフォルトのPyxel内蔵フォントは **4x6px** で非常に小さく、日本語表示に不向き
- `assets/fonts/madoufmg.ttf` を使い、**1文字16px** の読みやすいテキストにしたい
- 16pxフォントを活かすには256x256では狭すぎるため、**480x270（16:9）** に拡大

---

## Pyxel のカスタムフォント機能

### pyxel.Font クラス

Pyxel 2.1 以降で利用可能。**BDF** と **TTF/OTF** の両方に対応している。

```python
# TTFフォントをサイズ指定で読み込み
font = pyxel.Font("path/to/font.ttf", 16)

# BDFフォント（サイズはフォント自体に固定）
font = pyxel.Font("path/to/font.bdf")
```

### テキスト描画

`pyxel.text()` の第5引数に Font オブジェクトを渡す。

```python
# デフォルトフォント（4x6px）
pyxel.text(10, 10, "Hello", 7)

# カスタムフォント
pyxel.text(10, 10, "こんにちは", 7, font)
```

### テキスト幅の計測

レイアウト計算に便利な `text_width()` メソッドがある。

```python
width = font.text_width("こんにちは")  # → 80 (16px × 5文字)
```

---

## 実装内容

### 1. config.py（新規作成）

ゲーム全体の共通設定を集約するモジュール。

```python
import os
import pyxel

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 270

FONT_SIZE = 16
FONT_PATH = os.path.join(_PROJECT_ROOT, "assets", "fonts", "madoufmg.ttf")

FONT = None

def init_font():
    global FONT
    FONT = pyxel.Font(FONT_PATH, FONT_SIZE)
```

**ポイント:**
- `__file__` からプロジェクトルートを算出して **絶対パス** でフォントを参照
- `src/` ディレクトリから実行しても、他のディレクトリから実行してもパスが通る
- `pyxel.init()` の後でないと `pyxel.Font()` が使えないため、`init_font()` を分離

### 2. app.py の変更

```python
import config

class App:
    def __init__(self):
        pyxel.init(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, title="My Game")
        config.init_font()  # pyxel.init() の直後に呼ぶ
```

- 定数を `config` から参照するように変更
- フォント初期化を `pyxel.init()` 直後に実行

### 3. message_window.py の定数変更

| 定数 | 変更前 | 変更後 | 理由 |
|------|--------|--------|------|
| `MSG_WINDOW_X` | 8 | 8 | 据え置き |
| `MSG_WINDOW_Y` | 192 | 182 | 画面下部（270 - 80 - 8） |
| `MSG_WINDOW_WIDTH` | 240 | 464 | 画面幅480 - 余白16 |
| `MSG_WINDOW_HEIGHT` | 56 | 80 | 3行×20px + パディング |
| `NAME_WINDOW_HEIGHT` | 14 | 24 | 16pxフォント + 余白 |
| `NAME_WINDOW_PADDING` | 4 | 6 | バランス調整 |
| `FACE_SIZE` | 40 | 56 | ウィンドウ拡大に合わせて |
| `FACE_PADDING` | 4 | 6 | バランス調整 |
| `TEXT_PADDING` | 6 | 8 | バランス調整 |
| `LINE_HEIGHT` | 10 | 20 | 16px + 行間4px |
| `FONT_WIDTH` | 4 | 削除 | `text_width()` で動的に計算 |

### 4. 描画関数のフォント対応

すべての `pyxel.text()` 呼び出しに `config.FONT` を渡すように変更。

```python
# 変更前
pyxel.text(text_x, y, visible, self.text_color)

# 変更後
pyxel.text(text_x, y, visible, self.text_color, config.FONT)
```

対象ファイル:
- `ui/message_window.py` — テキスト描画、名前ウィンドウ、次アイコン
- `ui/window.py` — OverlayWindow のテキスト・ヒント描画
- `ui/menu.py` — メニュー項目の描画
- `scenes/title.py` — タイトルテキスト
- `scenes/game.py` — シーン内テキスト

### 5. 名前ウィンドウの幅計算を動的化

```python
# 変更前: 固定幅で計算
name_width = len(name) * FONT_WIDTH + NAME_WINDOW_PADDING * 2

# 変更後: フォントの実測値で計算
name_text_w = font.text_width(name) if font else len(name) * 4
name_width = name_text_w + NAME_WINDOW_PADDING * 2
```

日本語名前（全角）と英語名前（半角）で幅が自動的に正しく算出される。

### 6. UI 位置の調整

**メニュー（menu.py）:** 行間 10px → **24px**（16pxフォント + 余白8px）

**タイトルシーン（title.py）:**
- タイトルテキスト: (90, 40) → (160, 50)
- メニュー位置: (100, 120) → (200, 120)
- オプションウィンドウ: 48,48,160x160 → 100,50,280x170

**ゲームシーン（game.py）:** 全テキスト位置を480x270の中央寄りに調整

---

## テキスト領域の文字数計算

480x270 画面でのメッセージウィンドウのテキスト表示能力:

```
ウィンドウ幅:        464px
左右パディング:      8px × 2 = 16px
テキスト領域幅:      464 - 16 = 448px

全角文字（16px幅）:  448 / 16 = 28文字/行
半角文字（ 8px幅）:  448 /  8 = 56文字/行
行数:                最大3行
```

### デモシーンのテストパターン

game.py に以下のテストパターンを実装:

| # | テスト | 確認ポイント |
|---|--------|-------------|
| 1-2 | 日本語基本会話 | フォント描画・名前ウィンドウ |
| 3 | 全角28文字 | 1行ぴったり収まるか |
| 4 | 全角29文字 | 1文字はみ出し |
| 5 | 全角30文字 | 2文字はみ出し |
| 6 | 半角56文字 | 半角の限界値 |
| 7 | 半角60文字 | 半角はみ出し |
| 8 | 3行びっしり | 実用的な文章量 |
| 9 | 日英混在 | HP、Lv等ゲーム頻出パターン |
| 10 | 1行のみ | 最小メッセージ |
| 11 | 名前なし | 名前ウィンドウ非表示 |
| 12 | 長い名前 | 名前ウィンドウ幅の伸び |
| 13 | 自動送り | auto機能確認 |

---

## ファイル構成（変更後）

```
src/
├── config.py              ← 新規: 解像度・フォント設定
├── app.py                 ← 変更: config参照、init_font()追加
├── main.py                   （変更なし）
├── core/
│   └── scene_manager.py      （変更なし）
├── scenes/
│   ├── base.py               （変更なし）
│   ├── title.py           ← 変更: UI位置調整、フォント適用
│   └── game.py            ← 変更: テストデモ拡充、フォント適用
└── ui/
    ├── window.py          ← 変更: OverlayWindow フォント適用
    ├── menu.py            ← 変更: メニュー フォント適用
    └── message_window.py  ← 変更: 定数・レイアウト全面改修

assets/
└── fonts/
    └── madoufmg.ttf          使用フォント
```

---

## 注意点・ハマりどころ

### フォントパスは絶対パスで指定する

`pyxel.Font()` に渡すパスは実行時のカレントディレクトリからの相対パスとして解決される。
`src/` ディレクトリで実行する場合、`assets/fonts/...` は見つからない。

**解決策:** `config.py` で `__file__` からプロジェクトルートを算出し、絶対パスを構築する。

### pyxel.Font() は pyxel.init() の後に呼ぶ

Pyxel が初期化されていない状態で `pyxel.Font()` を呼ぶとエラーになる。
`config.init_font()` を `pyxel.init()` の直後に呼ぶ設計にしている。

### 自動改行はない

Pyxel にはテキストの自動折り返し機能がない。
1行に収まる文字数を意識してテキストを `\n` で手動改行する必要がある。
将来的に自動改行機能を `MessageWindow` に実装する余地がある。
