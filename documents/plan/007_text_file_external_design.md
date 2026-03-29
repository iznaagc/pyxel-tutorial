# 007: テキスト外部ファイル化 + エディタツール — 実装計画

## ステータス: Phase 2 完了

**決定事項:**
- エディタ v1: 閲覧 + プレビュー + コンパイル専用（テキスト編集は JSON を VSCode 等で行う）
- Phase 1 → Phase 2 の順に段階実装（Phase 1 完了後に Phase 2 着手）

---

## Context

game.py にすべてのテキストデータがハードコードされている。
テキストをゲームコードから分離して外部ファイル（JSON → gzip圧縮バイナリ）で管理し、
変更しやすくする。将来的にはPyxelベースのエディタツールで管理する。

---

## 設計方針

| 項目 | 決定 | 理由 |
|------|------|------|
| ソース形式 | JSON（UTF-8） | stdlib、追加依存なし |
| バイナリ形式 | gzip圧縮JSON | stdlib（json+gzip）、追加依存ゼロ |
| テキスト参照 | 文字列ID（例: `"msg_basic"`） | コードとデータの分離 |
| レイアウト情報 | コード側に残す | x, y, semi_transparent 等は表示制御 |
| ステータス名称 | コード側定数 | 要件通り |

---

## データスキーマ（demo_text.json）

```json
{
  "version": 1,
  "messages": {
    "msg_basic": [
      {"text": "こんにちは！\nメッセージの\nテスト", "name": "アリス"},
      "名前なしメッセージ"
    ]
  },
  "selections": {
    "demo_menu": {
      "items": ["メッセージ：基本（日本語会話）", ...],
      "cancel_index": 11
    },
    "select_yesno": {
      "items": ["はい", "いいえ"],
      "cancel_index": 1,
      "desc": {"text": "説明テキスト", "name": "説明"}
    }
  },
  "telops": {
    "telop_story": {
      "lines": ["", "遥かなる時の彼方──", ...],
      "scroll_speed": 0.8
    }
  }
}
```

---

## ディレクトリ構成

```
pyxel/tutorial/
├── data/
│   ├── text/
│   │   └── demo_text.json        # ソーステキスト
│   └── compiled/
│       └── demo_text.bin         # コンパイル済み
├── tools/
│   ├── compiler.py               # JSON → bin（Phase 1）
│   ├── editor_app.py             # エディタ本体（Phase 2）
│   ├── editor_config.py          # エディタ設定（Phase 2）
│   └── panels/                   # エディタパネル（Phase 2）
│       ├── base_panel.py
│       ├── text_panel.py
│       └── preview_panel.py
└── src/
    ├── data/
    │   ├── __init__.py
    │   └── text_manager.py       # ゲーム側ローダー
    ├── config.py                  # TEXT_MANAGER, DATA_DIR 追加
    ├── app.py                     # TextManager 初期化
    └── scenes/game.py             # ハードコードテキスト除去
```

---

## Phase 1: データ基盤（タスク一覧）

### タスク 1-1: `data/text/demo_text.json` 作成
- game.py から全テキストを抽出してJSON化
- 対象:
  - `DEMO_MENU_ITEMS` → selections.demo_menu
  - `_msg_basic()` → messages.msg_basic
  - `_msg_charcount()` → messages.msg_charcount
  - `_msg_mixed()` → messages.msg_mixed
  - `_get_select_patterns()` の各パターン → selections.select_yesno, select_3, select_long, select_many, select_semi（items + cancel_index + desc）
  - `_start_telop_story()` → telops.telop_story（lines + scroll_speed）
  - `_start_telop_credits()` → telops.telop_credits（lines + scroll_speed）

### タスク 1-2: `tools/compiler.py` 作成
- `data/text/*.json` を読み込み
- バリデーション（version, 必須キー確認）
- gzip圧縮して `data/compiled/*.bin` に出力
- CLI: `.venv/Scripts/python tools/compiler.py`
- PROJECT_ROOT は `os.path.dirname(__file__)` + `..` で算出

### タスク 1-3: `src/data/text_manager.py` 作成
- `TextManager` クラス:
  - `load(bin_path)`: gzip解凍 → json.loads → 内部辞書格納
  - `get_messages(msg_id) -> list`: MessageWindow.show() 形式で返す
  - `get_selection(sel_id) -> dict`: {"items": [...], "cancel_index": N, "desc": ...}
  - `get_telop(telop_id) -> dict`: {"lines": [...], "scroll_speed": float}
- 存在しないIDは KeyError + わかりやすいメッセージ

### タスク 1-4: `src/config.py` 変更
- `DATA_DIR = os.path.join(_PROJECT_ROOT, "data")`
- `COMPILED_DIR = os.path.join(DATA_DIR, "compiled")`
- `TEXT_MANAGER = None`
- `init_text_manager()` 関数追加

### タスク 1-5: `src/app.py` 変更
- `config.init_font()` 直後に `config.init_text_manager()` 呼び出し

### タスク 1-6: `src/scenes/game.py` 変更
- `DEMO_MENU_ITEMS` → `config.TEXT_MANAGER.get_selection("demo_menu")["items"]`
- `_msg_basic()` 等 → `config.TEXT_MANAGER.get_messages("msg_basic")`
- `_get_select_patterns()` → `config.TEXT_MANAGER.get_selection("select_yesno")` 等
- `_start_telop_story()` → `config.TEXT_MANAGER.get_telop("telop_story")`
- 座標やスタイル情報（x, y, semi_transparent, page_size等）はコードに残す

### タスク 1-7: 動作確認
- compiler.py でコンパイル実行
- ゲーム起動して全デモ項目を確認
- test_harness.py でスクリーンショット撮影（表示が変わっていないこと）

---

## Phase 2: Pyxel テキストエディタ v1（タスク一覧）

### タスク 2-1: エディタ骨格
- `tools/editor_app.py`: Pyxel アプリ（480x270）
- `sys.path` に `../src` 追加して game UI コンポーネントを import
- `config.init_font()` 呼び出しで同じフォント使用

### タスク 2-2: パネルシステム
- `panels/base_panel.py`: BasePanel（update, draw, on_activate, on_deactivate）
- タブバーでパネル切り替え（v1 は「テキスト」のみ）

### タスク 2-3: テキスト一覧パネル
- カテゴリ（messages / selections / telops）でグループ分け
- カーソル操作でID選択
- 選択するとプレビューパネルに反映

### タスク 2-4: プレビューパネル
- messages → MessageWindow（全文表示状態）
- selections → SelectWindow
- telops → TelopWindow（途中位置で静止表示）
- src/ui/ のコンポーネントをそのまま使用

### タスク 2-5: コンパイル・リロード
- F5: コンパイル実行
- F9: JSON 再読み込み
- ステータスバーに結果表示

---

## 重要ファイル（実装時に参照）

| ファイル | 内容 |
|---------|------|
| `src/scenes/game.py` | 抽出対象の全テキストデータ |
| `src/ui/message_window.py` | MessageWindow.show() の入力フォーマット |
| `src/ui/select_window.py` | SelectWindow の items フォーマット |
| `src/ui/telop_window.py` | TelopWindow.show() の入力フォーマット |
| `src/config.py` | パス定数・グローバル参照の管理パターン |
| `src/app.py` | 初期化順序（pyxel.init → init_font → init_text_manager） |
| `documents/plan/007_text_file_external.md` | 元の要件定義 |
