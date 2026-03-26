# Pyxel チュートリアル: ゲームの土台を作る

## 目標

起動 → タイトル画面 → メニュー選択（ゲーム開始 / オプション / 終了）という基本的なゲームフローを構築する。
シーン遷移の仕組み、オプションウィンドウのようなオーバーレイUI、そして再利用可能なモジュール分割を学ぶ。

---

## 1. ディレクトリ構造

まず、以下の構造を目指す。

```
src/
  main.py           # エントリーポイント（Appクラスの起動のみ）
  app.py            # Appクラス本体（pyxel.init, run, update, drawの管理）
  scenes/
    __init__.py
    base.py          # 全シーンの基底クラス（Scene）
    title.py         # タイトルシーン
    game.py          # ゲームシーン（仮）
  ui/
    __init__.py
    menu.py          # 汎用メニューUI（カーソル選択）
    window.py        # 汎用オーバーレイウィンドウ（オプション等）
  core/
    __init__.py
    scene_manager.py # シーンの切り替えを管理
    input.py         # 入力ヘルパー（必要に応じて後から追加）
assets/
```

**設計意図:**
- `scenes/` にシーンごとのファイルを置く。シーンが増えてもファイルを追加するだけで済む。
- `ui/` に画面部品を置く。メニューやウィンドウは複数のシーンから使い回せる。
- `core/` にゲーム全体を制御する仕組みを置く。シーン管理はどのシーンにも属さない中立的な処理。
- `main.py` はエントリーポイントとして最小限にする。実際のアプリ制御は `app.py` に書く。

---

## 2. シーン管理の考え方

### 2-1. シーンとは

「シーン」とはゲームのある画面状態のこと。タイトル画面、ゲーム画面、リザルト画面などがそれぞれ1つのシーンになる。
各シーンは共通のインターフェース（`update` と `draw`）を持ち、シーンマネージャーが「今どのシーンをアクティブにするか」を制御する。

### 2-2. SceneManager の役割

SceneManager はアクティブなシーンを1つ保持し、`update()` と `draw()` を呼び出す中継役。
シーンを切り替えたいときは、SceneManager に「次のシーンはこれ」と伝えるだけでよい。

動作イメージ:
1. `App` が `SceneManager` を持つ
2. `App.update()` → `SceneManager.update()` → アクティブシーンの `update()`
3. `App.draw()` → `SceneManager.draw()` → アクティブシーンの `draw()`
4. シーン内から `scene_manager.change_scene("game")` のように呼ぶと次フレームからシーンが切り替わる

### 2-3. 基底クラス Scene

全シーンに共通する構造を `scenes/base.py` に定義する。

- `scene_manager` への参照を持つことで、シーン内から `self.scene_manager.change_scene(...)` でシーン遷移ができる。
- `update` と `draw` は空実装にしておき、子クラスで上書きする。

```python
# src/scenes/base.py

class Scene:
    """全シーンの基底クラス。
    各シーンはこのクラスを継承し、update() と draw() をオーバーライドする。
    """

    def __init__(self, scene_manager):
        # シーンマネージャーへの参照を保持する。
        # シーン内から self.scene_manager.change_scene("name") で遷移できる。
        self.scene_manager = scene_manager

    def update(self):
        """毎フレーム呼ばれる。入力処理・ゲームロジックを書く。"""
        pass

    def draw(self):
        """毎フレーム呼ばれる。描画処理を書く。"""
        pass
```

### 2-4. SceneManager の実装方針

`core/scene_manager.py` に以下のような仕組みを作る。

- **シーン登録**: 辞書（dict）でシーン名とシーンクラスの対応を管理する。例: `{"title": TitleScene, "game": GameScene}`
- **シーン切り替え**: `change_scene(name)` を呼ぶと、辞書からクラスを取得してインスタンスを作り、アクティブシーンを差し替える。
- **初期シーン**: 起動時に `change_scene("title")` を呼んでタイトルから始める。

ポイントとして、シーンを切り替えるたびに新しいインスタンスを生成する設計にする。こうすると、シーンに入るたびに状態がリセットされるのでシンプルに保てる。もし状態を保持したい場合は後から辞書にインスタンスをキャッシュする方式に変更すればよい。

