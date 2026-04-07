# 013 イベントシステム設計書

## 1. 概要

シーン（オープニング、会話パートなど）を **イベントコマンドのリスト** として定義し、
データ駆動で実行する仕組みを構築する。

RPGツクールのイベントシステムと同様に、1行ずつコマンドを並べてシーンを組み上げる方式を採る。

### 目標

- シーンの流れを Python コードではなく **JSONデータ** で記述できる
- GUIエディタでイベントコマンドを **視覚的に編集** できる
- 「イベント実行中」という状態を明確に管理し、通常のゲーム操作と分離する

---

## 2. 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│  data/text/*.json                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │
│  │ messages  │ │ selections│ │ telops            │  │
│  └───────────┘ └───────────┘ └───────────────────┘  │
│  ┌─────────────────────────────────────────────────┐ │
│  │ events（新規追加）                                │ │
│  │  "ev_opening": [ {cmd: ...}, {cmd: ...}, ... ]  │ │
│  └─────────────────────────────────────────────────┘ │
└─────────┬───────────────────────────────────────────┘
          │ compiler.py (コンパイル)
          ▼
┌─────────────────────┐
│ data/compiled/       │
│   text_all.bin       │  ← events も含めて一括コンパイル
└─────────┬───────────┘
          │ TextManager.get_event(ev_id)
          ▼
