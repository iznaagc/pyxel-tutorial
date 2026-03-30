# AI Agent Instructions

When acting as an AI coding assistant in this repository, strictly abide by the following instructions:

1. **Virtual Environment Enforcement:**
   - ALWAYS activate the virtual environment before installing packages or executing Python scripts.
   - Command to activate (PowerShell): `.\.venv\Scripts\Activate.ps1`
   - Example when installing: `.\.venv\Scripts\Activate.ps1; pip install [package]`
   - Example when running: `.\.venv\Scripts\python.exe src/main.py`

2. **Project Context:**
   - Before suggesting or making major architectural decisions, review `Rule.md` to ensure compliance with project rules.
   - Also review `CLAUDE.md` at the start of work and treat its instructions as part of the repository guidance.
   
3. **Pyxel Specifics & Visual Output (using Pyxel-MCP):**
   - Use the `pyxel-mcp` tools (such as `run_and_capture`, `inspect_sprite`, `play_and_capture`, `inspect_screen`, etc.) to visually verify your code and troubleshoot layout/color issues.
   - **Always verify visually.** Pyxel's coordinate system, color indices, and sprite layouts often produce unexpected results. Do not assume your layout code works until you inspect a screenshot or screen output.
   - You can capture multiple frames or simulate input using `play_and_capture` or `capture_frames`. Always double check the Pyxel SKILL docs for syntax.
   - When suggesting new graphics, provide the exact coordinates or parameters to use with Pyxel drawing functions, and iterate based on visual/audio feedback.

4. **スクリーンショットの保存（恒久ルール）:**
   - 機能の追加や改修を行い、MCPを通して画面のチェックをする際には **都度スクリーンショットを `screenshots/` ディレクトリに保存する**。
   - 一時ディレクトリ（/tmp等）には残さず、必ずプロジェクト内に保存する。
   - ファイル名は内容がわかる英語の命名にする（例: `select_window_yes_no.png`, `msg_japanese_basic.png`）。
   - これは一時的な確認ではなく、変更履歴としての記録を兼ねる恒久的な作業である。

5. **タスク管理ルール（GitHub Issues ベース）:**
   - 詳細は `documents/plan/000_works_task_management.md` を参照すること
   - Codex / Claude Code など `.mcp.json` を読むAIでは、**MCP設定変更や `GITHUB_PAT` 変更後にAIセッション再起動が必要** な場合がある
   - GitHub MCP が使えない場合は、まず `tools/check_github_task_env.ps1` で診断し、その結果に従って認証を復旧する
   - **作業開始前に必ず確認**:
     - `gh issue list --state open` で未クローズのIssue一覧を確認する
     - `gh pr list --state open` で作業中のPR一覧を確認する
     - 他のAIが着手宣言済みのIssueには手を出さない
   - **着手時**:
     - Issueにコメントで着手宣言する（例: `🤖 **Claude Code** が着手します（ブランチ: task/15-xxx）`）
     - ブランチを `task/<Issue番号>-簡潔な説明` の形式で作成する
     - 他の作業中タスクと変更対象ファイルが重なる場合は人間に相談する
   - **完了時**:
     - PRを作成し、本文に `Closes #Issue番号` を含める
     - 実装内容の解説とスクリーンショット（該当する場合）をPRに記載する
   - **コンテキスト制限時**:
     - 進捗をコミット＆プッシュし、Issueにハンドオフコメントを残す
   - **mainブランチへの直接コミットは禁止**