```python
# src/core/scene_manager.py

class SceneManager:
    """シーンの登録・切り替え・実行を管理するクラス。"""

    def __init__(self):
        # シーン名 → シーンクラス の対応辞書
        self._scenes = {}
        # 現在アクティブなシーンのインスタンス
        self._current_scene = None

    def register(self, name, scene_class):
        """シーンを名前付きで登録する。

        Args:
            name: シーンを識別する文字列キー（例: "title", "game"）
            scene_class: Scene を継承したクラス（インスタンスではなくクラスそのもの）
        """
        self._scenes[name] = scene_class

    def change_scene(self, name):
        """アクティブシーンを切り替える。

        登録済みのクラスから新しいインスタンスを生成して差し替える。
        毎回新規生成するので、シーンに入るたびに状態がリセットされる。

        Args:
            name: 切り替え先のシーン名
        """
        if name not in self._scenes:
            raise KeyError(f"Scene '{name}' is not registered.")
        scene_class = self._scenes[name]
        self._current_scene = scene_class(self)

    def update(self):
        """アクティブシーンの update() を呼ぶ。"""
        if self._current_scene:
            self._current_scene.update()

    def draw(self):
        """アクティブシーンの draw() を呼ぶ。"""
        if self._current_scene:
            self._current_scene.draw()
```

---

## 3. タイトルシーンの構成

### 3-1. 画面レイアウト

タイトルシーンは以下の要素で構成する:
- ゲームタイトルのテキスト表示（画面上部）
- メニュー（画面中央〜下部）
  - 「START」 → ゲームシーンへ遷移
  - 「OPTION」 → オプションウィンドウを表示（シーン遷移しない）
  - 「QUIT」 → ゲーム終了

### 3-2. メニューの仕組み（ui/menu.py）

メニューは汎用的に作る。タイトル以外の場面でも使い回せるようにするため、以下の情報を外から渡す設計にする:

- **表示位置**: x, y座標
- **選択肢のリスト**: 文字列のリスト（例: `["START", "OPTION", "QUIT"]`）
- **カーソルの現在位置**: 何番目の項目が選択中か（整数のインデックス）

メニューが担当するのは以下:
- 上下キー入力でカーソルを移動する（`update` 内）
- 選択肢とカーソルを描画する（`draw` 内）
- 決定キー（Enter や Zキーなど）が押されたとき、選択中のインデックスを返す

**カーソル表示の方法:**
選択中の項目の左隣に `>` 記号を表示する。Pyxelの `pyxel.text()` でテキストを描画するので、カーソル記号とメニュー項目テキストのx座標をずらして配置する。

**入力の処理:**
- `pyxel.btnp(pyxel.KEY_UP)` → カーソルを1つ上へ（0未満にならないようクランプ、またはループさせる）
- `pyxel.btnp(pyxel.KEY_DOWN)` → カーソルを1つ下へ
- `pyxel.btnp(pyxel.KEY_RETURN)` や `pyxel.btnp(pyxel.KEY_Z)` → 決定

**決定の通知方法:**
`update()` の戻り値として「決定されたインデックス」または「まだ未決定なら `None`」を返す設計が簡単。タイトルシーンの `update` 内でこの戻り値を見て処理を分岐する。

```python
# src/ui/menu.py
import pyxel


class Menu:
    """汎用カーソル選択メニュー。
    任意の場面で使い回せるように、表示位置・選択肢・色を外から渡す。
    """

    # メニュー項目1行あたりの高さ（ピクセル）。
    # pyxel.text() のフォント高さ(5px) + 余白 で 10px が使いやすい。
    LINE_HEIGHT = 10

    def __init__(self, x, y, items, text_color=7, cursor_color=7):
        """
        Args:
            x: メニュー描画の基準x座標
            y: メニュー描画の基準y座標
            items: 選択肢の文字列リスト（例: ["START", "OPTION", "QUIT"]）
            text_color: テキストの色番号（デフォルト: 7=白）
            cursor_color: カーソル記号の色番号
        """
        self.x = x
        self.y = y
        self.items = items
        self.text_color = text_color
        self.cursor_color = cursor_color
        # 現在カーソルが指している項目のインデックス
        self.cursor = 0

    def update(self):
        """入力を処理し、決定されたインデックスまたは None を返す。

        Returns:
            int: 決定キーが押された場合、選択中のインデックス
            None: まだ決定されていない場合
        """
        # カーソル移動（上端/下端でループする）
        if pyxel.btnp(pyxel.KEY_UP):
            self.cursor = (self.cursor - 1) % len(self.items)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.cursor = (self.cursor + 1) % len(self.items)

        # 決定キー（Enterキー または Zキー）
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
            return self.cursor

        return None

    def draw(self):
        """選択肢一覧とカーソルを描画する。"""
        for i, item in enumerate(self.items):
            item_y = self.y + i * self.LINE_HEIGHT

            # 選択中の項目の左に ">" カーソルを表示
            if i == self.cursor:
                pyxel.text(self.x, item_y, ">", self.cursor_color)

            # 項目テキスト（カーソル分の幅 8px を右にずらす）
            pyxel.text(self.x + 8, item_y, item, self.text_color)
```

