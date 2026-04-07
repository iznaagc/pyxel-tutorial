# 015 Map Editor レビュー依頼

## 目的

`documents/plan/015_mapeditor_spec_and_next.md` に基づいて実装したマップエディタ拡張について、コードレビューをお願いします。  
主目的は以下です。

- バグの発見
- 回帰リスクの確認
- Undo/Redo と UI 状態同期の不整合確認
- PySide6 の signal-slot や再描画タイミングの問題確認
- 保守性と責務分離の観点からの改善点抽出

## このレビューで読めばよいファイル

まず以下を読んでください。

1. `documents/plan/015_mapeditor_spec_and_next.md`
2. `documents/report/015_mapeditor_implementation_report.md`
3. `tools/gui_editor.py`

補助的に必要なら以下も見てください。

- `data/text/demo.json`
- `data/maps/DebugMap.json`
- `screenshots/` 配下の関連画像

## 前提

- 仕様書にあるタスク A から J までをすべて完了済みです
- 残タスクはありません
- 実装の大半は `tools/gui_editor.py` に入っています
- 機能追加後の確認用スクリーンショットは `screenshots/` に保存済みです
- 実装内容の要約は `documents/report/015_mapeditor_implementation_report.md` にあります

## 対象機能

今回のレビュー対象は、仕様書 8.1 から 8.5 に対応する以下の機能です。

### タスク A: タイルセットプレビューの改善

- タイルセットパレットのズーム
- ホバー時のタイル情報表示
- 選択タイル拡大プレビュー

### タスク B: 複数タイル選択

- タイルセットパレットでの矩形選択
- 複数タイルのスタンプ描画

### タスク C: タイルセット設定の永続化

- 外部タイルセット画像の `assets/tilesets/` への自動コピー
- マップ JSON への相対パス保存
- 未設定 / 未検出時の警告表示

### タスク D: 矩形塗りつぶしツール

- `pen / rect / bucket` ツール基盤
- 矩形プレビュー
- 矩形確定塗り

### タスク E: バケツツール

- 4 方向フラッドフィル
- 安全上限 10000 タイル

### タスク F: コピー / ペースト

- 矩形選択
- コピー
- 貼り付けモード
- 貼り付けプレビュー

### タスク G: レイヤー UI とレイヤー切替

- 複数レイヤーデータ
- レイヤー一覧 UI
- 可視 / 非可視
- アクティブレイヤー切替
- レイヤー追加 / 削除 / 順序変更

### タスク H: ミニマップ

- マップ全体の縮小表示
- 現在ビューポート表示
- クリックジャンプ

### タスク I: タイル通行判定

- `passability` データ
- タイルごとの通行可否 UI
- キャンバス上の × オーバーレイ

### タスク J: マップ上のイベント配置

- `events` データ
- キャンバス上のイベントアイコン表示
- 空きマスへのイベント配置
- 既存イベントのダブルクリックで `EventEditor` を開く導線

## 主な編集ファイル

### 1. `tools/gui_editor.py`

今回の中心実装ファイルです。以下の責務が追加または拡張されています。

- `TilesetPalette`
- `MapCanvas`
- `MapPropertyPanel`
- `LayerPanel`
- `MinimapWidget`
- `MapSidePanel`
- `EditorWindow`
- マップ用データ初期化と Undo コマンド

### 2. `documents/report/015_mapeditor_implementation_report.md`

タスクごとの変更内容、確認内容、関連スクリーンショットをまとめた報告書です。

### 3. 補助ファイル

- `assets/tilesets/external_tileset_source.png`
- `screenshots/*.png`

## レビュー観点

以下の観点で確認してください。

### 1. 仕様適合性

- 各タスク A から J が仕様どおり実装されているか
- 仕様に対して不足や逸脱がないか

### 2. バグ・回帰リスク

- 既存のテキスト編集機能に副作用がないか
- マップモードとテキストモードの切替で破綻がないか
- ツール切替、コピー/ペースト、矩形塗り、バケツ、レイヤー切替、イベント配置の相互作用に問題がないか
- タイルセット未設定時やマップ未選択時など、境界条件で壊れないか

### 3. Undo/Redo 整合性

- `PaintTileCommand`
- `ResizeMapCommand`
- マップ編集後の `mark_dirty()` と UI 反映
- Undo/Redo 後に右パネル、キャンバス、レイヤー状態がズレないか
- レイヤー操作、通行判定、イベント配置に Undo 対応漏れがないか

### 4. PySide6 / signal-slot / UI 更新

- signal-slot の接続に危険がないか
- `_updating`、`_pushing_undo` の使い方に問題がないか
- `set_data()`、`update()`、`mark_dirty()` の連携が破綻していないか
- `QInputDialog` やモード切替中の UI 遷移に問題がないか

### 5. データ構造と保存

- マップ JSON の以下の拡張が妥当か
  - `layers`
  - `passability`
  - `events`
- 保存 / 読み込み時の後方互換や欠損データへの対応が十分か

### 6. 保守性

- `tools/gui_editor.py` に責務が集中しすぎていないか
- 直近で分割すべき領域があるか
- 今の段階で最低限やるべき整理があるか

## 特に重点的に見てほしい箇所

### `MapCanvas`

- 描画処理
- 入力処理
- ツール状態管理
- コピー / ペースト
- 矩形塗り
- バケツ
- イベントアイコン描画
- ダブルクリックでのイベント導線

### `EditorWindow`

- テキスト / マップモード切替
- マップ読み込み
- マップ選択時の UI 反映
- イベント配置と `EventEditor` オープン処理
- Undo/Redo 後の同期

### `MapPropertyPanel`

- タイル選択との連動
- ツールボタン
- 通行判定 UI

### `LayerPanel`

- レイヤー一覧 UI
- アクティブレイヤー変更
- 可視切替
- レイヤー順変更

## 期待するレビュー結果の形式

問題がある場合は、重要度順に列挙してください。  
可能なら以下の形式で返してください。

1. 問題の要約
2. 該当ファイルと行番号
3. 現状の挙動
4. なぜ問題か
5. 修正方針

問題が見つからなかった場合も、その旨を明記してください。  
そのうえで以下があれば書いてください。

- 残留リスク
- テスト不足
- 将来的なリファクタ候補

## 参考

- 仕様書: `documents/plan/015_mapeditor_spec_and_next.md`
- 実装報告: `documents/report/015_mapeditor_implementation_report.md`
- 実装本体: `tools/gui_editor.py`
