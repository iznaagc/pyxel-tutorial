# 017 gui_editor.py 復元タスク — STEP分割

作成日: 2026-04-06  
対象: `tools/gui_editor.py` の全機能復元  
ベースライン: Git HEAD (`b49a02f`) の 1571行版（テキストエディタのみ）

---

## 現状整理

### 現在の gui_editor.py に含まれている機能（1571行）

| クラス | 行 | 内容 |
|--------|-----|------|
| `PreviewPanel` | 94 | ゲーム画面風プレビュー（messages/selections/telops） |
| `EditCommand` | 421 | Undo用コマンド |
| `RenameCommand` | 458 | リネームUndo用コマンド |
| `FileTreePanel` | 489 | 左ツリー（ファイル→カテゴリ→エントリ） |
| `MessageEditor` | 544 | Messages 編集フォーム |
| `SelectionEditor` | 689 | Selections 編集フォーム |
| `TelopEditor` | 787 | Telops 編集フォーム |
| `EditorWindow` | 840 | メインウィンドウ（テキストモードのみ） |

### 復元が必要な機能（破損前に存在していたもの）

1. **EventEditor** — イベントコマンド編集フォーム（テキストモード内）
2. **マップエディタ全体** — MapCanvas, TilesetPalette, MapSidePanel, MapPropertyPanel, LayerPanel, ToolIconBar, ミニマップ
3. **モード切替** — text ↔ map ↔ character の3モード
4. **CharacterEditor** — キャラクター編集フォーム
5. **キャラクターモード統合** — _load_char_files, _save_char_files, _new_char_file 等

### 注意事項

- **各STEPは独立して動作確認できる単位** にする
- 各STEP完了時にファイルが正常起動し、既存機能が壊れていないこと
- **作業前に必ず退避コピー** (`cp tools/gui_editor.py tools/gui_editor.py.bak_stepN`)
- 1つのSTEPで失敗した場合、前のSTEPのバックアップに戻せること

---

## STEP 0: 準備（必須・最初に実施）

**担当**: 最初に着手する人  
**所要行数**: 変更なし

### 作業内容

1. 現在の `tools/gui_editor.py` を退避コピー
   ```bash
   cp tools/gui_editor.py tools/gui_editor.py.bak_step0
   ```
2. 現在のファイルが正常起動することを確認
   ```bash
   .venv/Scripts/python tools/gui_editor.py
   ```
   - Text Editor モードが開くこと
   - ツリーにファイルが表示されること
   - エントリ選択→編集→プレビューが動くこと

### 完了条件

- バックアップファイルが存在する
- 起動確認OK

---

## STEP 1: Events カテゴリ追加 + EventEditor クラス

**担当**: 未定  
**推定追加行数**: 約400行  
**依存**: STEP 0

### 作業内容

現在の gui_editor.py は `messages`, `selections`, `telops` の3カテゴリのみ。`events` カテゴリとその編集フォームを追加する。

#### 1-1. 定数の更新

```python
CATEGORY_LABELS = {
    "messages": "Messages",
    "selections": "Selections",
    "telops": "Telops",
    "events": "Events",      # 追加
}
CATEGORIES = ["messages", "selections", "telops", "events"]  # events追加
```

#### 1-2. EVENT_CMD_FIELDS 定義

イベントコマンドごとのフィールド仕様を辞書で定義する。ゲーム内で使用されているコマンド:

```python
EVENT_CMD_FIELDS = {
    "wait":          [("duration", "Duration", "int", 60)],
    "message":       [("id", "Message ID", "str", "")],
    "selection":     [("id", "Selection ID", "str", "")],
    "telop":         [("id", "Telop ID", "str", "")],
    "show_picture":  [
        ("no", "Picture No", "int", 1),
        ("file", "File", "str", ""),
        ("x", "X", "int", 0),
        ("y", "Y", "int", 0),
        ("opacity", "Opacity", "int", 100),
        ("colkey", "Color Key", "int_or_none", None),
    ],
    "move_picture":  [
        ("no", "Picture No", "int", 1),
        ("x", "X", "int_or_none", None),
        ("y", "Y", "int_or_none", None),
        ("opacity", "Opacity", "int_or_none", None),
        ("duration", "Duration", "int", 60),
    ],
    "erase_picture": [("no", "Picture No", "int", 1)],
    "fadein":        [("duration", "Duration", "int", 60)],
    "fadeout":       [("duration", "Duration", "int", 60)],
    "play_bgm":     [("file", "File", "str", "")],
    "stop_bgm":     [("fadeout", "Fadeout (ms)", "int", 0)],
    "play_se":      [
        ("sound_no", "Sound No", "int", 0),
        ("ch", "Channel", "int", 3),
    ],
    "change_scene":  [("scene", "Scene", "str", "")],
}
```

#### 1-3. EventEditor クラス実装

- コマンドリスト（QListWidget、ドラッグ並替え対応）
- コマンド種類コンボ（QComboBox）
- 動的フィールド生成（`_build_fields(cmd_type, cmd)`）
- フィールドタイプ: `str`→QLineEdit, `int`→QSpinBox, `float`→QDoubleSpinBox, `bool`→QCheckBox, `int_or_none`→QSpinBox+QCheckBox, `combo`→QComboBox
- コマンド追加/削除ボタン
- `set_data(event_list)`, `_on_changed()`, `_on_cmd_selected()`, `_on_type_changed()`
- `window().mark_dirty()` パターン準拠

#### 1-4. EditorWindow への統合

- `_stack` に EventEditor を追加
- `_on_tree_selected` に events 分岐追加
- PreviewPanel は events プレビュー不要（テキスト表示程度でOK）

### 完了条件

- 起動OK
- demo.json の events カテゴリがツリーに表示される
- `ev_opening_demo` を選択→コマンドリスト表示→フィールド編集可能
- コマンド追加/削除/並替え動作
- 保存→再読込で整合

---

## STEP 2: モード切替の基盤整備

**担当**: 未定  
**推定追加行数**: 約50行  
**依存**: STEP 1

### 作業内容

EditorWindow にモード管理の骨組みを入れる。マップの実装はまだ行わないが、切替の枠組みだけ用意する。

#### 2-1. import と定数追加

```python
import re
import shutil
from collections import deque

from PySide6.QtWidgets import QComboBox, QScrollArea, QFileDialog, QFrame, QListWidgetItem, QActionGroup
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QActionGroup, QImage, QIcon

MAP_DIR = os.path.join(_PROJECT_ROOT, "data", "maps")
CHAR_DIR = os.path.join(_PROJECT_ROOT, "data", "characters")
TILESET_DIR = os.path.join(_PROJECT_ROOT, "assets", "tilesets")
SPRITE_DIR = os.path.join(_PROJECT_ROOT, "assets", "images", "sprite")
```

（※ 既に import 済みのものは重複しないようにする）

#### 2-2. EditorWindow.__init__ にモード変数追加

```python
self._mode = "text"  # "text" | "map" | "character"
self._map_file_data = {}
self._current_map_path = None
self._char_file_data = {}
```

#### 2-3. Mode メニュー追加

- `QActionGroup` で排他的な3つのアクション: Text Editor / Map Editor / Character Editor
- `_switch_mode(mode)` メソッドの雛形（map/character 選択時は「未実装」表示で text に戻す）

#### 2-4. _save_current のモード分岐

```python
def _save_current(self):
    if self._mode == "text":
        self._save_all()
    elif self._mode == "map":
        self._save_map()      # STEP 3 で実装
    elif self._mode == "character":
        self._save_char_files()  # STEP 5 で実装
```

### 完了条件

- Mode メニューに3つの項目が表示される
- Text Editor は従来通り動作
- Map Editor / Character Editor 選択時は警告表示（or 何もしない）で壊れない