タイトルシーン側でメニューの戻り値を使って分岐するイメージ:

```python
# タイトルシーンの update 内
selected = self.menu.update()
if selected == 0:  # START
    self.scene_manager.change_scene("game")
elif selected == 1:  # OPTION
    self.option_window.open()
elif selected == 2:  # QUIT
    pyxel.quit()
```

---

## 4. オーバーレイウィンドウ（ui/window.py）

### 4-1. オーバーレイとは

オプション画面のように「シーン遷移せず、今の画面の上に重ねて表示するUI」をオーバーレイウィンドウと呼ぶ。
シーンを切り替えないので、閉じればそのまま元の画面に戻れる。

### 4-2. 基本設計

ウィンドウは以下の状態を持つ:
- **is_open**: 開いているか閉じているか（True/False）
- **位置・サイズ**: x, y, width, height

タイトルシーンでの制御の流れ:
1. ウィンドウが閉じている間は通常通りメニューの `update` / `draw` を処理する
2. メニューで「OPTION」が選ばれたら `window.open()` を呼ぶ
3. ウィンドウが開いている間はメニューの入力を無効にし、ウィンドウの `update` / `draw` を処理する
4. ウィンドウ内でEscキーなど閉じる操作をしたら `window.close()` を呼び、メニュー操作に戻る

**重要な点:** `draw` の順序に注意。先にシーン背景やメニューを描画し、最後にウィンドウを描画すると、ウィンドウがメニューの上に重なって見える。

### 4-3. 描画内容

- `pyxel.rect()` でウィンドウ背景の矩形を描画（暗い色）
- `pyxel.rectb()` でウィンドウの枠線を描画（明るい色）
- `pyxel.text()` でウィンドウ内のテキストやオプション項目を表示

オプション画面に何を置くかは後から自由に追加できるが、最初は「CLOSE」の1項目だけでもよい。まずは「開く→閉じる」が正常に動くことを確認するのが大事。

```python
# src/ui/window.py
import pyxel


class Window:
    """汎用オーバーレイウィンドウ。
    画面上に矩形のウィンドウを重ねて表示する。
    シーン遷移せずに情報表示や設定変更UIを出したいときに使う。
    """

    def __init__(self, x, y, width, height,
                 bg_color=1, border_color=7, text_color=7,
                 close_key=pyxel.KEY_ESCAPE):
        """
        Args:
            x: ウィンドウ左上のx座標
            y: ウィンドウ左上のy座標
            width: ウィンドウの幅
            height: ウィンドウの高さ
            bg_color: 背景色（デフォルト: 1=暗い青）
            border_color: 枠線の色（デフォルト: 7=白）
            text_color: テキスト色（デフォルト: 7=白）
            close_key: 閉じるキー（デフォルト: Escキー）
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.close_key = close_key

        # ウィンドウの開閉状態
        self.is_open = False

        # ウィンドウ内に表示するテキスト行のリスト
        self._lines = []

    def open(self, lines=None):
        """ウィンドウを開く。

        Args:
            lines: ウィンドウ内に表示するテキストのリスト（省略時は前回の内容を維持）
        """
        self.is_open = True
        if lines is not None:
            self._lines = lines

    def close(self):
        """ウィンドウを閉じる。"""
        self.is_open = False

    def update(self):
        """ウィンドウが開いている間の入力処理。

        Returns:
            True: ウィンドウが閉じられた（呼び出し元でメニュー操作を再開してよい）
            False: ウィンドウはまだ開いている
        """
        if not self.is_open:
            return False

        if pyxel.btnp(self.close_key):
            self.close()
            return True

        return False

    def draw(self):
        """ウィンドウを描画する。is_open が False なら何もしない。"""
        if not self.is_open:
            return

        # 背景の矩形
        pyxel.rect(self.x, self.y, self.width, self.height, self.bg_color)
        # 枠線
        pyxel.rectb(self.x, self.y, self.width, self.height, self.border_color)

        # テキスト描画（ウィンドウ内側に余白4pxを取る）
        text_x = self.x + 4
        text_y = self.y + 4
        for i, line in enumerate(self._lines):
            pyxel.text(text_x, text_y + i * 10, line, self.text_color)

        # 閉じ方のヒント（ウィンドウ下部）
        hint = "ESC:CLOSE"
        hint_y = self.y + self.height - 10
        pyxel.text(text_x, hint_y, hint, self.text_color)
```

