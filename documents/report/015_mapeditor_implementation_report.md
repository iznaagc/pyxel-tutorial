# 015 Map Editor 実装報告

## 概要

- 対象仕様: `documents/plan/015_mapeditor_spec_and_next.md`
- 実装範囲: タスク A から J まで
- 残タスク: なし
- 主な編集対象: `tools/gui_editor.py`

## タスク別実施内容

### タスク A: タイルセットプレビューの改善

- `TilesetPalette` にズーム機能を追加
- ホバー時にタイル番号とグリッド座標のツールチップを表示
- 選択変更通知を追加
- `MapPropertyPanel` に選択タイルの拡大プレビューと `+/-` のズーム操作を追加

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット: `screenshots/map_editor_tileset_preview.png`

### タスク B: 複数タイル選択

- `TilesetPalette` に矩形ドラッグ選択を追加
- 選択情報を `(start_index, cols, rows)` で保持するように変更
- `MapCanvas` で複数タイルブロックのスタンプ描画を実装
- 1 ストロークを 1 つの `PaintTileCommand` として Undo 管理

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット: `screenshots/map_editor_multi_tile_selection.png`

### タスク C: タイルセット設定の永続化

- `assets/tilesets/` 外の画像を選択した場合の自動コピー処理を追加
- マップ JSON にはコピー先の相対ファイル名のみ保存
- タイルセット未設定または未検出時の警告表示を追加

編集ファイル:

- `tools/gui_editor.py`
- `assets/tilesets/external_tileset_source.png`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット: `screenshots/map_editor_tileset_import.png`

### タスク D: 矩形塗りつぶしツール

- `MapCanvas` に `pen / rect / bucket` ツール基盤を追加
- 矩形塗りのドラッグプレビューと確定処理を実装
- 複数タイル選択時の繰り返し塗りに対応
- `MapPropertyPanel` にツール切替ボタンを追加
- `P / R / B` ショートカットを接続

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット:
  - `screenshots/map_editor_rect_tool_preview.png`
  - `screenshots/map_editor_rect_tool_applied.png`

### タスク E: バケツツール

- 4 方向フラッドフィルを追加
- クリック 1 回の変更を 1 つの `PaintTileCommand` に集約
- 10000 タイルの安全上限を追加
- 上限到達時の警告表示を追加

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット: `screenshots/map_editor_bucket_fill.png`

### タスク F: コピー / ペースト

- `MapCanvas` に選択ツールと内部クリップボードを追加
- `S` で矩形選択、`Ctrl+C` でコピー、`Ctrl+V` で貼り付けモードを実装
- 貼り付けプレビュー表示と左クリック確定を追加
- 貼り付けを 1 つの `PaintTileCommand` に集約
- `MapPropertyPanel` に `Select (S)` ボタンを追加

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット:
  - `screenshots/map_editor_copy_selection.png`
  - `screenshots/map_editor_paste_preview.png`
  - `screenshots/map_editor_paste_applied.png`

### タスク G: レイヤー UI とレイヤー切替

- マップデータを複数レイヤー構造に拡張
- `MapCanvas` は可視レイヤーを下から順に描画し、編集はアクティブレイヤーのみに限定
- `PaintTileCommand` をレイヤー対応に変更
- マップリサイズを全レイヤー対応に変更
- `LayerPanel` を追加し、追加・削除・上下移動・可視切替・アクティブ切替を実装

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット:
  - `screenshots/map_editor_layers.png`
  - `screenshots/map_editor_layers_visibility.png`

### タスク H: ミニマップ

- `MapCanvas` にビュー状態取得 API とタイル中心ジャンプ API を追加
- `MapSidePanel` に `MinimapWidget` を追加
- マップ全体縮小表示、ビューポート矩形表示、クリックジャンプを実装
- パンとズーム時にミニマップ更新を接続

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット:
  - `screenshots/map_editor_minimap.png`
  - `screenshots/map_editor_minimap_jump.png`

### タスク I: タイル通行判定の設定

- マップ JSON に `passability` を追加
- `MapPropertyPanel` に選択タイル用の `Passable` チェックを追加
- タイルごとの通行可否設定を保存可能に変更
- キャンバス上で通行不可タイルに赤い `×` オーバーレイを表示

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット: `screenshots/map_editor_passability.png`

### タスク J: マップ上のイベント配置

- マップ JSON に `events` を追加
- `MapCanvas` 上でイベント位置に `E` アイコンを表示
- 空きマスのダブルクリックでイベント ID を選択して配置
- 既存イベント上のダブルクリックでテキストモードに切り替え、対応する `EventEditor` を開く処理を追加

編集ファイル:

- `tools/gui_editor.py`

確認:

- `python -m py_compile tools/gui_editor.py`
- スクリーンショット: `screenshots/map_editor_events.png`

## 変更ファイル一覧

- `tools/gui_editor.py`
- `assets/tilesets/external_tileset_source.png`
- `screenshots/map_editor_tileset_preview.png`
- `screenshots/map_editor_multi_tile_selection.png`
- `screenshots/map_editor_tileset_import.png`
- `screenshots/map_editor_rect_tool_preview.png`
- `screenshots/map_editor_rect_tool_applied.png`
- `screenshots/map_editor_bucket_fill.png`
- `screenshots/map_editor_copy_selection.png`
- `screenshots/map_editor_paste_preview.png`
- `screenshots/map_editor_paste_applied.png`
- `screenshots/map_editor_layers.png`
- `screenshots/map_editor_layers_visibility.png`
- `screenshots/map_editor_minimap.png`
- `screenshots/map_editor_minimap_jump.png`
- `screenshots/map_editor_passability.png`
- `screenshots/map_editor_events.png`

## ClaudeCode レビュー依頼用メモ

- 仕様書 `documents/plan/015_mapeditor_spec_and_next.md` のタスク A から J までが完了している前提でレビューしてください。
- 主な観点:
  - `tools/gui_editor.py` に集中した変更の妥当性
  - マップモード追加後の責務分離とイベント配線の見通し
  - Undo/Redo とマップデータ更新の整合性
  - PySide6 の signal-slot と UI 更新タイミングの問題有無
  - 将来的な分割対象やリファクタ候補
