# 引継ぎ資料: GUIエディタ機能拡張（Phase 4-6 完了）

## 完了済み作業

### Phase 1: データ基盤
- テキストデータを JSON に分離 (`data/text/demo.json`)
- `tools/compiler.py` で JSON → gzip 圧縮バイナリ (`text_all.bin`)
- `src/data/text_manager.py` (TextManager) でゲーム側からロード

### Phase 2: Pyxel プレビューア
- `tools/editor_app.py` — Pyxel ベースのテキストビューア
- ゲーム内 UI コンポーネントで実際の見た目を確認

### Phase 3: テキストファイル分割対応
- `demo.json` に `file_id` フィールド追加
- `compiler.py` を複数ファイルマージ対応（ID 重複チェック付き）

### Phase 4: PySide6 GUIエディタ 基本機能
- `tools/gui_editor.py` — PySide6 ベースのテキストエディタ
- ファイルツリー（3階層: ファイル → カテゴリ → ID）
- カテゴリ別編集フォーム（Messages / Selections / Telops）
- 保存 (Ctrl+S)、コンパイル (F5)、リロード (F9)
- ID追加・削除 (Edit メニュー)
- 未保存時の確認ダイアログ

### Phase 5: プレビューパネル
- `PreviewPanel` クラス — QPainter で 480x270 ゲーム画面を再現描画
- 3ペイン構成（ツリー | エディタ | プレビュー）
- メッセージウィンドウ: 名前ウィンドウ + 半透明背景 + テキスト3行 + 送りアイコン + ページ表示
- 選択肢ウィンドウ: カーソル(>) + 自動サイズ + desc 対応 + 半透明対応
- テロップ: 中央揃え + 行数超過時の自動縮小 + scroll_speed 表示
- ゲーム用フォント (`madoufmg.ttf`) を QFontDatabase で読み込み
- 編集内容のリアルタイムプレビュー更新

### Phase 6: Undo/Redo + テキスト検索
- `EditCommand` (QUndoCommand) + `QUndoStack` によるコマンドパターン
  - in-place 更新で参照維持（`clear()` + `extend()`/`update()`）
  - 500ms デバウンスで連続入力を1コマンドにまとめる
  - `_pushing_undo` / `_closing` フラグで再帰・クラッシュ防止
- テキスト検索 (Ctrl+F)
  - 上部に検索バー（トグル表示）
  - 全ファイル × 全カテゴリ横断のインクリメンタル検索
  - ID名 + テキスト内容が検索対象
  - Enter / `<` `>` ボタンで結果間ナビゲーション

## 現在のブランチ
- `tutorial/text_file_external_03`（未コミット変更あり）

## 関連ドキュメント
- `documents/plan/007_text_file_external.md` — 元の要件定義
- `documents/plan/007_text_file_external_design.md` — 実装計画（Phase 1-4）
- `documents/plan/007_text_file_external_guide.md` — 運用ガイド + 今後の改善提案
- `documents/plan/008_gui_editor_plan.md` — GUIエディタ計画書（PySide6選定理由等）
- `documents/plan/010_editor_preview_undo_search.md` — Phase 5-6 の実装詳細・設計判断

## エディタの現在の操作一覧

| 操作 | ショートカット | 状態 |
|------|------------|------|
| 保存 | Ctrl+S | 実装済み |
| コンパイル | F5 | 実装済み |
| リロード | F9 | 実装済み |
| 終了 | Ctrl+Q | 実装済み |
| Undo | Ctrl+Z | 実装済み |
| Redo | Ctrl+Y | 実装済み |
| ID追加 | Edit → Add ID | 実装済み |
| ID削除 | Delete キー | 実装済み |
| 検索 | Ctrl+F | 実装済み |
| IDリネーム | — | **未実装** |
| ファイル間ID移動 | — | **未実装** |
| ゲーム起動 | F6 | **未実装** |
| バリデーション | — | **未実装** |

## 今後の改善候補（優先順）

### 優先度: 高

1. **IDリネーム機能**
   - 現在は追加・削除のみ。リネームは「削除→追加」で代替しているが不便
   - 右クリックメニューに「Rename ID」を追加
   - ゲームコード側の参照更新は手動（将来的にはgrep連携も検討）

2. **バリデーション強化**
   - 1行あたりの文字数チェック（MessageWindowは3行×約28文字が上限目安）
   - 未使用ID検出（`src/` 内をgrep して参照されていないIDを警告）
   - コンパイル時 or ステータスバーに警告表示

### 優先度: 中

3. **プレビュー精度向上**
   - 現在の QPainter 描画はゲームと同一フォントを使っているが、テキスト幅の計算方法が Pyxel と異なるため微妙にズレる
   - Pyxel の `Font.text_width()` と QPainter の `QFontMetrics.horizontalAdvance()` で差異がある
   - 文字数超過の視覚的な警告（赤枠等）を追加するとバリデーションと連携できる

4. **ファイル間ID移動**
   - ドラッグ&ドロップでIDを別ファイルに移動
   - 右クリック → 「Move to...」でファイル選択

5. **右クリックコンテキストメニュー**
   - ツリー上で右クリック → Add / Delete / Rename / Copy / Move to
   - 現在は Edit メニューからのみ

6. **多言語対応（i18n）**
   - `data/text/ja/`, `data/text/en/` の言語ディレクトリ構成
   - TextManager で言語切り替え
   - エディタで言語を並べて比較編集

### 優先度: 低

7. **差分コンパイル**（タイムスタンプ比較）
8. **エクスポート/インポート**（CSV/TSV for 翻訳）
9. **ゲーム制作ツール統合**（QDockWidget でイベント/マップ/スプライトエディタ）

## 技術スタック
- Python 3.x + Pyxel（ゲーム本体）
- PySide6-Essentials 6.11.0（GUIエディタ）
- Pillow（スクリーンショットハーネス）
- 仮想環境: `.venv/`

## 既知の注意点

### QUndoStack の参照切断問題
`EditCommand` でデータを差し替える際は **in-place 更新**（`clear()` + `extend()`/`update()`）が必須。オブジェクト参照を丸ごと置き換えるとエディタの `_data` 参照が切断され、2回目以降の編集が反映されなくなる。詳細は `010_editor_preview_undo_search.md` を参照。

### シャットダウン時のシグナル
`QUndoStack.clear()` は `indexChanged` を発火する。ウィンドウ破棄後にこれが走ると `RuntimeError: Internal C++ object already deleted` が発生する。`_closing` フラグで防止済み。

### 運用ガイドの更新
`007_text_file_external_guide.md` の「画面構成」セクションは2ペイン時代の記述のままになっている。3ペイン + 検索バーの内容に更新が必要。