---

## 5. App クラスと main.py

### 5-1. app.py の役割

`app.py` に `App` クラスを作り、以下を担当させる:

1. `pyxel.init()` の呼び出し（画面サイズ、タイトルなどの初期設定）
2. `SceneManager` の生成とシーンの登録
3. 初期シーン（タイトル）の設定
4. `pyxel.run(self.update, self.draw)` の呼び出し
5. `update` メソッド: `scene_manager.update()` を呼ぶ
6. `draw` メソッド: `scene_manager.draw()` を呼ぶ

```python
# src/app.py
import pyxel

from core.scene_manager import SceneManager
from scenes.title import TitleScene
from scenes.game import GameScene


class App:
    """ゲームアプリケーション本体。
    Pyxelの初期化・ゲームループの起動・シーン管理を統括する。
    """

    # 画面サイズ（必要に応じて調整）
    SCREEN_WIDTH = 256
    SCREEN_HEIGHT = 256

    def __init__(self):
        pyxel.init(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, title="My Game")

        # シーンマネージャーの初期化
        self.scene_manager = SceneManager()

        # 使用するシーンを全て登録する
        self.scene_manager.register("title", TitleScene)
        self.scene_manager.register("game", GameScene)
        # 新しいシーンが増えたらここに register を追加する

        # 最初に表示するシーンを指定
        self.scene_manager.change_scene("title")

        # ゲームループ開始（ここでブロッキング。以降は毎フレーム update/draw が呼ばれる）
        pyxel.run(self.update, self.draw)

    def update(self):
        """毎フレームの更新処理。アクティブシーンに委譲する。"""
        self.scene_manager.update()

    def draw(self):
        """毎フレームの描画処理。アクティブシーンに委譲する。"""
        self.scene_manager.draw()
```

### 5-2. main.py の役割

`main.py` はエントリーポイントとして最小限にする。
`App()` のコンストラクタ内で `pyxel.run()` が呼ばれるので、インスタンス化するだけでゲームが起動する。

```python
# src/main.py
from app import App

App()
```

---

## 6. シーンの実装例

ベースクラスとUIクラスを組み合わせてシーンを作る具体例を示す。

### 6-1. TitleScene（タイトルシーン）

```python
# src/scenes/title.py
import pyxel

from scenes.base import Scene
from ui.menu import Menu
from ui.window import Window


class TitleScene(Scene):
    """タイトル画面。メニュー選択とオプションウィンドウを持つ。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)

        # メニュー（画面中央付近に配置）
        self.menu = Menu(
            x=100, y=120,
            items=["START", "OPTION", "QUIT"]
        )

        # オプションウィンドウ（画面中央にオーバーレイ）
        self.option_window = Window(
            x=48, y=48, width=160, height=160
        )

    def update(self):
        # ウィンドウが開いている間はウィンドウの入力のみ処理する
        if self.option_window.is_open:
            self.option_window.update()
            return

        # メニューの入力処理
        selected = self.menu.update()
        if selected is None:
            return

        if selected == 0:  # START
            self.scene_manager.change_scene("game")
        elif selected == 1:  # OPTION
            self.option_window.open(lines=["- OPTION MENU -", "", "No settings yet."])
        elif selected == 2:  # QUIT
            pyxel.quit()

    def draw(self):
        pyxel.cls(0)

        # タイトルテキスト
        pyxel.text(90, 40, "MY GAME", 7)

        # メニュー（ウィンドウが開いていても背景として描画する）
        self.menu.draw()

        # オーバーレイウィンドウ（開いていれば最前面に描画）
        self.option_window.draw()
```

