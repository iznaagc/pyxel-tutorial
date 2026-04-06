# 作業履歴

---

## 2026-04-07 - gui_editor 復旧: STEP 4-E（イベント配置 UI）実施

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step4e`, `documents/history/works.md`

### 概要

マップ上にイベントを配置・表示・削除する機能と、配置済みイベントから Text Editor へジャンプする機能を実装しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step4e` として退避 |
| イベントバッジ描画 | paintEvent にイベント配置マスの紫色「E」バッジ描画を追加 |
| MapCanvas シグナル | `event_place_requested(col, row)` — 空マスダブルクリック、`event_jump_requested(event_id)` — 配置済みマスダブルクリック |
| mouseDoubleClickEvent | ダブルクリック時に既存イベントの有無を判定して適切なシグナルを発火 |
| イベント配置ダイアログ | `_on_event_place()` — data/text/*.json の events カテゴリからイベント一覧を表示し選択配置 |
| イベントジャンプ | `_on_event_jump()` — Yes でテキストエディタのイベントへジャンプ、No でマップからイベント削除 |
| _collect_event_ids | 全テキストファイルの events カテゴリからイベントID一覧を収集するヘルパー |

### 確認内容

- `py_compile` で構文チェック通過
- オフスクリーンテストで以下を確認:
  - イベントIDの収集（`ev_opening_demo` が取得される）
  - マップデータへのイベント追加/削除
  - イベントバッジ付きの paintEvent がクラッシュしない
  - 全モード切替が正常動作

### 備考

- イベントデータ形式: `[{"x": col, "y": row, "event_id": "ev_xxx"}, ...]`
- ダブルクリック時の3択（ジャンプ/削除/キャンセル）で操作ミスを防止
- 次の STEP 4 候補: レイヤー機能の仕上げ（並べ替え、名前編集など）

---

## 2026-04-07 - gui_editor 復旧: STEP 4-D（ミニマップ＋パン）実施

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step4d`, `documents/history/works.md`

### 概要

MapCanvas に中ドラッグによるパン（スクロール）機能を追加し、MapSidePanel 下部にミニマップウィジェットを実装しました。ミニマップはマップ全体の縮小表示、ビューポート枠の表示、クリック/ドラッグによるジャンプ機能を持ちます。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step4d` として退避 |
| MapCanvas パン機能 | `_pan_x` / `_pan_y` オフセット追加。中ドラッグでパン、ズーム時もオフセット維持 |
| MapCanvas API追加 | `viewport_info()` — ビューポート情報取得、`pan_to_tile()` — 指定タイルへジャンプ |
| MapCanvas シグナル | `viewport_changed` — パン/ズーム時に発火 |
| 座標系パン対応 | `_tile_rect`、`_tile_at_pos`、ドラッグプレビュー、選択範囲、ペーストプレビューの全座標計算をパンオフセット対応に修正 |
| Minimap 新規実装 | マップ全体の縮小描画、ビューポート枠（黄色）、クリック/ドラッグでジャンプ |
| MapSidePanel 拡張 | 下部に「Minimap」ラベルとミニマップウィジェットを追加 |
| EditorWindow 統合 | ミニマップのジャンプシグナル接続、ビューポート変更時の自動更新、マップ選択/プロパティ変更時のミニマップ更新 |
| resize 撤廃 | paintEvent 末尾の `self.resize()` を削除（パン対応のため固定サイズ化） |

### 確認内容

- `py_compile` で構文チェック通過
- オフスクリーンテストで以下を確認:
  - Minimap ウィジェットが MapSidePanel に配置される
  - DebugMap 読み込み時にミニマップにマップデータが反映
  - `viewport_info()` が正しいビューポート情報を返す
  - パン後のビューポート座標が正しく変化
  - `pan_to_tile()` でキャンバスがジャンプ
  - ミニマップの `jump_requested` シグナルでキャンバスがジャンプ
  - 全モード切替が正常動作

### 備考

- ミニマップは最上位レイヤーの可視タイルを縮小描画（全レイヤー合成は重すぎるため省略）
- ビューポート枠はパン/ズーム操作のたびにリアルタイム更新
- 次の STEP 4 候補: イベント配置 UI、レイヤー機能の仕上げ

---

## 2026-04-06 - gui_editor 復旧: STEP 4-C（通行判定 UI）実施

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step4c`, `documents/history/works.md`

### 概要

通行判定（Passability）の表示オーバーレイと編集UIを実装しました。マップ上の通行不可タイルを赤い×で可視化し、タイルごとの通行可否をプロパティパネルで切り替えられます。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step4c` として退避 |
| MapCanvas オーバーレイ | `_show_passability` フラグ追加。ON 時に通行不可タイル（`passability[id]=false`）に赤い×を描画 |
| MapCanvas ショートカット | `P` キーで通行判定オーバーレイの表示/非表示トグル |
| ToolIconBar 拡張 | 「Pass (P)」トグルボタン追加。ON 時オレンジ色ハイライト。`passability_toggled` シグナル |
| MapPropertyPanel 通行判定UI | タイル選択に連動する「Passable / Blocked」トグルボタン。タイルIDごとに `passability` 辞書を編集 |
| シグナル接続 | TilesetPalette → MapPropertyPanel の `set_selected_tile` 接続を追加 |

### 確認内容

- `py_compile` で構文チェック通過
- オフスクリーンテストで以下を確認:
  - ToolIconBar の Pass ボタンで MapCanvas のオーバーレイ表示/非表示がトグル
  - MapPropertyPanel でタイル選択 → 通行可否の切替 → map_data の passability 辞書に反映
  - 全モード切替が正常動作

### 備考

- passability データ形式: `{"タイルID文字列": bool}` — 未登録タイルはデフォルト通行可（true）
- オーバーレイは全レイヤーの最上位非0タイルIDを基準に判定
- 次の STEP 4 候補: ミニマップ、イベント配置 UI、レイヤー機能の仕上げ

---

## 2026-04-06 - gui_editor 復旧: STEP 4-B（ToolIconBar）実施

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step4b`, `documents/history/works.md`

### 概要

MapCanvas 上にオーバーレイ配置する `ToolIconBar` クラスを実装し、MapPropertyPanel にあったツール選択（QComboBox）と Eraser チェックボックスを ToolIconBar に移行しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step4b` として退避 |
| ToolIconBar 新規実装 | Pen/Rect/Bucket/Select の排他ボタン + Eraser トグルの計5ボタン。MapCanvas の右上にオーバーレイ配置 |
| MapPropertyPanel 整理 | `tool_changed` / `erase_mode_changed` シグナルと tool_combo / erase_check を削除 |
| MapCanvas シグナル追加 | `tool_changed_by_key` / `erase_mode_changed_by_key` でキーボードショートカットとToolIconBarの双方向同期 |
| MapCanvas resizeEvent | ToolIconBar を右上に自動配置 |
| EditorWindow 統合 | ToolIconBar の生成・シグナル接続。MapPropertyPanel の旧接続を削除 |

### 確認内容

- `py_compile` で構文チェック通過
- オフスクリーンテストで以下を確認:
  - ToolIconBar が MapCanvas の子ウィジェットとして配置される
  - ツールボタンクリック → MapCanvas の `_tool` が変更される
  - Eraser トグル → MapCanvas の `_erase_mode` が変更される
  - Text / Character モード切替で壊れない
  - 全3モードの切替が正常に動作

### 備考

- ToolIconBar のスタイルは半透明の暗色背景で、マップ描画の視認性を妨げない設計
- キーボードショートカット（B/R/F/S/E）は MapCanvas の keyPressEvent に残し、ToolIconBar のボタン状態と双方向同期
- 次の STEP 4 候補: MapPropertyPanel の強化（サイズ変更 Apply ボタンなど）、ミニマップ、通行判定 UI、イベント配置 UI

---

## 2026-04-06 - gui_editor 復旧: STEP 4-A 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step4a`, `documents/history/works.md`

### 概要

Map Editor のサイドパネル拡張として `LayerPanel` を追加し、レイヤーの追加・削除・アクティブ切替・表示/非表示切替を行えるようにしました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step4a` として退避 |
| LayerPanel 実装 | レイヤー一覧表示、`+`/`-`/`Toggle` ボタン、アクティブレイヤー選択を追加 |
| MapSidePanel 統合 | `TilesetPalette` と `MapPropertyPanel` の間に `LayerPanel` を追加 |
| MapCanvas 対応 | `_active_layer_idx` を追加し、描画・編集対象をアクティブレイヤーへ切り替えるよう変更 |
| レイヤー描画 | `visible` が true のレイヤーだけを下から順に描画するよう変更 |
| EditorWindow 接続 | `active_layer_changed` / `layers_changed` を接続し、MapCanvas とマップデータへ反映するよう追加 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で `CheckMap.json` を読み込み、レイヤー追加・アクティブ切替・表示トグル・削除が動作することを確認

### 備考

- 今回は最低限のレイヤー操作のみで、並べ替え・名前編集・表示アイコン化は未着手
- 次の map 系タスク候補はミニマップ、通行判定 UI、イベント配置、またはレイヤー機能の仕上げ

## 2026-04-06 - gui_editor 復旧: STEP 3-E 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step3e`, `documents/history/works.md`

### 概要

Map Editor の貼り付け操作を仕上げ、`Ctrl+V` 後の貼り付けプレビューと `Esc` キャンセルを追加しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step3e` として退避 |
| 貼り付けプレビュー移動 | `select` ツール中に貼り付け待機状態ならマウス位置にプレビュー起点が追従するよう変更 |
| `Esc` キャンセル | 貼り付け待機中に `Esc` で `_paste_origin` を解除する処理を追加 |
| プレビュー描画強化 | 貼り付け範囲の矩形だけでなく、クリップボード内容の半透明タイル描画を追加 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーンで `Ctrl+V` 相当後に貼り付け開始位置がセットされることを確認
- 貼り付け待機中の位置更新、`Esc` キャンセル、貼り付け確定後のタイル反映を確認

### 備考

- 今回は貼り付けプレビューとキャンセルだけを追加
- レイヤー、ミニマップ、イベント配置など STEP 4 系は未着手のまま
- 次の map 系タスク候補は STEP 4 系の UI 拡張

## 2026-04-06 - gui_editor 復旧: STEP 3-D 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step3d`, `documents/history/works.md`

### 概要

Map Editor の描画編集に対して Undo/Redo を追加し、`Ctrl+Z / Ctrl+Y` でマップ状態を戻せるようにしました。今回はマップ全体スナップショットを `UndoStack` に積む方式で統合しています。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step3d` として退避 |
| MapEditCommand 追加 | マップ全体 dict を in-place で差し替える `MapEditCommand` を追加 |
| スナップショット管理 | `EditorWindow` に `_map_snapshot` を追加し、マップ選択・モード切替時に更新/クリアするよう変更 |
| `_flush_undo()` 分岐 | map モード時は現在マップ全体の差分を見て `MapEditCommand` を push するよう追加 |
| `_on_undo_or_redo()` 分岐 | map モード時は `MapCanvas`、`MapPropertyPanel`、`TilesetPalette` を再同期する処理を追加 |
| 保存連携 | `_save_map()` の前に `_flush_undo()` を行い、保存時に `UndoStack` を clean に戻すよう変更 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で `DebugMap.json` を読み込み、単一タイル編集後に Undo/Redo が動作することを確認
- Rect 塗りのような複数タイル編集でも Undo が効くことを確認

### 備考

- 現在の Undo 単位は「デバウンスされたマップ全体スナップショット」で、専用の差分コマンドにはしていない
- レイヤー・イベント配置・通行判定が入った後もこの方式で当面は対応可能
- 次の map 系タスク候補は貼り付けプレビュー/キャンセルの仕上げ、または STEP 4 系の UI 拡張

## 2026-04-06 - gui_editor 復旧: STEP 3-C 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step3c`, `documents/history/works.md`

### 概要

Map Editor の `Select` 系操作として、範囲選択、内部コピー、貼り付け、`Delete` による範囲消去を `MapCanvas` に追加しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step3c` として退避 |
| Select 状態追加 | `_selection_start`, `_selection_end`, `_clipboard_tiles`, `_paste_origin` を追加 |
| 範囲選択 | `select` ツールでドラッグ選択し、キャンバス上に破線矩形で表示するよう追加 |
| コピー | `Ctrl+C` 相当の `_copy_selection()` で選択範囲を内部クリップボードへ保存 |
| 貼り付け | `_paste_tiles()` を追加し、選択範囲起点または `(0,0)` 起点から貼り付け可能にした |
| 範囲消去 | `Delete` 相当の `_delete_selection()` で選択範囲をタイル 0 に置換 |
| UI 接続 | `MapPropertyPanel` の Tool コンボに `select` を追加 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で選択範囲コピー、貼り付け、Delete 範囲消去がマップデータへ反映されることを確認
- `MapPropertyPanel` の Tool コンボで `select` を選ぶと `MapCanvas` 側へ反映されることを確認

### 備考

- 今回のコピー/貼り付けは内部クリップボードのみで、OS クリップボード連携は未実装
- 貼り付けのマウス追従プレビューや `Esc` キャンセルの仕上げ、マップ描画 Undo/Redo は未着手
- 次の map 系タスク候補はマップ描画 Undo/Redo、または STEP 4 系の UI 拡張

## 2026-04-06 - gui_editor 復旧: STEP 3-B 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step3b`, `documents/history/works.md`

### 概要

Map Editor の描画ツール基盤として、`Pen / Rect / Bucket / Eraser` の切替と適用を `MapCanvas` に追加しました。今回はツール操作の復旧に絞り、`Select` とマップ専用 Undo/Redo は次段階へ回しています。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step3b` として退避 |
| MapCanvas 拡張 | `_tool`, `_erase_mode`, `_drag_start`, `_drag_current` を追加 |
| Pen/Eraser | 左ドラッグ配置、右クリック消去に加え、消しゴムモードを追加 |
| Rect | ドラッグ矩形のプレビューと矩形塗り処理を追加 |
| Bucket | 4方向フラッドフィル（上限10000タイル）の処理を追加 |
| キーボード操作 | `B / R / F / E` でペン・矩形・バケツ・消しゴムを切り替える処理を追加 |
| プロパティ UI | `MapPropertyPanel` に Tool コンボと Eraser Mode チェックを追加し、MapCanvas と接続 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で `DebugMap.json` を読み込み、Rect 塗り、Bucket 塗り、Eraser がデータへ反映されることを確認
- `MapPropertyPanel` の Tool/Erase UI 変更が `MapCanvas` 側に反映されることを確認

### 備考

- `Select` ツール、コピー/ペースト、Delete 範囲消去は未着手
- マップ描画操作の Undo/Redo は未着手で、現時点では直接データ更新
- 次の map 系タスク候補は `Select` 系を含む `STEP 3-C`、または `STEP 4`

## 2026-04-06 - gui_editor 復旧: STEP 3-A 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step3a`, `documents/history/works.md`

### 概要

Map Editor の土台復旧として、`MapCanvas`、`TilesetPalette`、`MapPropertyPanel`、`MapSidePanel` を追加し、`Mode > Map Editor` で `data/maps/*.json` を読み込み・表示・保存できる状態まで戻しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step3a` として退避 |
| マップ定数追加 | `MAP_DIR` / `TILESET_DIR` と `_create_default_map()` を追加 |
| TilesetPalette 実装 | PNG タイルセットの簡易表示とタイル選択を追加 |
| MapCanvas 実装 | 単一レイヤー描画、簡易ペン配置、右クリック消去、ホイールズームを追加 |
| MapPropertyPanel 実装 | マップ名、幅、高さ、タイルサイズ、tileset の基本編集フォームを追加 |
| Map モード統合 | `_switch_mode(\"map\")`, `_load_map_files()`, `_build_map_tree()`, `_on_map_tree_selected()`, `_save_map()`, `_new_map()` を追加 |
| レイアウト統合 | splitter に `MapCanvas` と `MapSidePanel` を追加し、text/character/map で表示切替できるよう更新 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で `Mode > Map Editor` へ切り替え、`data/maps/*.json` が読めることを確認
- `DebugMap.json` 選択時に `test_tileset.png` がプロパティとキャンバスへ反映されることを確認
- `MapCanvas` 上で簡易ペン描画がマップデータへ反映されることを確認
- `New Map...` で新規マップを生成し、`_save_map()` で JSON 保存できることを確認

### 備考

- 今回は STEP 3 を 1 回分に分割した `STEP 3-A` 扱い
- 未着手: Rect / Bucket / Select / Eraser 専用モード、Undo/Redo のマップ専用コマンド、パン、グリッド切替、サイドパネル高度化、レイヤー、ミニマップ、イベント配置
- 次の map 系タスク候補は `STEP 3-B` または `STEP 4`

## 2026-04-06 - gui_editor 復旧: ドキュメント差分確認

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `documents/tutorial/007_gui_editor_manual.md`, `documents/history/works.md`

### 概要

`documents/tutorial/007_gui_editor_manual.md` が Map Editor 実装済み前提の説明になっていたため、2026-04-06 時点の実装状態に合わせて注記を追加しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| 実装状況注記 | `Text Editor` / `Character Editor` は実装済み、`Map Editor` は未実装である旨を明記 |
| モード切替説明 | `Mode > Character Editor` を追記し、`Map Editor` 選択時は警告後に `Text Editor` へ戻ることを追記 |
| 共通操作補正 | `Ctrl+S` の保存対象と `F5` の対象を現行実装（text + characters）に合わせて修正 |
| Map 節注記 | Map Editor の画面構成説明が「実装後の想定」であることを明記 |

### 確認内容

- `tools/gui_editor.py` の現状挙動と説明文の上位セクションが一致することを確認
- character モード切替が動作し、map モードは未実装警告で戻ることを再確認

### 備考

- `documents/plan/017_gui_editor_recovery_steps.md` 上の `STEP 7` は「全STEP完了後」前提のため、今回は最終完了扱いではなく現状差分の明確化のみ実施
- Map Editor の本文詳細セクションは、STEP 3/4 完了後に最終状態へ更新が必要

## 2026-04-06 - gui_editor 復旧: STEP 6 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/compiler.py`, `tools/compiler.py.bak_step6`, `documents/history/works.md`

### 概要

`tools/compiler.py` の character コンパイル処理を STEP 6 として整理し直し、`data/characters/*.json` の読み込み、必須項目バリデーション、マージ、gzip 出力までを仕様どおり単独で完了させました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/compiler.py` を `tools/compiler.py.bak_step6` として退避 |
| 文字化け修正 | character 関連の docstring / メッセージの崩れた文言を整理 |
| validation 強化 | `graphics.face/walk/battle.image`, `selection_id`, `base_stats`, `growth_rates.stats`, `physical_skills`, `magic_skills` の必須キーと整数型を検証 |
| helper 追加 | 整数辞書の必須項目確認用 `_require_int_dict()` を追加 |
| compile 維持 | `main()` から `compile_text()` と `compile_characters()` を順次呼び出す流れを維持 |

### 確認内容

- `py_compile` で `tools/compiler.py` の構文が通ることを確認
- `.venv/Scripts/python tools/compiler.py` で text + characters の両方が正常にコンパイルされることを確認
- 一時的に不正な character JSON を作成し、`growth_rates.stats.hp` 欠落時に validation error で終了することを確認
- `data/compiled/characters_all.bin` が生成されることを確認

### 備考

- STEP 5 の GUI 側保存形式と整合する validation に揃えた
- 依存関係上、Codex 担当の次の残タスクは全体完了後の `STEP 7`

## 2026-04-06 - gui_editor 復旧: STEP 5 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step5`, `documents/history/works.md`

### 概要

`tools/gui_editor.py` に `CharacterEditor` と character モード統合を追加し、`data/characters/*.json` を GUI 上で読み込み・編集・保存できる状態まで復旧しました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step5` として退避 |
| CharacterEditor 実装 | 基本情報、グラフィック、基礎ステータス、成長率（ステータス/物理スキル/魔術スキル）の編集フォームを追加 |
| グラフィックプレビュー | `assets/images/sprite/` の画像と `selection_id` から 32x32 の切り出しプレビューを表示 |
| モード統合 | `_switch_mode("character")`、`_load_char_files()`、character 用ツリー構築、選択反映を追加 |
| 保存対応 | `_save_char_files()` を実装し、character モードの `Ctrl+S` と終了時保存に対応 |
| ID 操作対応 | `_new_char_file()`、`_add_char_id()`、`_delete_char_id()`、`_rename_char_id()` を追加 |
| Undo/Redo 統合 | 既存 `EditCommand` / `RenameCommand` を character ストアでも使えるよう store 分岐を追加 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で character モードへ切り替え、`default.json > char_hero` を選択して `CharacterEditor` が開くことを確認
- フィールド編集、新規 character file 追加、character ID の追加/リネーム/削除、保存処理が例外なく通ることを確認
- text モードへ戻して既存のツリー読込が維持されることを確認
- `tools/compiler.py` 実行で text + characters の両方がコンパイル成功することを確認

### 備考

- `default.json` の既存文字列には文字化けした値が含まれているが、今回の STEP では構造復旧のみを実施
- 依存関係上の次ステップ候補は `STEP 6` または `STEP 3`

## 2026-04-06 - gui_editor 復旧: STEP 2 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step2`, `documents/history/works.md`

### 概要

`tools/gui_editor.py` にモード切替の骨組みを追加し、`Text Editor / Map Editor / Character Editor` の3項目をメニューから選べる状態にしました。`map` と `character` はまだ未実装として警告を出し、安全に `text` モードへ戻します。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step2` として退避 |
| モード状態追加 | `self._mode`, `self._map_file_data`, `self._current_map_path`, `self._char_file_data` を追加 |
| Mode メニュー | `QActionGroup` で排他的な `Text Editor / Map Editor / Character Editor` を追加 |
| モード切替雛形 | `_switch_mode(mode)` を追加し、未実装モード選択時は警告表示後に `text` を維持 |
| 保存分岐 | `Ctrl+S` の接続先を `_save_current()` に変更し、モード別保存の分岐を追加 |
| 未実装スタブ | `_save_map()` / `_save_char_files()` の雛形を追加し、現時点ではステータス表示のみ行う |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で `Map Editor` / `Character Editor` 選択時に警告を出しつつ `_mode` が `text` のまま維持されることを確認
- `_save_current()` が `text / map / character` の全分岐で例外なく実行できることを確認

### 備考

- マップ・キャラクター実体は未実装のまま。依存関係上の次ステップは `STEP 3` または `STEP 5`

## 2026-04-06 - gui_editor 復旧: STEP 1 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py`, `tools/gui_editor.py.bak_step1`, `documents/history/works.md`

### 概要

`tools/gui_editor.py` に `events` カテゴリと `EventEditor` を追加し、既存のテキストエディタ構成のままイベントコマンド一覧の編集を可能にしました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step1` として退避 |
| カテゴリ追加 | `CATEGORY_LABELS` / `CATEGORIES` に `events` を追加し、ツリーに `Events` が表示されるよう更新 |
| EventEditor 実装 | コマンド一覧、追加/削除、ドラッグ並べ替え、コマンド種別変更、動的フィールド編集を実装 |
| EditorWindow 統合 | `_stack`、`_on_tree_selected`、Undo/Redo 再描画、ID追加デフォルト値に `events` 分岐を追加 |
| 検索対応 | `events` の `cmd` 名と文字列引数を検索対象に追加 |
| プレビュー補助 | `PreviewPanel` にイベントコマンド概要の簡易表示を追加 |

### 確認内容

- `py_compile` で `tools/gui_editor.py` の構文が通ることを確認
- オフスクリーン起動で `demo.json > Events > ev_opening_demo` を選択し、`EventEditor` が開いて 17 コマンド読めることを確認

### 備考

- Mode メニューや Character/Map モードの基盤は未着手。依存関係上の次ステップは `STEP 2`

## 2026-04-06 - gui_editor 復旧: STEP 0 実施

**ブランチ**: 現在の作業ツリー  
**担当**: Codex  
**変更ファイル**: `tools/gui_editor.py.bak_step0`, `documents/history/works.md`

### 概要

`documents/plan/017_gui_editor_recovery_steps.md` に従い、復旧作業の開始前準備として `tools/gui_editor.py` の退避コピー作成と起動確認を行いました。

### 変更内容

| 項目 | 内容 |
|------|------|
| バックアップ作成 | `tools/gui_editor.py` を `tools/gui_editor.py.bak_step0` として退避 |
| 起動確認 | `QT_QPA_PLATFORM=offscreen` で `tools/gui_editor.py` を起動し、4秒間クラッシュせず稼働継続することを確認 |
| 現状確認 | 現在の `tools/gui_editor.py` はテキストエディタ構成で、STEP 2/5 のモード拡張は未適用であることを確認 |

### 備考

- PowerShell 実行時にプロファイル由来の `InvalidOperation` ノイズは出るが、バックアップ作成と起動確認自体は成功
- 次の着手候補は依存関係上 `STEP 1` または、別実装がすでに入っているかを整理した上での `STEP 2` 以降の再判定

---

## 2026-04-05 — キャラクターエディットモードの追加

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`, `tools/compiler.py`, `data/characters/default.json`

### 概要

GUIエディタに3つ目のモード「Character Editor」を追加しました。Mode メニューから切り替えてキャラクターの各種パラメータを編集できます。

### 変更内容

| 項目 | 内容 |
|------|------|
| CharacterEditor クラス | 基本情報・グラフィック・基礎ステータス・成長率（ステータス/物理スキル/魔術スキル）の編集フォーム |
| モード切替 | `_switch_mode` を2モードから3モード対応に拡張 |
| データ管理 | `data/characters/` ディレクトリに JSON ファイルとして保存・読込 |
| 画像プレビュー | スプライト画像から32x32の切り出しプレビュー表示 |
| コンパイラ | `compiler.py` にキャラクターデータのバリデーション・マージ・圧縮を追加 |
| Undo/Redo | 既存の QUndoStack を利用したキャラクター編集の Undo/Redo 対応 |
| 追加/削除/リネーム | キャラクターIDの追加・削除・リネーム機能 |

### キャラクターデータ構造

- 名前（文字列）、初期職業ID、性格ID
- グラフィック（顔/歩行/戦闘 × 画像ファイル名 + 選択ID）
- 基礎ステータス（HP/MP/STR/VIT/INT/MND/LUK）
- 成長率 - ステータス（HP/MP/STR/VIT/INT/MND/LUK）
- 成長率 - 物理スキル（短剣/剣/刀/斧/槍/棍/爪/弓）
- 成長率 - 魔術スキル（回復/元素/強化/弱体）

---

## 2026-04-05 — ツールバー: 消しゴムとツールボタンの排他制御

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`

### 概要

ペンツールが選択中に消しゴムをクリックすると両方がアクティブ（青枠）になる問題を修正しました。

### 変更内容

`ToolIconBar` の以下 3 メソッドを修正し、ツールボタンと消しゴムボタンが互いに排他になるようにしました。

| メソッド | 変更内容 |
|---|---|
| `set_active_tool(tool)` | ツールボタン選択時に消しゴムボタンを必ず OFF にする |
| `set_erase_mode(enabled)` | 消しゴム ON 時にすべてのツールボタンを unchecked にする |
| `_on_eraser()` | 消しゴム ON 時にすべてのツールボタンを unchecked にする |

これによりキーボードショートカット（B/R/F/S/E）経由でも UI 上の選択状態が正しく排他になります。

---

## 2026-04-05 — マップエディタ: 選択範囲修正 & ショートカット変更

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`

### 概要

選択範囲ツールの視覚的問題を修正し、ペイントツールのキーボードショートカットを整理しました。

---

### 1. 選択範囲の修正

**背景**  
選択した矩形とは別に、マップ全体にアクティブレイヤーを示す白い破線枠が常時描画されており、選択結果が分かりにくかった。

**変更内容**

| 修正内容 | 詳細 |
|---|---|
| 余計な背景色変化を除去 | `paintEvent` からマップ全体を囲む破線枠（白・半透明・DashLine）を削除 |
| ツール切り替えで選択解除 | `set_tool` でselect以外のツールに切り替えると `_selection_start/_end` をリセット |
| Delete キーで範囲消去 | 選択中に Delete → 選択範囲内のタイルを全て 0 に置換（Undo対応） |

---

### 2. キーボードショートカット変更

| ツール | 旧キー | 新キー |
|---|---|---|
| Pen | `P` | `B` |
| Rect | `R` | `R` (変更なし) |
| Bucket | `B` | `F` |
| Select | `S` | `S` (変更なし) |
| Eraser Mode | `E` | `E` (変更なし) |

- `ToolIconBar` のツールチップも新ショートカットに合わせて更新（`Pen (B)`, `Bucket (F)`）

---

## 2026-04-04 — マップエディタ: 消去モード追加 & ツールアイコンバー実装

**ブランチ**: `task/asset-loading-support`  
**担当**: Claude Code  
**変更ファイル**: `tools/gui_editor.py`

### 概要

マップエディタのペイントツール周りを 2 点改修しました。

---

### 1. 消去モード (Eraser Mode)

**背景**  
従来の「消去」は右クリックのみに対応していた。Rect・Bucket ツール使用時にも一括消去できるよう、明示的な消去モードを追加。

**変更内容**

- `MapCanvas` に `_erase_mode` フラグを追加
- `set_erase_mode(enabled: bool)` メソッドを追加
- `_paint_at`、`_paint_rect`、`_paint_bucket` の 3 メソッドで `self._erasing or self._erase_mode` を参照するよう変更
  - 消去モード ON 時: 選択タイルに関わらず、全ツールがタイル 0 (空タイル) で塗る
  - 右クリックによる一時消去 (`_erasing`) は引き続き動作

**ショートカット**

| キー | 動作 |
|---|---|
| `E` | 消去モードのトグル |
| `P` / `R` / `B` / `S` | 各ツールの切り替え（変わらず） |
| 右クリックドラッグ | 一時的な消去（変わらず） |

---

### 2. ツールアイコンバー (ToolIconBar)

**背景**  
従来の「Pen / Select / Rect / Bucket」テキストボタンは横並びで幅を取り、ツール数が増えると破綻する設計だった。ペイントツールライクなアイコン縦並びに刷新。

**変更内容**

- `_make_tool_icon(tool_id)`: 各ツールの 24px アイコン (QIcon) を QPainter で生成するユーティリティ関数を追加
- `ToolIconButton` クラス: チェック可能な 36×36px アイコンボタン。選択中は青くハイライト
- `ToolIconBar` クラス: `MapCanvas` の右端にオーバーレイ表示される縦型ツールバー
  - ツール 4 種 (Pen / Rect / Bucket / Select) + セパレーター + Eraser Mode トグルの構成
  - `resizeEvent` / `showEvent` で常にキャンバス右端上部に自動再配置
  - シグナル: `tool_changed(str)`, `erase_mode_changed(bool)`
- `MapCanvas.set_tool_bar(bar)` / `resizeEvent` / `showEvent` を追加
- `MapPropertyPanel` からテキストツールボタン・消しゴムボタン・`tool_changed` シグナル・`set_active_tool`・`_on_eraser` を削除
- `EditorWindow._setup_ui` で `ToolIconBar` を生成し各シグナルを接続

**UI 上の変化**

- 右サイドパネル内のツールボタン行が消え、`Map Properties` がスッキリした
- キャンバス右端に半透明の縦型アイコンバーが表示される
- 消しゴムアイコンがアクティブ（青枠）になると消去モード中であることが一目でわかる

---
