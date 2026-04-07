# マップエディタ 仕様書 & 次フェーズ実装ガイド

## 1. 概要

`tools/gui_editor.py` に RPG ツクール風のタイルマップエディタ機能を統合した。
テキストエディタモードと **Mode メニュー** で切り替えて使用する。

Phase 1 (MVP) として以下を実装済み:
- タイルパレットからのタイル選択
- ペン描画（左クリック）/ 消去（右クリック）
- 単一レイヤー
- マップサイズ設定・リサイズ
- JSON 保存/読込（`data/maps/*.json`）
- Undo/Redo（QUndoStack ベース）
- ズーム（ホイール）/ パン（中クリックドラッグ）
- グリッド表示切替（G キー）

---

## 2. ファイル構成

```
tools/gui_editor.py          # エディタ本体 (約2994行)
data/maps/                   # マップ JSON 保存先
assets/tilesets/             # タイルセット PNG 置き場
  test_tileset.png           # テスト用 (8x8タイル, 各16x16px)
```

---

## 3. データ形式

### マップ JSON (`data/maps/<name>.json`)

```json
{
  "version": 1,
  "name": "はじまりの森",
  "width": 20,
  "height": 15,
  "tile_size": 16,
  "tileset": "forest.png",
  "layers": [
    {
      "name": "ground",
      "visible": true,
      "tiles": [[0, 0, 1, 1, ...], [0, 1, 1, 2, ...], ...]
    }
  ]
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `version` | int | データバージョン（現在 1） |
| `name` | string | マップ表示名 |
| `width` / `height` | int | マップサイズ（タイル数） |
| `tile_size` | int | 1タイルのピクセルサイズ（16 がデフォルト） |
| `tileset` | string | `assets/tilesets/` からの相対ファイル名 |
| `layers` | array | レイヤー配列（Phase 1 では要素1つのみ） |
| `layers[].tiles` | int[][] | 2D配列 `[row][col]`。0=空、1~=タイルインデックス |

**タイルインデックス**: タイルセット画像を `tile_size` で区切り、左上から右へ行単位で 1-based で採番。0 は「タイルなし（空）」を意味する。

---

## 4. クラス構成（マップ関連のみ）

### 4.1 Undo コマンド

| クラス | 行 | 説明 |
|---|---|---|
| `PaintTileCommand` | 515-533 | 1ストローク分のタイル変更を記録。`changes: [(row, col, old, new), ...]` |
| `ResizeMapCommand` | 535-569 | マップサイズ変更。変更前の tiles 全体をスナップショット保存 |

### 4.2 UI ウィジェット

| クラス | 行 | 説明 |
|---|---|---|
| `TilesetPalette` | 576-683 | タイルセット PNG をグリッド表示。クリックでタイル選択 |
| `MapCanvas` | 690-938 | メインキャンバス。描画・ズーム・パン・ペン/消しゴム |
| `MapPropertyPanel` | 944-1057 | マップ名・サイズ・タイルセット設定フォーム |
| `MapSidePanel` | 1063-1084 | TilesetPalette + MapPropertyPanel の縦分割コンテナ |

### 4.3 ヘルパー

| 関数/定数 | 行 | 説明 |
|---|---|---|
| `MAP_DIR` | 19 | `data/maps/` の絶対パス |
| `TILESET_DIR` | 20 | `assets/tilesets/` の絶対パス |
| `_create_default_map()` | 497-513 | 空のマップデータ dict を生成 |

### 4.4 EditorWindow のマップ関連メソッド

| メソッド | 説明 |
|---|---|
| `_switch_mode(mode)` | "text" ↔ "map" のモード切替。未保存確認 → パネル show/hide → データ読込 |
| `_load_map_files()` | `data/maps/*.json` を読み込みツリーに表示 |
| `_save_map()` | 現在のマップを JSON 保存 |
| `_save_current()` | モードに応じて `_save_all` or `_save_map` を呼ぶ |
| `_on_map_tree_selected()` | ツリーでマップ選択 → タイルセット読込 → キャンバス/パネル反映 |
| `_on_map_property_changed()` | プロパティ変更 → dirty フラグ |
| `_on_map_resize()` | サイズ変更 → `ResizeMapCommand` push |
| `_on_tileset_changed()` | タイルセット変更 → パレット再読込 |
| `_new_map()` | 新規マップ作成ダイアログ → JSON 生成 → ツリー選択 |

---

## 5. UI レイアウト

### テキストモード（既存）
```
[FileTree 200px] | [Editor Stack 500px] | [PreviewPanel 400px]
```

### マップモード
```
[FileTree 200px] | [MapCanvas 700px] | [MapSidePanel 250px]
                                        ├ TilesetPalette (上)
                                        └ MapPropertyPanel (下)
```

QSplitter に 5 ウィジェットが入っており、モードに応じて show/hide + `setSizes` で切り替え。

```python
# splitter 内のウィジェット順序:
# [0] FileTreePanel
# [1] text_center (テキスト編集エリア)
# [2] PreviewPanel
# [3] MapCanvas
# [4] MapSidePanel
```

---

## 6. 操作方法

| 操作 | 機能 |
|---|---|
| 左クリック / ドラッグ | タイル配置（選択中のタイル） |
| 右クリック / ドラッグ | 消去（tile=0 に設定） |
| 中クリック + ドラッグ | パン（スクロール） |
| ホイール | ズーム（0.5x ~ 8.0x、カーソル中心） |
| G | グリッド表示切替 |
| E / Eraser ボタン | 消しゴム選択（tile=0） |
| Ctrl+Z / Ctrl+Y | Undo / Redo |
| Ctrl+S | 保存 |
| Mode メニュー | テキスト ↔ マップ切替 |
| Edit > New Map... | 新規マップ作成 |

---

## 7. 既知の設計上の考慮点

1. **QSplitter 5ペイン構成**: hide/show + `setSizes([..., 0, 0])` で切替。ウィジェットの追加/削除はしない
2. **Undo スタック共有**: テキスト/マップで同じ `_undo_stack` を使用。モード切替時にクリアされる
3. **タイルセット空**: `_new_map` で作成直後は tileset が空文字。ユーザーがブラウズで設定する前提
4. **editors パターン**: 各エディタは `set_data(data)` で直接参照を受け取り、`_on_changed()` で in-place 修正 → `window().mark_dirty()` を呼ぶ
5. **`layers` 配列**: Phase 1 では要素 1 つだが、Phase 2 の複数レイヤー対応のため最初から配列形式

---

## 8. Phase 2 実装タスク一覧

以下のタスクを Codex に依頼する。優先度順に記載。

### 8.1 タイルセット管理の強化 (優先度: 高)

**目的**: スプライトシート（大きなタイルセット画像）を実用的に扱えるようにする。

#### タスク A: タイルセットプレビューの改善
- **ファイル**: `tools/gui_editor.py` の `TilesetPalette` クラス (576行目~)
- **内容**:
  - 現在は固定 2x 表示。**ズーム機能を追加**（ホイール or +/- ボタン）
  - パレット上にマウスホバーでタイルインデックスとグリッド座標をツールチップ表示
  - 選択中のタイルを MapPropertyPanel 付近にプレビュー表示（拡大）

#### タスク B: 複数タイル選択 (矩形選択)
- **ファイル**: `TilesetPalette` + `MapCanvas`
- **内容**:
  - パレット上でドラッグして矩形範囲のタイルを選択可能にする
  - 選択された矩形タイルブロックをキャンバスに一括描画
  - `_selected_tile: int` → `_selected_rect: (start_idx, cols, rows)` に拡張
  - `PaintTileCommand` はそのまま使える（changes リストに複数タイル分が入る）

#### タスク C: タイルセット設定の永続化
- **ファイル**: `MapPropertyPanel._on_browse_tileset()` (1030行目~)
- **内容**:
  - 現在は `os.path.basename(path)` だけ保存。`assets/tilesets/` 外の画像を選んだ場合に自動コピーする機能を追加
  - タイルセットが見つからない場合のエラー表示を改善（ステータスバーに警告）

### 8.2 描画ツールの拡充 (優先度: 高)

#### タスク D: 矩形塗りつぶしツール
- **ファイル**: `MapCanvas` クラス (690行目~)
- **内容**:
  - ツールモード切替の仕組みを追加: `self._tool = "pen" | "rect" | "bucket"`
  - MapPropertyPanel または ツールバーにツール選択 UI を追加
  - 矩形ツール: ドラッグ開始→終了で矩形範囲を選択タイルで塗りつぶし
  - ドラッグ中はプレビュー表示（半透明のオーバーレイ）
  - マウスリリース時に1つの `PaintTileCommand` として push
  - **ショートカット**: P=ペン、R=矩形、B=バケツ

#### タスク E: バケツ（フラッドフィル）ツール
- **ファイル**: `MapCanvas` クラス
- **内容**:
  - クリック位置と同じタイル ID の連結領域を選択タイルで塗りつぶす
  - 4方向フラッドフィル（BFS/DFS）
  - 全変更を1つの `PaintTileCommand` にまとめる
  - パフォーマンス上限: 最大 10000 タイルまで（無限ループ防止）

#### タスク F: コピー/ペースト (矩形選択)
- **ファイル**: `MapCanvas` クラス
- **内容**:
  - 選択ツール (S キー): ドラッグで矩形範囲選択 → 選択範囲ハイライト
  - Ctrl+C: 選択範囲のタイルデータをクリップボード（内部変数）にコピー
  - Ctrl+V: ペーストモード → マウス位置にプレビュー → クリックで確定
  - `PasteTileCommand` を新規作成するか、`PaintTileCommand` の changes として扱う

### 8.3 複数レイヤー (優先度: 中)

#### タスク G: レイヤー UI とレイヤー切替
- **ファイル**: `MapSidePanel` に `LayerPanel` を追加
- **内容**:
  - レイヤー一覧を `QListWidget` で表示
  - レイヤー追加/削除/並び替え（ドラッグ）
  - アクティブレイヤー選択（描画対象の切替）
  - レイヤー表示/非表示トグル（目のアイコン）
  - JSON の `layers` 配列に複数要素が入るようにする
- **`MapCanvas` 変更**:
  - `self._active_layer_idx` を追加
  - `paintEvent` で全レイヤーを下から順に描画（非表示レイヤーはスキップ）
  - ペン描画は `_active_layer_idx` のレイヤーのみに適用
  - `PaintTileCommand` に `layer_idx` パラメータを追加

### 8.4 グリッド表示・ナビゲーション改善 (優先度: 中)

#### タスク H: ミニマップ
- **ファイル**: `MapSidePanel` に追加
- **内容**:
  - マップ全体を縮小表示する小さなウィジェット
  - 現在の表示範囲をハイライト
  - クリックでジャンプ（キャンバスのパンオフセットを変更）

#### タスク I: タイル通行判定の設定
- **ファイル**: `MapPropertyPanel` or 新規 `PassabilityEditor`
- **内容**:
  - 各タイルに通行可/不可フラグを設定
  - データ形式: `"passability": { "1": true, "2": false, ... }` をマップ JSON に追加
  - キャンバスでオーバーレイ表示（通行不可タイルに × マーク）

### 8.5 イベント配置連携 (優先度: 低 / Phase 3)

#### タスク J: マップ上のイベント配置
- **ファイル**: `MapCanvas` + `EditorWindow`
- **内容**:
  - マップ JSON に `"events": [{"x": 5, "y": 3, "event_id": "ev_chest_01"}, ...]` を追加
  - キャンバスでイベント位置にアイコン表示
  - ダブルクリックでイベント編集（既存の EventEditor をテキストモードで開く）

---

## 9. 実装時の注意事項

### コーディング規約
- 既存のエディタパターン（`set_data()` / `_on_changed()` / `mark_dirty()`）に従う
- Undo コマンドは `QUndoCommand` を継承。redo/undo で in-place 更新
- `_updating` フラグでシグナルの再帰を防止
- `_pushing_undo` フラグで Undo push 中の再帰を防止

### テスト方法
```bash
# エディタ起動
.venv/Scripts/python tools/gui_editor.py

# offscreen テスト (CI 用)
QT_QPA_PLATFORM=offscreen .venv/Scripts/python -c "
from PySide6.QtWidgets import QApplication
import sys; app = QApplication(sys.argv)
from gui_editor import EditorWindow
w = EditorWindow(); w.show()
w._switch_mode('map')
# ... テストコード
"
```

### スクリーンショット
- 機能追加後は必ず `screenshots/` にスクリーンショットを保存する（CLAUDE.md / AGENT.md ルール）
- ファイル名例: `map_editor_rect_tool.png`, `map_editor_layers.png`

### ブランチ運用
- ベースブランチは `develop`（main ではない）
- ブランチ名: `task/<Issue番号>-<簡潔な説明>` (例: `task/15-map-rect-tool`)
- PR は `develop` に向けて作成

---

## 10. 参照ファイル一覧

| ファイル | 説明 |
|---|---|
| `tools/gui_editor.py` | エディタ本体 |
| `documents/plan/014_mapeditor.md` | 元の要件メモ |
| `documents/plan/015_mapeditor_spec_and_next.md` | **本ドキュメント** |
| `AGENT.md` | AI エージェント作業ルール |
| `CLAUDE.md` | プロジェクトルール |
| `assets/tilesets/test_tileset.png` | テスト用タイルセット |
| `screenshots/map_editor_test.png` | マップエディタ動作スクリーンショット |