### 6-2. GameScene（ゲームシーン・仮実装）

```python
# src/scenes/game.py
import pyxel

from scenes.base import Scene


class GameScene(Scene):
    """ゲーム画面の仮実装。Escでタイトルに戻る。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.scene_manager.change_scene("title")

    def draw(self):
        pyxel.cls(0)
        pyxel.text(100, 120, "GAME SCENE", 7)
        pyxel.text(80, 140, "Press ESC to return", 5)
```

---

## 7. 全体の処理フロー

起動から実際の動きを時系列で整理する:

```
1. main.py 実行
2. App.__init__() が呼ばれる
3.   pyxel.init() で画面初期化
4.   SceneManager を生成、シーン辞書を登録
5.   change_scene("title") でタイトルシーンを生成・アクティブ化
6.   pyxel.run(update, draw) でゲームループ開始
7. 毎フレーム:
8.   App.update() → SceneManager.update() → TitleScene.update()
9.     - ウィンドウが開いていなければ Menu.update() を処理
10.      - 上下キーでカーソル移動
11.      - 決定キーで選択結果を返す
12.    - 選択結果に応じて:
13.      - START → scene_manager.change_scene("game")
14.      - OPTION → window.open()
15.      - QUIT → pyxel.quit()
16.    - ウィンドウが開いていれば Window.update() を処理
17.      - Escキーで window.close()
18.  App.draw() → SceneManager.draw() → TitleScene.draw()
19.    - 画面クリア
20.    - タイトルテキスト描画
21.    - メニュー描画
22.    - ウィンドウが開いていればウィンドウ描画（最前面）
```

---

## 8. 実装の進め方（推奨順序）

一度に全部作ろうとせず、以下の順序で少しずつ動かしながら進める。

### Step 1: 最小構成で動かす
- `app.py` に `App` クラスを作る
- `core/scene_manager.py` に `SceneManager` を作る
- `scenes/base.py` に `Scene` 基底クラスを作る
- `scenes/title.py` に `TitleScene` を作る（画面に "TITLE" とだけ表示）
- `main.py` から `App()` を呼ぶ
- **確認:** 起動して「TITLE」の文字が表示されればOK

### Step 2: メニューを追加する
- `ui/menu.py` に `Menu` クラスを作る
- `TitleScene` にメニューを組み込む
- **確認:** 上下キーでカーソルが動き、決定で選択インデックスが取れればOK（printデバッグで確認）

### Step 3: シーン遷移を実装する
- `scenes/game.py` に `GameScene` を作る（"GAME" と表示するだけの仮実装）
- メニューの「START」でゲームシーンへ遷移する
- メニューの「QUIT」で `pyxel.quit()` を呼ぶ
- **確認:** STARTでゲーム画面に切り替わり、QUITで終了すればOK

### Step 4: オーバーレイウィンドウを実装する
- `ui/window.py` に `Window` クラスを作る
- `TitleScene` にウィンドウを組み込む
- メニューの「OPTION」でウィンドウが開き、Escで閉じる
- ウィンドウ表示中はメニュー操作を無効にする
- **確認:** OPTION→ウィンドウ表示→Esc→メニューに戻る、の流れが動けばOK

### Step 5: ゲームシーンからタイトルに戻る
- ゲームシーン内でEscキーを押すとタイトルに戻る処理を追加する
- **確認:** タイトル→ゲーム→タイトルの往復ができればOK

---

## 9. 設計上の注意点

### pyxel.text() の日本語対応について
Pyxelのデフォルトフォントは英数字のみ対応。日本語を使いたい場合はカスタムフォントの設定が必要になるが、まずは英語テキストで進め、後から対応する方が進捗が早い。

### update と draw の分離
Rule.md にも記載の通り、`update` にはゲームロジックと入力処理のみ、`draw` には描画処理のみを書く。メニューやウィンドウのクラスも同様に `update` と `draw` を分けて持たせること。

### 画面サイズの選択
現在は `160x120` だが、メニューやウィンドウを配置するなら `256x256` 程度にしておくと余裕がある。ここは好みで決めてよい。

### シーン間のデータ受け渡し
今の段階では不要だが、将来的にスコアや設定値をシーン間で共有したくなったら、`App` クラスや `SceneManager` に共有データ用の辞書を持たせて、各シーンからアクセスできるようにするとよい。
