  このプロジェクトのテキスト外部ファイル化 + エディタツールの続きの作業をしてください。                                                                                                             

  ## 現状
  documents/plan/007_handoff.md に引継ぎ資料があるので最初に読んでください。
  関連ドキュメントは以下です:
  - documents/plan/007_text_file_external_guide.md（運用ガイド + 今後の改善提案）
  - documents/plan/008_gui_editor_plan.md（GUIエディタ計画書）

  ## ブランチ
  tutorial/text_file_external_03（Phase 1-4 完了済み）

  ## 次のタスク
  GUIエディタ（tools/gui_editor.py）に以下の機能を追加してください:

  1. プレビューパネル — 右ペインに QPainter でゲームUIを再現描画。編集内容をリアルタイムでプレビュー。Pyxelパレットカラーを使い、ウィンドウ枠・テキスト・名前ウィンドウを描画する。
  2. Undo/Redo — QUndoStack を使ったコマンドパターン
  3. テキスト検索（Ctrl+F） — ID名やテキスト内容をインクリメンタル検索

  まずは引継ぎ資料と現在のソースコードを確認してから、1番のプレビューパネルから着手してください。