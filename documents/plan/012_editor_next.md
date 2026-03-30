このプロジェクトのテキスト外部ファイル化 + エディタツールの続きの作業について相談したいです。

## 現状
documents/plan/011_handoff.md に引継ぎ資料があるので最初に読んでください。
関連ドキュメントは以下です:
- documents/plan/007_text_file_external_guide.md（運用ガイド）
- documents/plan/008_gui_editor_plan.md（GUIエディタ計画書）
- documents/plan/010_editor_preview_undo_search.md（プレビュー・Undo・検索の実装詳細）

## ブランチ
tutorial/text_file_external_03（Phase 1-6 完了済み）

## 完了済みの機能
- テキストデータ JSON 管理 + コンパイラ + ゲーム側ローダー
- PySide6 GUIエディタ（ファイルツリー / カテゴリ別編集フォーム / 保存 / コンパイル / リロード / ID追加・削除）
- QPainter プレビューパネル（メッセージ / 選択肢 / テロップの再現描画 + リアルタイム更新）
- Undo/Redo（QUndoStack + EditCommand）
- テキスト検索（Ctrl+F インクリメンタル検索）

## エディタの次の機能追加・改修メモ

以下の候補から、次に取り組む機能・改善について相談させてください。
011_handoff.md の「今後の改善候補」セクションに優先度付きリストがあります。

主な候補:
1. IDリネーム機能
2. バリデーション強化（文字数チェック、未使用ID検出）
3. プレビュー精度向上
4. ファイル間ID移動
5. 右クリックコンテキストメニュー
6. 運用ガイド (007) の更新（3ペイン構成の反映）
7. その他やりたいこと

