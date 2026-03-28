# 006: テロップシステム

## 概要

テキストを下から上にスクロール表示する **TelopWindow** を実装した。
オープニングのストーリー表示やスタッフロールなど、
長い文章を画面上に流して見せる演出に使用する。

---

## 背景・目的

- RPGのオープニングで物語の導入テキストを表示したい
- エンディングでスタッフロール（クレジット）を流したい
- 既存のウィンドウシステム（BaseWindow）を流用し、最小限のコードで実現する

---

## 設計判断：BaseWindow に盛り込むか、別クラスにするか

計画書（006_create_telop_system.md）の問い「ウィンドウベースクラスに盛り込んでも問題ないか」に対する結論:

**BaseWindow には最小限の変更のみ、テロップ固有の機能は専用サブクラスに分離。**

| 変更先 | 変更内容 | 理由 |
|--------|----------|------|
| BaseWindow | `has_bg` フラグ追加 | 背景非表示は他のウィンドウでも汎用的に使える |
| TelopWindow（新規） | スクロール制御、中央揃え等 | テロップ固有のアニメーション機能であり、他のウィンドウには不要 |

### has_bg フラグ

BaseWindow に `has_bg=True` パラメータを追加。`False` のとき背景の `pyxel.rect()` 描画をスキップする。

```python
# 変更前: 常に背景を描画
pyxel.rect(self.x, self.y, self.width, self.height, self.bg_color)

# 変更後: has_bg=True のときだけ描画
if self.has_bg:
    pyxel.rect(self.x, self.y, self.width, self.height, self.bg_color)
```

既存のサブクラス（OverlayWindow, MessageWindow, SelectWindow）は `has_bg` を指定しないため、デフォルトの `True` で動作が変わらない。

---

## クラス構成

```
BaseWindow（基底クラス）
├── OverlayWindow（汎用オーバーレイ）
├── MessageWindow（メッセージ表示専用）
├── SelectWindow（選択肢ウィンドウ）
└── TelopWindow（テロップ表示）  ← 新規
```

---

## TelopWindow

### スクロールの仕組み

**「文字を動かすのではなくウィンドウごと動かす」** 方式を採用。

```
フレーム0:   ウィンドウ全体が画面下端の下に配置される
              ┌──画面──────────┐
              │                    │
              │                    │
              └────────────────────┘
              ┌──ウィンドウ────────┐  ← y = 270 (画面下端)
              │ テキスト行1        │
              │ テキスト行2        │
              │ ...                │
              └────────────────────┘

フレームN:   ウィンドウが上方向に移動し、テキストが画面内に入る
              ┌──画面──────────┐
              │ テキスト行3        │  ← ウィンドウの一部が画面内
              │ テキスト行4        │
              │ テキスト行5        │
              └────────────────────┘

完了:        ウィンドウ全体が画面上端の上に出たら完了
              ┌──ウィンドウ────────┐  ← y + height < 0
              │ ...                │
              └────────────────────┘
              ┌──画面──────────┐
              │                    │
              └────────────────────┘
```

- ウィンドウの `y` 座標をフレームごとに `scroll_speed` 分だけ減算
- テキストはウィンドウ内に静的に配置されているため、ウィンドウと一緒に移動する
- `has_bg=False`, `has_border=False` なのでウィンドウ枠は見えず、テキストだけが流れるように見える
- 画面外（上端より上 or 下端より下）の行は描画をスキップして効率化

### 基本的な使い方

```python
from ui.telop_window import TelopWindow

# テロップを作成
telop = TelopWindow(
    scroll_speed=1.0,   # 1px/frame のスクロール速度
    text_color=7,       # 白色
    center=True,        # 中央揃え
)

# テロップを開始
telop.show([
    "遥かなる時の彼方──",
    "",
    "世界は光と闇の狭間で",
    "均衡を保っていた。",
])
```

### コンストラクタのパラメータ

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `x` | int | 0 | テキスト表示のx座標 |
| `width` | int | 0 | 幅（0で画面幅=480） |
| `text_color` | int | 7 | テキストの色 |
| `scroll_speed` | float | 1.0 | スクロール速度（px/frame） |
| `line_height` | int | 24 | 行の高さ（px） |
| `center` | bool | True | テキストを中央揃えにするか |

### スクロール速度の目安

Pyxelのデフォルトフレームレートは30fpsとして:

| scroll_speed | 実速度 | 20行の所要時間 | 用途 |
|---|---|---|---|
| 0.5 | 15px/秒 | 約50秒 | ゆっくり読ませるストーリー |
| 1.0 | 30px/秒 | 約25秒 | 標準的なスタッフロール |
| 2.0 | 60px/秒 | 約13秒 | 早送り / 短いテロップ |

※ 所要時間 = (行数 × 行高さ + 画面高さ) / 実速度

### 公開メソッド