---

## STEP 3: マップエディタ — コア（MapCanvas + TilesetPalette）

**担当**: 未定  
**推定追加行数**: 約1200行  
**依存**: STEP 2  
**※ 最大のSTEP。必要なら 3-A / 3-B に分割可能**

### 作業内容

マップエディタの中核である MapCanvas と TilesetPalette を実装する。

#### 3-1. TilesetPalette クラス

QWidget ベースのタイルセットパレット。

- `assets/tilesets/` のPNG画像を読み込み表示
- タイルサイズに合わせてグリッド表示
- 左クリック: 1タイル選択
- 左ドラッグ: 矩形選択（複数タイルスタンプ）
- マウスホイール: パレットズーム
- ホバー時ツールチップ（タイル番号と座標）
- Signal: `tile_selected(int)` — 選択タイルID変更時

#### 3-2. MapCanvas クラス

QWidget ベースのマップキャンバス。

**表示機能:**
- タイルマップの描画（全レイヤー重ね合わせ）
- グリッド表示（`G`キーでトグル）
- パン（中ドラッグ）
- ズーム（ホイール、0.5x〜8.0x、Ctrl+0でリセット）
- 通行不可タイルに赤い×オーバーレイ
- イベント配置マスに `E` バッジ

**描画ツール:**
- **Pen (B)**: 左ドラッグで配置、右ドラッグで消去
- **Rect (R)**: ドラッグ矩形塗り（プレビュー付き）
- **Bucket (F)**: フラッドフィル（4方向、上限10000タイル）
- **Select (S)**: 範囲選択→コピー(Ctrl+C)/ペースト(Ctrl+V)/Delete
- **Eraser Mode (E)**: 全ツールで「タイル0で塗る」動作

**Undo 対応:**
- 各描画操作で `EditCommand` を `QUndoStack` に push
- マップデータは `self._map_file_data[path]` の `layers[active].tiles` を直接更新

**マップデータの構造:**
```python
{
    "version": 1, "name": "...", "width": 20, "height": 15,
    "tile_size": 16, "tileset": "test_tileset.png",
    "passability": {"1": true, "2": false},
    "events": [{"x": 5, "y": 3, "event_id": "ev_chest_01"}],
    "layers": [{"name": "ground", "visible": true, "tiles": [[0,1,...], ...]}]
}
```

#### 3-3. EditorWindow への統合（マップモード基本）

- splitter に MapCanvas を追加
- `_switch_mode("map")`: テキストパネル非表示→MapCanvas表示
- `_load_map_files()`: `data/maps/*.json` 読み込み→ツリー再構築
- `_save_map()`: 現在のマップJSON保存
- `_on_map_tree_selected()`: マップ選択→キャンバスに読み込み
- `Edit > New Map...` メニュー

### 完了条件

- Map Editor モードに切り替え可能
- DebugMap.json が読み込まれ、タイルが描画される
- Pen / Rect / Bucket / Select / Eraser の全ツールが動作
- タイルセットパレットでタイル選択可能
- Undo/Redo 動作
- 保存→再読込で整合

---

## STEP 4: マップエディタ — サイドパネル（Layer, Property, Minimap, ToolIconBar）

**担当**: 未定  
**推定追加行数**: 約800行  
**依存**: STEP 3

### 作業内容

マップエディタの右サイドパネルと操作UIを追加する。

#### 4-1. ToolIconBar クラス

MapCanvas の右端に重ねるアイコンツールバー。

- Pen / Rect / Bucket / Select / Eraser の5ボタン
- ボタンは排他（ツールとEraserが相互排他）
- キーボードショートカット: B / R / F / S / E
- Signal: `tool_changed(str)`, `erase_mode_changed(bool)`

#### 4-2. MapPropertyPanel クラス

