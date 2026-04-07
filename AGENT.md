# AI Agent Instructions

**最初にこのファイルを最後まで読み、すべてのルールに従うこと。**

## AI名一覧

作業時はこの名前を使って着手宣言・PRコメント等を行うこと:

| AIツール | 表示名 |
|---|---|
| Claude Code | `Claude Code` |
| Codex (OpenAI) | `Codex` |
| Antigravity (Gemini) | `Antigravity` |

---

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
   - **Codex での gh CLI 利用時の注意**: デフォルトの `gh auth` トークンが無効な場合がある。その場合は `$env:GH_TOKEN = $env:GITHUB_PAT` を設定してから `gh` コマンドを実行すること（PowerShell の場合）。bash の場合は `GH_TOKEN=$GITHUB_PAT gh ...` の形式で実行する
   - **作業開始前に必ず確認**:
     - `gh issue list --state open` で未クローズのIssue一覧を確認する
     - `gh pr list --state open` で作業中のPR一覧を確認する
     - 他のAIが着手宣言済みのIssueには手を出さない
   - **ブランチ運用**:
     - ベースブランチは `develop`（main ではない）
     - 機能ブランチは `develop` から切り、PRも `develop` に向けて出す
     - `main` への反映は `develop` からのマージで行う（人間が判断）
     - **main / develop ブランチへの直接コミットは禁止**
   - **着手時**:
     - Issueにコメントで着手宣言する（例: `🤖 **Claude Code** が着手します（ブランチ: task/15-xxx）`）
     - ブランチを `task/<Issue番号>-簡潔な説明` の形式で `develop` から作成する
     - 他の作業中タスクと変更対象ファイルが重なる場合は人間に相談する
   - **完了時**:
     - PRを `develop` ブランチに向けて作成し、本文に `Closes #Issue番号` を含める
     - 実装内容の解説とスクリーンショット（該当する場合）をPRに記載する
   - **PRレビュールール**:
     - PRは **作成者以外のAI** が Approve しないとマージできない
     - 例: Claude Code が作成 → Codex or Antigravity が Approve
     - 例: Codex が作成 → Claude Code or Antigravity が Approve
     - レビュー時は `gh pr review <番号> --approve --body "レビューコメント"` を使用
     - レビュー観点: 動作確認、コード品質、既存機能への影響、AGENT.md ルール準拠
   - **同一アカウント制約の例外運用**:
     - 全AIが同一GitHubアカウントで操作する場合、GitHub APIの仕様上 `gh pr review --approve` は「自分のPRを自分でApproveできない」エラーになる
     - この場合、レビュー担当AIが **Issue または PRへのコメントでレビュー結果（LGTM等）を投稿** すれば、正式な Approve と同等とみなす
     - **マージ作業は Claude Code のみが行う**（`gh pr merge <番号> --merge --admin` を使用し、マージコメントにレビュー経緯を記載する）
     - Codex / Antigravity はレビューまでを担当し、マージは実行しないこと
   - **PRレビュー依頼フロー**:
     1. PR作成後、Issue にコメントでレビュー依頼を残す:
        `gh issue comment <番号> --body "PR #<PR番号> を作成しました。他のAIのレビューをお願いします。"`
     2. レビュー担当のAIは、人間から「PR #<番号> をレビューして」と指示されたら以下を実施:
        - `gh pr diff <番号>` で差分を確認
        - コード品質・既存機能への影響・ルール準拠を確認
        - 問題なければ `gh pr review <番号> --approve --body "確認内容の要約"`
        - 問題があれば `gh pr review <番号> --request-changes --body "指摘内容"`
   - **作業開始前の安全コミット（必須）**:
     - ファイル編集を始める前に、ワーキングツリーの未コミット変更を確認する（`git status`）
     - 未コミットの変更がある場合は、**作業に着手する前に現状をコミットする**
     - コミットメッセージ例: `WIP: 作業前の状態を保全`
     - これにより、作業中にファイルを破損しても `git checkout` で直前の状態に復元できる
     - **このルールは例外なく適用する。「小さな変更だから」「すぐ終わるから」は理由にならない**
   - **コンテキスト制限時**:
     - 進捗をコミット＆プッシュし、Issueにハンドオフコメントを残す
