# 引継ぎ資料: テキスト外部ファイル化 + エディタツール

## 完了済み作業

### Phase 1: データ基盤
- テキストデータをゲームコード（game.py）から分離して JSON 管理
- `data/text/demo.json` にメッセージ/選択肢/テロップを集約
- `tools/compiler.py` で JSON → gzip圧縮バイナリ（text_all.bin）
- `src/data/text_manager.py` の TextManager でゲーム側からロード
- `src/config.py` に init_text_manager() 追加、`src/app.py` で初期化

### Phase 2: Pyxelプレビューア
- `tools/editor_app.py` — Pyxel ベースのテキストビューア
- `tools/editor_config.py` — 画面サイズ等の設定ファイル
- `tools/panels/` — ビューア用パネル（text_panel, preview_panel）
- ゲーム内UIコンポーネントでプレビュー表示

### Phase 3: テキストファイル分割対応
- `demo_text.json` → `demo.json` にリネーム、`file_id` フィールド追加
- compiler.py を複数ファイルマージ対応に改修（ID重複チェック付き）
- 出力先を `text_all.bin` に統一

### Phase 4: PySide6 GUIエディタ
- `tools/gui_editor.py` — PySide6 ベースの本格テキストエディタ
- ファイルツリー（3階層: ファイル→カテゴリ→ID）
- カテゴリ別編集フォーム（Messages/Selections/Telops）
- 保存（Ctrl+S）、コンパイル（F5）、リロード（F9）
- ID追加・削除（Editメニュー）
- 未保存時の確認ダイアログ

## 現在のブランチ
- `tutorial/text_file_external_03`（コミット済み、working tree clean）

## 関連ドキュメント
- `documents/plan/007_text_file_external.md` — 元の要件定義
- `documents/plan/007_text_file_external_design.md` — 実装計画（Phase 1-4 完了）
- `documents/plan/007_text_file_external_guide.md` — 運用ガイド + 今後の改善提案
- `documents/plan/008_gui_editor_plan.md` — GUIエディタ計画書（PySide6選定理由等）

## 次にやるべきこと（優先順）

1. **GUIエディタ: プレビューパネル追加** — QPainter でゲームUI再現描画、編集とリアルタイム連動
2. **GUIエディタ: Undo/Redo** — QUndoStack によるコマンドパターン
3. **GUIエディタ: テキスト検索（Ctrl+F）** — ID/テキスト内容のインクリメンタル検索
4. **IDリネーム機能** — 現在は追加・削除のみ
5. **バリデーション強化** — 文字数チェック、未使用ID検出

## 技術スタック
- Python 3.x + Pyxel（ゲーム本体）
- PySide6-Essentials 6.11.0（GUIエディタ）
- Pillow（スクリーンショットハーネス）
- 仮想環境: `.venv/`