- マップ名（QLineEdit）
- タイルサイズ（表示のみ）
- 幅/高さ（QSpinBox + Apply Size ボタン）
- タイルセット選択（Browse... ボタン → QFileDialog）
  - `assets/tilesets/` 内ならそのまま、外部なら `assets/tilesets/` にコピー
- 通行判定（Passable ON/OFF）
- パレットズーム（-/+ ボタン）
- Signal: `property_changed`, `resize_requested`, `tileset_changed`

#### 4-3. LayerPanel クラス

- レイヤー一覧（QListWidget）
- アクティブレイヤー選択
- 名前編集（ダブルクリック）
- 表示/非表示トグル
- 追加/削除/上移動/下移動ボタン
- ドラッグ並替え
- 最低1レイヤー保持
- Signal: `active_layer_changed(int)`, `layers_changed`

#### 4-4. MapSidePanel クラス

上記パネルをまとめるコンテナ。

- 上部: TilesetPalette
- 中部: LayerPanel
- 下部: MapPropertyPanel + ミニマップ

#### 4-5. ミニマップ

MapSidePanel 内に組み込み。

- マップ全体の縮小表示
- 現在のビューポート枠表示
- クリックジャンプ

#### 4-6. イベント配置UI

- 空マスのダブルクリック → イベント選択ダイアログ（data/text/*.json の events カテゴリから一覧）
- 配置済みマスのダブルクリック → Text Editor のイベントへジャンプ
- Undo 対応

#### 4-7. EditorWindow 統合

- splitter に MapSidePanel を追加
- splitter sizes: `[200, 0, 0, 700, 250, 0]` (map mode)
- ToolIconBar の Signal 接続
- LayerPanel の Signal 接続
- PropertyPanel の Signal 接続

### 完了条件

- レイヤー追加/削除/並替え/表示切替が動作
- タイルセット変更が動作
- マップサイズ変更が動作
- 通行判定の設定と×オーバーレイ表示
- ミニマップ表示とクリックジャンプ
- ToolIconBar でツール切替（キーボード含む）
- イベント配置とダブルクリックジャンプ

---

## STEP 5: キャラクターエディタ

**担当**: 未定  
**推定追加行数**: 約350行  
**依存**: STEP 2

### 作業内容

キャラクター編集モードを追加する。

#### 5-1. 定数追加

```python
STAT_KEYS = ["hp", "mp", "str", "vit", "int", "mnd", "luk"]
STAT_LABELS = {"hp": "HP", "mp": "MP", ...}
PHYSICAL_SKILL_KEYS = ["dagger", "sword", "katana", "axe", "spear", "staff", "claw", "bow"]
PHYSICAL_SKILL_LABELS = {"dagger": "短剣", ...}
MAGIC_SKILL_KEYS = ["healing", "elemental", "buff", "debuff"]
MAGIC_SKILL_LABELS = {"healing": "回復", ...}
GRAPHIC_CUT_SIZE = 32
DEFAULT_CHARACTER = { ... }
```

#### 5-2. CharacterEditor クラス

QScrollArea 内に6つの QGroupBox:
- 基本情報（名前/初期職業ID/性格ID）
- グラフィック（顔/歩行/戦闘 × QComboBox画像 + SpinBox選択ID + 32x32プレビュー）
- 基礎ステータス（HP〜LUK）
- 成長率 - ステータス
- 成長率 - 物理スキル（短剣〜弓）
- 成長率 - 魔術スキル（回復〜弱体）

パターン: `set_data()`, `_on_changed()`, `_updating` フラグ, `window().mark_dirty()`

#### 5-3. EditorWindow 統合

- splitter に CharacterEditor を追加
- `_switch_mode("character")`: `_char_editor.show()`, `_load_char_files()`
- `_load_char_files()`: `data/characters/*.json` 読み込み→ツリー構築
- `_save_char_files()`: 全ファイル保存
- `_new_char_file()`: 新規ファイル作成
- `_add_char_id()`, `_delete_char_id()`: エントリ追加/削除
- `_on_char_tree_selected()`: 選択→エディタに反映
- `_flush_undo` にキャラクターストア分岐
- `_rename_id` にキャラクターストア分岐

#### 5-4. データディレクトリ

`data/characters/default.json` が既に存在する（前回作成済み）。

### 完了条件

- Character Editor モードに切替可能
- default.json のキャラクターがツリーに表示
- 全フィールド（基本情報/グラフィック/ステータス/成長率）の編集が動作
- グラフィックプレビュー表示
- 新規追加/削除/リネーム動作
- Undo/Redo 動作
- 保存→再読込で整合

---

## STEP 6: compiler.py のキャラクター対応

**担当**: 未定  
**推定追加行数**: 約80行（compiler.py）  
**依存**: STEP 5

### 作業内容

`tools/compiler.py` にキャラクターデータのコンパイル機能を追加。

- `validate_character()`: 必須フィールドチェック
- `load_and_validate_characters()`: JSON読込+バリデーション
- `merge_characters()`: 複数ファイルマージ+重複IDチェック
- `compile_characters()`: `data/characters/*.json` → `data/compiled/characters_all.bin`
- `main()` から `compile_text()` と `compile_characters()` を順次呼出

### 完了条件

- `python tools/compiler.py` で text + characters 両方コンパイル成功
- `data/compiled/characters_all.bin` が生成される

---

## STEP 7: ドキュメント更新

**担当**: 未定  
**依存**: 全STEP完了後

### 作業内容

- `documents/history/works.md`: 復元作業の履歴追記
- `documents/tutorial/007_gui_editor_manual.md`: 3モード構成の記載に更新（既に更新済みなら差分確認のみ）

---

## 依存関係まとめ

```
STEP 0 (準備)
  ├── STEP 1 (EventEditor)
  │     └── STEP 2 (モード切替基盤)
  │           ├── STEP 3 (MapCanvas + TilesetPalette)
  │           │     └── STEP 4 (サイドパネル群)
  │           └── STEP 5 (CharacterEditor)
  │                 └── STEP 6 (compiler.py)
  └── STEP 7 (ドキュメント) ← 全完了後
```

### 並行作業可能な組み合わせ

- **STEP 3+4** と **STEP 5+6** は STEP 2 完了後に並行作業可能
  - 例: Claude Code → STEP 3+4（マップ）、Codex → STEP 5+6（キャラクター）
  - 例: 逆の割り当てでもOK
- **STEP 1** と **STEP 2** は直列（1→2の順）

### 推奨分担案

| STEP | 推奨担当 | 理由 |
|------|---------|------|
| STEP 0 | 最初の着手者 | 退避のみ |
| STEP 1 | Claude Code | 前回 EventEditor の構造を読んでいる |
| STEP 2 | STEP 1 と同じ | 連続作業の方が効率的 |
| STEP 3+4 | Claude Code | マップエディタの全コードを前回読んでいる |
| STEP 5+6 | Codex | 独立性が高く、仕様が明確 |
| STEP 7 | 最後に着手する人 | 全体確認後 |

---

## 復元後の最終確認チェックリスト

- [ ] Text Editor モードが開く
- [ ] Messages / Selections / Telops / Events の編集が動作
- [ ] Map Editor モードが開く
- [ ] マップ一覧が読める
- [ ] タイルセットパレットが表示される
- [ ] 全描画ツール（Pen/Rect/Bucket/Select/Eraser）が動作
- [ ] レイヤー操作が動作
- [ ] ミニマップが表示される
- [ ] Character Editor モードが開く
- [ ] キャラクターファイルが読める
- [ ] 全フィールドの編集が動作
- [ ] モード切替時の未保存確認が動作
- [ ] Ctrl+S / F5 / Ctrl+Z / Ctrl+Y が全モードで動作
- [ ] 起動直後にクラッシュしない