```python
telop.show(lines)     # テロップ開始（画面下端から）
telop.pause()         # 一時停止
telop.resume()        # 再開
telop.skip()          # スキップして即完了
```

### プロパティ

```python
telop.is_complete     # スクロール完了したか
telop.is_paused       # 一時停止中か
telop.is_open         # 表示中か（BaseWindow継承）
```

### シーンへの組み込み方

```python
class MyScene(Scene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self._telop = None

    def start_telop(self):
        self._telop = TelopWindow(scroll_speed=0.8)
        self._telop.show([
            "第一章「旅立ちの朝」",
            "",
            "ある朝、少年は目を覚ました。",
            ...
        ])

    def update(self):
        if self._telop and self._telop.is_open:
            # スキップ操作
            if pyxel.btnp(pyxel.KEY_RETURN):
                self._telop.skip()
                return
            self._telop.update()
            if self._telop.is_complete:
                # テロップ完了後の処理
                self._telop = None
            return

        # 通常のシーン更新...

    def draw(self):
        pyxel.cls(0)
        if self._telop:
            self._telop.draw()
            return
        # 通常のシーン描画...
```

**ポイント:**
- テロップ中は他のUI更新をスキップする
- `draw()` でもテロップ中は全画面をテロップに使う（`pyxel.cls(0)` で黒背景）
- Enter/Spaceでのスキップはシーン側で `skip()` を呼ぶ

---

## サブピクセルスクロール

`scroll_speed` は `float` 型で、1フレームあたり1px未満の速度も指定可能。

```python
self._scroll_y -= self.scroll_speed   # float で計算
self.y = int(self._scroll_y)          # 描画時に int に変換
```

`_scroll_y` を `float` で保持し、描画用の `self.y` は `int` にキャストする。
これにより `scroll_speed=0.5` のような低速度でも、2フレームに1pxずつ滑らかに移動する。

---

## テキストの中央揃え

`center=True`（デフォルト）のとき、各行のテキスト幅を `font.text_width()` で計測し、ウィンドウ幅内で中央に配置する。

```python
if self._center:
    text_w = font.text_width(line)
    text_x = self.x + (self.width - text_w) // 2
```

日本語と英語が混在する行でも、実際の描画幅に基づいて正確に中央揃えされる。

---

## デモシーンへの統合

デモメニューに2つのテロップテストを追加:

| メニュー項目 | 内容 | scroll_speed |
|---|---|---|
| テロップ：ストーリー風 | RPGオープニング風の物語テキスト | 0.8 |
| テロップ：スタッフロール風 | 役職＋名前のクレジット形式 | 1.0 |

テロップデモ中の操作:

| キー | 動作 |
|------|------|
| Enter / Space | スキップ（テロップ終了→メニューへ） |
| Backspace | メニューに戻る |
| Q | タイトルに戻る |

テロップデモ中は `DEMO SCENE` ヘッダーや他のUIウィンドウを描画せず、黒背景にテロップのみを表示する。

---

## ファイル構成（変更後）

```
src/
├── config.py
├── app.py
├── main.py
├── test_harness.py            ← 変更: テロップ撮影追加
├── core/
│   └── scene_manager.py
├── scenes/
│   ├── base.py
│   ├── title.py
│   └── game.py                ← 変更: テロップデモ追加
└── ui/
    ├── window.py               ← 変更: has_bg フラグ追加
    ├── menu.py
    ├── message_window.py
    ├── select_window.py
    └── telop_window.py         ← 新規: テロップウィンドウ
```

---

## 注意点・ハマりどころ

### ウィンドウ移動方式 vs テキスト移動方式

テキスト（文字列）を個別に移動させる方式だと、行ごとの座標計算が複雑になる。
ウィンドウごと移動させる方式は、テキストはウィンドウ内に静的に配置するだけでよく実装がシンプル。
Pyxelは画面外への描画を自動的にクリップするため、画面外に出たテキストの処理は不要。
ただし描画効率のため、明らかに画面外の行はスキップしている。

### 画面外描画のスキップ

テロップの全行数が多い場合（スタッフロール等）、画面に見えない行まで `pyxel.text()` を呼ぶのは無駄。
各行の y 座標を計算し、画面範囲外なら描画をスキップする。

```python
if line_y + self._line_height < 0:    # 画面上端より上
    continue
if line_y > self._visible_height:      # 画面下端より下
    continue
```

### テロップ中の画面構成

テロップは全画面を使う演出のため、デモシーンの `draw()` ではテロップ中に限り
他のUIヘッダーやウィンドウを描画しないようにしている。

```python
# テロップデモ中は全画面テロップのみ描画
if self._state == STATE_TELOP_DEMO:
    if self._telop:
        self._telop.draw()
    pyxel.text(...)  # 操作ヒントのみ
    return            # 他のUI描画をスキップ
```
