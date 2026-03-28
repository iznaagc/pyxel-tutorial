# 作業再開ドキュメント: ウィンドウシステム

## ブランチ

`tutorial/window_base_002`

## 完了済み作業

### 1. BaseWindowクラスの作成（完了）
- `src/ui/window.py` をリファクタリング
- 共通機能（位置・サイズ・枠線有無・半透明）を `BaseWindow` に抽出
- `pyxel.dither()` で半透明背景を実現

### 2. OverlayWindowクラスの作成（完了）
- 既存 `Window` の機能を `BaseWindow` を継承した `OverlayWindow` に移行
- `Window = OverlayWindow` で後方互換を維持
- `src/scenes/title.py` のimportを `OverlayWindow` に変更済み

### 3. MessageWindowクラスの作成（完了）
- `src/ui/message_window.py` を新規作成
- 実装済み機能:
  - 1文字ずつテキスト表示（速度: FAST/NORMAL/SLOW）
  - 決定キー（Enter/Space）で即時表示完了
  - キャラクター名ウィンドウ（左上に表示）
  - 顔グラフィック対応（左側に `pyxel.blt()` で表示）
  - メッセージキュー（複数メッセージ連続表示）
  - 自動送り対応（`auto: True`）
  - メッセージ送りアイコン（点滅+上下アニメーション）
  - 枠線有無・半透明背景の選択

### 4. GameSceneにデモを組み込み（完了）
- `src/scenes/game.py` にMessageWindowのテストデモを実装
- Enterキーでデモ開始、4つのメッセージを順番に表示
- ユニットテスト（import確認・ロジックテスト）は通過済み

### 5. チュートリアルドキュメント（完了）
- `documents/tutorial/002_window_system.md` を作成済み

### 6. pyxel-mcp設定ファイル（完了）
- `.mcp.json` をプロジェクトルートに作成済み

## 未完了作業（再開後にやること）

### A. pyxel-mcpによる視覚的動作確認
- `run_and_capture` でタイトル画面の表示を確認
- `play_and_capture` でゲーム画面に遷移し、Enterキーでメッセージウィンドウのデモを起動
- 以下を視覚確認する:
  - ウィンドウの位置・サイズ（画面下部 x=8, y=192, w=240, h=56）
  - 半透明背景の表示（dither効果）
  - 名前ウィンドウの表示位置（メインウィンドウ左上）
  - テキストの1文字ずつ表示
  - メッセージ送りアイコンのアニメーション
  - 複数メッセージの連続表示
  - 自動送りメッセージの動作

### B. 問題の起票と修正
- 視覚確認で問題があれば issue としてドキュメントに記録
- 解決策を記載し、コード修正後に再確認
- 結果もドキュメントに記録

### C. MCP利用手順ドキュメントの作成
- pyxel-mcpの設定方法・使い方をドキュメントにまとめる
- 保存先: `documents/tutorial/` に別ファイルとして保存

## 変更ファイル一覧

| ファイル | 状態 | 内容 |
|---|---|---|
| `src/ui/window.py` | 変更 | BaseWindow + OverlayWindow にリファクタリング |
| `src/ui/message_window.py` | 新規 | MessageWindowクラス |
| `src/scenes/title.py` | 変更 | import を OverlayWindow に変更 |
| `src/scenes/game.py` | 変更 | MessageWindowデモを追加 |
| `documents/tutorial/002_window_system.md` | 新規 | ウィンドウシステムのドキュメント |
| `.mcp.json` | 新規 | pyxel-mcp MCPサーバー設定 |
| `documents/plan/create_window_system.md` | 既存 | 元の要望書 |

## 再開時の指示

以下のドキュメントを読んでから未完了作業（A〜C）を実行してください:
1. `documents/plan/resume_window_system.md`（このファイル）
2. `documents/plan/create_window_system.md`（元の要望）
3. `src/ui/message_window.py`（実装コード）
4. `src/scenes/game.py`（デモコード）

pyxel-mcpのツール（`run_and_capture`, `play_and_capture` 等）を使って視覚確認を行い、問題があれば修正してドキュメントに記録してください。