┌─────────────────────────────────────────────────────┐
│  EventInterpreter（新規クラス）                       │
│  ┌─────────────┐                                    │
│  │ コマンド列   │  → 1コマンドずつ順番に実行           │
│  │ 実行位置     │  → ウェイト・完了管理                │
│  │ 状態管理     │  → 表示中オブジェクト（画像・音声）    │
│  └─────────────┘                                    │
│     ↓ 利用                                          │
│  Image / Sprite / Audio / MessageWindow / TelopWindow│
│  SelectWindow                                        │
└─────────────────────────────────────────────────────┘
```

---

## 3. 「イベント実行中」の状態管理

### 3.1 ゲームの状態遷移

```
┌──────────────┐    イベント開始    ┌──────────────┐
│   通常状態    │ ───────────────→ │ イベント実行中 │
│ (自由操作)    │ ←─────────────── │ (操作制限)     │
└──────────────┘    イベント終了    └──────────────┘
```

- **通常状態**: プレイヤーがキャラクターを操作できる（将来の探索パートなど）
- **イベント実行中**: EventInterpreter がコマンドを逐次実行。プレイヤーの自由操作は無効化される。メッセージ送り・選択肢選択などイベントが要求する入力のみ受け付ける。

### 3.2 Scene クラスとの関係

```python
class GameScene(Scene):
    """ゲーム本編シーン。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self._event = EventInterpreter(scene_manager)
        # シーン開始時にイベントを実行する場合
        event_data = config.TEXT_MANAGER.get_event("ev_opening")
        self._event.start(event_data)

    def update(self):
        if self._event.is_running:
            # イベント実行中 → EventInterpreter に制御を委譲
            self._event.update()
        else:
            # 通常状態 → プレイヤー操作など
            self._update_normal()

    def draw(self):
        # 背景やマップの描画（通常）
        self._draw_map()
        # イベントが管理するオブジェクトの描画（画像、ウィンドウ等）
        self._event.draw()
```

**ポイント**:
- `Scene` はゲームの「場面」（タイトル、フィールド、戦闘など）を管理する既存の単位
- `EventInterpreter` は Scene の **中で動く** 仕組み。Scene を置き換えるのではなく、Scene 内のイベント進行を担当する
- 1つの Scene 内で複数のイベントを順次実行できる（話しかけるたびに別のイベントを開始、など）

### 3.3 オープニング専用シーンの場合

オープニングのように「シーン全体がイベント」の場合は、シンプルにイベント完了後にシーン遷移する:

```python
class OpeningScene(Scene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self._event = EventInterpreter(scene_manager)
        self._event.start(config.TEXT_MANAGER.get_event("ev_opening"))

    def update(self):
        self._event.update()
        if not self._event.is_running:
            self.scene_manager.change_scene("title")

    def draw(self):
        pyxel.cls(0)
        self._event.draw()
```

---

## 4. イベントコマンド仕様

### 4.1 基本構造

各コマンドは以下の形式の dict:

```json
{
  "cmd": "コマンド名",
  "パラメータ1": 値,
  "パラメータ2": 値
}
```

### 4.2 コマンド一覧

#### グラフィック系

| コマンド | 説明 | ウェイト |
|---|---|---|
| `show_picture` | 画像を表示（番号指定スロット） | なし |
| `move_picture` | 画像の位置・透明度をアニメーション | **あり** |
| `erase_picture` | 画像を消去 | なし |

#### 画面効果系

| コマンド | 説明 | ウェイト |
|---|---|---|
| `fadeout` | 画面フェードアウト | **あり** |
| `fadein` | 画面フェードイン | **あり** |
| `wait` | 指定フレーム数待機 | **あり** |

#### 音声系

| コマンド | 説明 | ウェイト |
|---|---|---|
| `play_bgm` | BGM再生 | なし |
| `stop_bgm` | BGM停止 | なし |
| `play_se` | SE再生 | なし |
| `play_me` | ME再生 | なし |

#### テキスト系

| コマンド | 説明 | ウェイト |
|---|---|---|
| `message` | メッセージウィンドウ表示 | **あり**（全ページ送り完了まで） |
| `selection` | 選択肢ウィンドウ表示 | **あり**（選択完了まで） |
| `telop` | テロップ表示 | **あり**（スクロール完了まで） |

#### フロー制御系

| コマンド | 説明 | ウェイト |
|---|---|---|
| `label` | ジャンプ先ラベル定義 | なし |
| `jump` | 指定ラベルへジャンプ | なし |
| `end` | イベント終了 | - |

#### 特殊

| コマンド | 説明 | ウェイト |
|---|---|---|
| `change_scene` | シーン遷移（イベント強制終了） | - |

### 4.3 各コマンドの詳細

---

#### `show_picture` — 画像表示

RPGツクールの「ピクチャの表示」と同じ概念。番号付きスロットで画像を管理する。

```json
{
  "cmd": "show_picture",
  "no": 1,
  "file": "background/sample_opening.png",
  "x": 0,
  "y": 0,
  "opacity": 100
}
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `no` | int | yes | - | ピクチャ番号（1〜20）。番号が大きいほど手前に描画 |
| `file` | str | yes | - | `assets/images/` からの相対パス |
| `x` | int | no | 0 | 表示X座標 |
| `y` | int | no | 0 | 表示Y座標 |
| `opacity` | int | no | 100 | 不透明度（0〜100） |
| `colkey` | int/null | no | null | 透過色（null=透過なし） |

**設計意図**:
- `Image` と `Sprite` を統一して「ピクチャ」として扱う。RPGツクールと同じく番号で管理する
- 背景もスプライトも同じ `show_picture` で表示する。背景は no=1（奥）、キャラは no=5（手前）のように番号で前後関係を制御
- 「背景用コマンド」「スプライト用コマンド」を分けない（シンプルさ優先）

---

#### `move_picture` — 画像の移動・変化

表示済みピクチャの位置・不透明度をアニメーション付きで変更する。**ウェイトあり**（アニメーション完了まで次に進まない）。

```json
{
  "cmd": "move_picture",
  "no": 1,
  "x": 100,
  "y": 50,
  "opacity": 0,
  "duration": 60
}
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `no` | int | yes | - | 対象ピクチャ番号 |
| `x` | int | no | (現在値) | 移動先X座標 |
| `y` | int | no | (現在値) | 移動先Y座標 |
| `opacity` | int | no | (現在値) | 変更後の不透明度 |
| `duration` | int | yes | - | アニメーション時間（フレーム数） |

**使用例**: フェードイン表示
```json
{"cmd": "show_picture", "no": 1, "file": "background/sample_opening.png", "opacity": 0},
{"cmd": "move_picture", "no": 1, "opacity": 100, "duration": 60}
```

**使用例**: スプライトを歩かせる
```json
{"cmd": "move_picture", "no": 5, "x": 200, "y": 100, "duration": 90}
```

---

#### `erase_picture` — 画像消去

```json
{
  "cmd": "erase_picture",
  "no": 1
}
```

---

#### `fadeout` / `fadein` — 画面フェード

画面全体のフェードアウト/フェードイン。**ウェイトあり**。

```json
{"cmd": "fadeout", "duration": 60, "color": 0}
{"cmd": "fadein", "duration": 60}
```

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `duration` | int | no | 30 | フレーム数 |
| `color` | int | no | 0 | フェード色（Pyxelパレット番号。0=黒, 7=白） |

**`move_picture` の opacity との違い**:
- `fadeout` / `fadein` は画面全体に影響する（全ピクチャ・UIの上に覆いかぶさる）
- `move_picture` の `opacity` は個別ピクチャの透明度

---

#### `wait` — ウェイト

```json
{"cmd": "wait", "duration": 60}
```

---

#### `play_bgm` / `stop_bgm` / `play_se` / `play_me` — 音声

```json
{"cmd": "play_bgm", "file": "RPG1_01.ogg"}
{"cmd": "stop_bgm"}
{"cmd": "play_se", "file": "cursor.wav"}
{"cmd": "play_me", "file": "fanfare.ogg"}
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `file` | str | yes（stop_bgm以外） | `assets/audio/bgm/` or `assets/audio/se/` からのファイル名 |

---

#### `message` — メッセージ表示

既存の TextManager のメッセージIDを参照して表示する。**ウェイトあり**（全ページ送り完了まで）。

```json
{"cmd": "message", "id": "msg_opening_01"}
```

**動作**:
1. `TextManager.get_messages("msg_opening_01")` でメッセージデータを取得
2. `MessageWindow.show(messages)` で表示開始
3. 全メッセージが送られて `MessageWindow.is_busy == False` になるまでウェイト

**インライン定義**（IDを使わず直接記述する場合）:
```json
{
  "cmd": "message",
  "text": "ここはどこだ？",
  "name": "主人公"
}
```

`id` がある場合は TextManager を参照、`text` がある場合はインラインとして扱う。
ただし **GUIエディタではID参照を推奨**（テキストの一元管理のため）。

---

#### `selection` — 選択肢表示

```json
{
  "cmd": "selection",
  "id": "select_yesno",
  "branches": {
    "0": "label_yes",
    "1": "label_no"
  }
}
```

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | str | yes | TextManager の選択肢ID |
| `branches` | dict | no | 選択結果 → ジャンプ先ラベルの対応。省略時はジャンプせず次のコマンドへ |

**動作**:
1. `TextManager.get_selection("select_yesno")` で選択肢データを取得
2. `SelectWindow` で表示
3. ユーザーが選択するまでウェイト
4. `branches` が定義されていれば、選択インデックスに対応するラベルへジャンプ

---

#### `telop` — テロップ表示

```json
{"cmd": "telop", "id": "telop_story"}
```

**動作**:
1. `TextManager.get_telop("telop_story")` でデータ取得
2. `TelopWindow.show(lines)` で表示
3. スクロール完了（`is_complete == True`）までウェイト

---

#### `label` / `jump` — フロー制御

```json
{"cmd": "label", "name": "label_yes"},
{"cmd": "message", "id": "msg_yes_response"},
{"cmd": "jump", "to": "label_end"},

{"cmd": "label", "name": "label_no"},
{"cmd": "message", "id": "msg_no_response"},

{"cmd": "label", "name": "label_end"}
```

**label**: 何もしない。ジャンプ先の目印として機能する
**jump**: 指定ラベルの位置までコマンド実行位置を移動する

---

#### `end` — イベント終了

```json
{"cmd": "end"}
```

コマンド列の最後に達した場合も暗黙的に終了するが、`selection` の分岐内で途中終了したい場合などに使う。

---

#### `change_scene` — シーン遷移

```json
{"cmd": "change_scene", "scene": "title"}
```

イベントを強制終了し、SceneManager 経由でシーンを切り替える。

---

## 5. JSONデータ形式

### 5.1 既存構造への統合

`data/text/*.json` に `"events"` カテゴリを追加する:

```json
{
  "version": 1,
  "file_id": "demo",
  "messages": { ... },
  "selections": { ... },
  "telops": { ... },
  "events": {
    "ev_opening": [
      {"cmd": "show_picture", "no": 1, "file": "background/sample_opening.png", "opacity": 0},
      {"cmd": "move_picture", "no": 1, "opacity": 100, "duration": 60},
      {"cmd": "play_bgm", "file": "RPG1_01.ogg"},
      {"cmd": "telop", "id": "telop_story"},
      {"cmd": "fadeout", "duration": 60},
      {"cmd": "erase_picture", "no": 1},

      {"cmd": "show_picture", "no": 1, "file": "background/sample_opening.png", "opacity": 0},
      {"cmd": "show_picture", "no": 5, "file": "sprite/player.png", "x": 60, "y": 100, "opacity": 0, "colkey": 0},
      {"cmd": "fadein", "duration": 60},
      {"cmd": "move_picture", "no": 1, "opacity": 100, "duration": 60},
      {"cmd": "move_picture", "no": 5, "opacity": 100, "duration": 60},

      {"cmd": "message", "id": "msg_opening_01"},
      {"cmd": "move_picture", "no": 5, "x": 200, "y": 80, "duration": 90},
      {"cmd": "play_se", "file": "cursor.wav"},

      {"cmd": "fadeout", "duration": 60},
      {"cmd": "change_scene", "scene": "title"}
    ]
  }
}
```

### 5.2 ファイル構成

テキストデータと同じ `data/text/` ディレクトリに配置する（別ディレクトリにはしない）。

理由:
- 既存の compiler / TextManager / GUIエディタのパイプラインに乗せられる
- イベント内で `msg_id` や `telop_id` を参照するため、同じファイルにあるほうが見通しが良い
- ファイル分割は既存の仕組み（`file_id` 別ファイル）で対応可能

### 5.3 TextManager の拡張

```python
class TextManager:
    def get_event(self, event_id: str) -> list[dict]:
        """イベントコマンドリストを取得する。"""
        return self._data["events"][event_id]
```

---

## 6. EventInterpreter クラス設計

### 6.1 クラス概要

```
src/core/event_interpreter.py
```

```python
class EventInterpreter:
    """イベントコマンドを逐次実行するインタプリタ。

    RPGツクールの「イベントコマンド実行エンジン」に相当する。
    コマンドリストを受け取り、1コマンドずつ順番に実行する。
    ウェイトが必要なコマンドでは、完了まで次に進まない。
    """
```

### 6.2 主要な状態

```python
class EventInterpreter:
    def __init__(self, scene_manager):
        self._scene_manager = scene_manager

        # --- コマンド実行状態 ---
        self._commands: list[dict] = []   # コマンドリスト
        self._index: int = 0              # 現在の実行位置
        self._running: bool = False       # イベント実行中フラグ
        self._waiting: bool = False       # ウェイト中フラグ

        # --- ピクチャ管理 ---
        # 番号 → Picture オブジェクト
        self._pictures: dict[int, Picture] = {}

        # --- 画面フェード ---
        self._fade_alpha: float = 0.0     # 0.0=透明, 1.0=完全に覆う
        self._fade_color: int = 0
        self._fade_target: float = 0.0
        self._fade_speed: float = 0.0

        # --- UIウィンドウ ---
        self._msg_window: MessageWindow = MessageWindow()
        self._select_window: SelectWindow | None = None
        self._telop_window: TelopWindow | None = None

        # --- ラベルインデックス ---
        self._labels: dict[str, int] = {} # ラベル名 → コマンドindex
```

### 6.3 メインループ

```python
def update(self):
    """毎フレーム呼ばれる。"""
    if not self._running:
        return

    # ウェイト中なら完了チェック
    if self._waiting:
        self._update_wait()
        return

    # コマンドを実行（ウェイトなしコマンドは連続実行）
    while self._index < len(self._commands):
        cmd = self._commands[self._index]
        self._index += 1
        result = self._execute(cmd)

        if result == "wait":
            self._waiting = True
            return  # 次フレームで完了チェック

    # 全コマンド実行完了
    self._running = False
```

**重要な動作**:
- ウェイトなしコマンド（`play_bgm`, `show_picture` 等）は **同一フレーム内で連続実行** される
- ウェイトありコマンド（`message`, `fadeout` 等）に到達すると、そのフレームの実行を中断し、次フレーム以降で完了を待つ
- これにより「BGM再生 → ピクチャ表示 → メッセージ」のような流れで、BGM再生とピクチャ表示は同時に処理される（RPGツクールと同じ挙動）

### 6.4 ウェイト管理

```python
def _update_wait(self):
    """ウェイト中の状態を更新し、完了したらウェイト解除する。"""
    # ピクチャアニメーション更新
    for pic in self._pictures.values():
        pic.update()

    # ウェイト種別に応じた完了チェック
    if self._wait_type == "fade":
        self._update_fade()
        if self._fade_alpha == self._fade_target:
            self._waiting = False

    elif self._wait_type == "message":
        self._msg_window.update()
        if not self._msg_window.is_busy:
            self._waiting = False

    elif self._wait_type == "telop":
        self._telop_window.update()
        if self._telop_window.is_complete:
            self._waiting = False

    elif self._wait_type == "selection":
        self._select_window.update()
        # 選択完了時の処理は _execute_selection 内で設定済み
        ...

    elif self._wait_type == "move_picture":
        if self._animating_picture.is_animation_complete:
            self._waiting = False

    elif self._wait_type == "wait":
        self._wait_counter -= 1
        if self._wait_counter <= 0:
            self._waiting = False
```

### 6.5 描画

```python
def draw(self):
    """イベントが管理するオブジェクトを描画する。"""
    # ピクチャを番号順（小→大 = 奥→手前）に描画
    for no in sorted(self._pictures.keys()):
        self._pictures[no].draw()

    # テロップ
    if self._telop_window and self._telop_window.is_open:
        self._telop_window.draw()

    # メッセージ・選択肢（最前面）
    self._msg_window.draw()
    if self._select_window:
        self._select_window.draw()

    # 画面フェード（最最前面）
    if self._fade_alpha > 0:
        self._draw_fade_overlay()
```

---

## 7. Picture クラス（内部クラス）

ピクチャ番号で管理される画像オブジェクト。既存の `Image` クラスをラップする。

```python
class Picture:
    """ピクチャ番号で管理される画像。"""

    def __init__(self, no: int, image: Image, x: int, y: int,
                 opacity: int, colkey: int | None):
        self.no = no
        self.image = image
        self.x = x
        self.y = y
        self.opacity = opacity    # 0〜100
        self.colkey = colkey

        # アニメーション用
        self._anim_target_x: float | None = None
        self._anim_target_y: float | None = None
        self._anim_target_opacity: float | None = None
        self._anim_duration: int = 0
        self._anim_elapsed: int = 0

    def move_to(self, x=None, y=None, opacity=None, duration=30):
        """アニメーション開始。"""
        ...

    @property
    def is_animation_complete(self) -> bool:
        return self._anim_elapsed >= self._anim_duration

    def update(self):
        """アニメーションを1フレーム進める。"""
        ...

    def draw(self):
        """描画。"""
        self.image.set_fade(self.opacity / 100.0)
        self.image.x = self.x
        self.image.y = self.y
        self.image.draw()
```

---

## 8. オープニングデモの変換例

現在の `opening_demo.py` のハードコードを、イベントコマンドに変換した場合:

```json
{
  "ev_opening_demo": [
    {"cmd": "show_picture", "no": 1, "file": "background/sample_opening.png", "opacity": 0},
    {"cmd": "move_picture", "no": 1, "opacity": 100, "duration": 60},

    {"cmd": "play_bgm", "file": "RPG1_01.ogg"},
    {"cmd": "telop", "id": "telop_opening"},

    {"cmd": "fadeout", "duration": 60},

    {"cmd": "show_picture", "no": 1, "file": "background/sample_opening.png", "opacity": 0},
    {"cmd": "show_picture", "no": 5, "file": "sprite/player.png", "x": 60, "y": 100, "opacity": 0, "colkey": 0},
    {"cmd": "move_picture", "no": 1, "opacity": 100, "duration": 60},
    {"cmd": "move_picture", "no": 5, "opacity": 100, "duration": 60},
    {"cmd": "fadein", "duration": 60},

    {"cmd": "message", "id": "msg_opening_01"},

    {"cmd": "move_picture", "no": 5, "x": 200, "y": 80, "duration": 90},
    {"cmd": "play_se", "file": "decide.wav"},
    {"cmd": "wait", "duration": 60},

    {"cmd": "fadeout", "duration": 60},
    {"cmd": "change_scene", "scene": "title"}
  ]
}
```

これは opening_demo.py の約200行のPythonコードと同等の動作を、16行のコマンドで表現している。

---

## 9. GUIエディタへの統合

### 9.1 ツリーへの追加

既存の 3カテゴリ（Messages / Selections / Telops）に「Events」を追加:

```
demo.json
├── Messages
│   ├── msg_basic
│   └── ...
├── Selections
│   └── ...
├── Telops
│   └── ...
└── Events        ← 新規
    └── ev_opening
```

### 9.2 イベントエディタパネル

```
┌─────────────────────────────────────────────────────────┐
│ イベントコマンドリスト                                    │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ● ピクチャの表示   No.1 background/sample_opening.png│ │
│ │ ● ピクチャの移動   No.1 → opacity:100 (60F)         │ │
│ │ ● BGMの再生       RPG1_01.ogg                       │ │
│ │ ● テロップの表示   telop_opening                     │ │
│ │ ● フェードアウト   60F                               │ │
│ │ ● メッセージの表示 msg_opening_01                     │ │
│ │   ...                                               │ │
│ └──────────────────────────────────────────────────────┘ │
│ [挿入] [削除] [▲] [▼] [コピー] [貼り付け]                │
├─────────────────────────────────────────────────────────┤
│ コマンド編集（選択中のコマンドの詳細）                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ コマンド: [ピクチャの表示 ▼]                          │ │
│ │ No:      [1       ]                                 │ │
│ │ ファイル: [background/sample_opening.png] [参照...]   │ │
│ │ X:       [0    ]  Y: [0    ]                        │ │
│ │ 不透明度: [0    ]                                    │ │
│ │ 透過色:   [なし ▼]                                   │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 9.3 プレビューパネル

選択中のコマンド位置から「そこまでの画面状態」を算出してプレビュー:

- 先頭からそのコマンドまでを走査
- `show_picture` → QPixmap を読み込んで描画
- `erase_picture` → 該当ピクチャを除去
- `fadeout` → 半透明オーバーレイ（進行中なら途中の透過度）
- `message` → 既存の `_draw_message()` でメッセージプレビュー
- 音声系コマンドはプレビューに影響しない

---

## 10. 実装順序

### Phase 1: データ形式 + インタプリタ

1. JSON仕様の確定（このドキュメントの内容をレビュー後）
2. `TextManager` に `get_event()` を追加
3. `EventInterpreter` クラスの実装
4. `Picture` クラスの実装
5. `opening_demo.py` を EventInterpreter ベースに書き換えて動作確認

### Phase 2: GUIエディタ対応

6. `compiler.py` に events カテゴリのバリデーション追加
7. `gui_editor.py` にイベントエディタパネル追加
8. コマンドリストUI + 詳細編集フォーム
9. アセットブラウザ（ファイル参照ダイアログ）
10. プレビュー対応

### Phase 3: 拡充

11. 選択肢の分岐（`label` / `jump` / `selection.branches`）
12. 追加コマンドの検討（条件分岐、変数、ループなど）

---

## 11. 設計判断メモ

### Q: なぜ `show_bg` と `show_sprite` を分けず `show_picture` に統一したのか？

A: RPGツクールのピクチャシステムと同じ考え方。背景もスプライトも「画面に画像を表示する」という点では同じ操作。番号の大小で描画順（前後関係）を制御するほうが、コマンドの種類が少なくなりエディタの実装もシンプルになる。

運用例:
- No.1〜3: 背景用（奥）
- No.4〜10: キャラクター・オブジェクト用（手前）
- No.11〜20: UI演出用（最前面）

### Q: `move_picture` をウェイトありにした理由は？

A: 「スプライトが移動し終わるのを待ってからメッセージを表示」のような演出が多いため。ウェイトなしで移動させたい場合（BGMを鳴らしながら移動など）は、ノンブロッキングのコマンドを間に挟むことで実質的に非同期実行できる。ただし、これだけでは柔軟性が足りない場合は、将来的に `"wait": false` オプションを検討する。

### Q: なぜイベントデータを `data/text/` に統合したのか？

A: イベント内でテキストID（`msg_id`, `telop_id`, `sel_id`）を参照するため、同じファイル内にあったほうが管理しやすい。また既存のコンパイラ・エディタのパイプラインを大きく変更せずに拡張できる。

### Q: 将来的に必要になりそうなコマンドは？

- `if` / `else` / `endif`: 条件分岐（変数やフラグに基づく）
- `set_variable`: 変数の設定
- `shake_screen`: 画面揺れ
- `tint_screen`: 画面の色調変更
- `move_route`: キャラクターの移動ルート指定（RPG探索パートで必要）

これらは Phase 3 以降で必要に応じて追加する。
