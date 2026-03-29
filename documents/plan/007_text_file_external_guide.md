# テキスト外部ファイル化 + エディタツール 運用ガイド

## 概要

ゲーム内のテキスト（メッセージ、選択肢、テロップ）をソースコードから分離し、
JSONファイルで管理するシステム。エディタツールでプレビュー・コンパイルが可能。

---

## ディレクトリ構成

```
pyxel/tutorial/
├── data/
│   ├── text/
│   │   └── demo_text.json        ← テキストソース（人間が編集する）
│   └── compiled/
│       └── demo_text.bin         ← gzip圧縮バイナリ（自動生成）
├── tools/
│   ├── compiler.py               ← コンパイラ
│   ├── editor_app.py             ← テキストエディタ v1
│   ├── editor_harness.py         ← エディタのスクリーンショット撮影
│   └── panels/
│       ├── base_panel.py         ← パネル基底クラス
│       ├── text_panel.py         ← テキスト一覧パネル
│       └── preview_panel.py      ← プレビューパネル
└── src/
    └── data/
        └── text_manager.py       ← ゲーム側ローダー（TextManager）
```

---

## 日常のワークフロー

### テキストを変更する

1. `data/text/demo_text.json` を VSCode 等で編集
2. コンパイル実行:
   ```bash
   .venv/Scripts/python tools/compiler.py
   ```
3. ゲームを起動して確認

### エディタでプレビューしながら作業する

```bash
.venv/Scripts/python tools/editor_app.py
```

| キー | 操作 |
|------|------|
| Up/Down | テキストID選択 |
| F5 | コンパイル実行（JSON → bin） |
| F9 | JSONリロード（編集を即反映） |
| ESC | 終了 |

**典型的な流れ:**
1. エディタを起動
2. VSCode で JSON を編集・保存
3. エディタで F9 → プレビュー確認
4. 問題なければ F5 でコンパイル

---

## JSONスキーマ詳細

### messages（メッセージ）

MessageWindow に渡すデータ。各IDに配列を紐付ける。

```json
"messages": {
  "msg_basic": [
    {"text": "テキスト\n改行もOK", "name": "キャラ名"},
    {"text": "自動送り", "name": "説明", "auto": true},
    "名前なしメッセージ（文字列だけでもOK）"
  ]
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| text | string | Yes | 表示テキスト（`\n`で改行、最大3行） |
| name | string | No | 名前ウィンドウに表示する名前 |
| auto | boolean | No | true で自動送り（一定時間後に次のメッセージへ） |

文字列リテラルだけを書いた場合は名前なしメッセージとして扱われる。

### selections（選択肢）

SelectWindow に渡すデータ。

```json
"selections": {
  "select_yesno": {
    "items": ["はい", "いいえ"],
    "cancel_index": 1,
    "semi_transparent": false,
    "desc": {"text": "説明テキスト", "name": "説明"}
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| items | string[] | Yes | 選択肢テキストの配列 |
| cancel_index | int | No | ESCキー押下時に選ばれる選択肢のインデックス |
| semi_transparent | boolean | No | true で半透明ウィンドウ |
| desc | object | No | 選択肢と同時表示する説明メッセージ |

### telops（テロップ）

TelopWindow に渡すデータ。

```json
"telops": {
  "telop_story": {
    "lines": ["", "遥かなる時の彼方──", "", "世界は光と闇の..."],
    "scroll_speed": 0.8
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| lines | string[] | Yes | テロップ行（空文字で空行） |
| scroll_speed | float | No | スクロール速度（デフォルト: 1.0） |

---

## ゲームコードからの使い方

```python
import config

# メッセージ表示
messages = config.TEXT_MANAGER.get_messages("msg_basic")
msg_window.show(messages)

# 選択肢表示
sel = config.TEXT_MANAGER.get_selection("select_yesno")
select_window = SelectWindow(
    x=200, y=60,
    items=sel["items"],
    cancel_index=sel.get("cancel_index", -1),
)

# テロップ表示
telop = config.TEXT_MANAGER.get_telop("telop_story")
telop_window = TelopWindow(scroll_speed=telop.get("scroll_speed", 1.0))
telop_window.show(telop["lines"])
```

**座標（x, y）やスタイル（semi_transparent等の表示制御）はコード側に書く。**
テキスト内容だけをJSONで管理する。

---

## コンパイラ（compiler.py）の仕様

- `data/text/` 内の全 `.json` を処理
- バリデーション:
  - `version` キー必須（現在は `1` のみ対応）
  - `messages`, `selections`, `telops` が存在すること
  - messages の各値が配列であること
  - selections の各値に `items` があること
  - telops の各値に `lines` があること
- 出力: `data/compiled/{basename}.bin`（gzip圧縮JSON）

---

## 新しいテキストデータを追加する手順

1. `demo_text.json` に新しいIDとデータを追加:
   ```json
   "messages": {
     "msg_new_scene": [
       {"text": "新しいシーンの\nメッセージです。", "name": "キャラ名"}
     ]
   }
   ```

2. コンパイル:
   ```bash
   .venv/Scripts/python tools/compiler.py
   ```

3. ゲームコードで参照:
   ```python
   msgs = config.TEXT_MANAGER.get_messages("msg_new_scene")
   self.msg_window.show(msgs)
   ```

---

## 今後の改善提案

### 優先度: 高

1. **テキストファイル分割対応**
   - 現在は `demo_text.json` 1ファイルにすべて集約
   - シーン別・チャプター別にファイルを分割し、コンパイラが全ファイルをマージできるようにする
   - 例: `data/text/chapter01.json`, `data/text/chapter02.json` → `compiled/text_all.bin`

2. **エディタ上でのテキスト編集機能**
   - 現状はVSCodeでJSON編集 → F9リロードという流れ
   - エディタ内でテキストを直接編集・保存できるようにする
   - テキスト入力フィールド、保存（Ctrl+S）、Undo/Redo

3. **新規ID追加・削除機能**
   - エディタ上でテキストIDの新規作成・削除・リネームを行えるようにする

### 優先度: 中

4. **多言語対応（i18n）**
   - `demo_text.json` に `"lang": "ja"` を追加し、言語別にファイルを管理
   - `data/text/ja/demo_text.json`, `data/text/en/demo_text.json`
   - TextManager で言語切り替え

5. **テキスト検索機能**
   - エディタ内でテキスト内容をインクリメンタル検索
   - 特定の文字列を含むIDをすぐに見つけられるようにする

6. **メッセージ送り確認プレビュー**
   - 現在は全文表示状態の静止プレビューのみ
   - Space/Enterでページ送りしながら実際のテキスト送りを確認できるモード

7. **エディタをゲーム制作ツールに拡張する基盤**
   - 要件にある通り、将来的にイベント・マップ・スプライト管理も行いたい
   - パネルシステムはすでに拡張可能な設計（BasePanel継承）
   - タブバーを追加して「テキスト」「イベント」「マップ」等を切り替える UI
   - `tools/panels/` に新パネルを追加するだけで機能拡張できる構造

### 優先度: 低

8. **バリデーション強化**
   - 1行あたりの文字数チェック（MessageWindowの表示幅を超えないか）
   - 未使用ID検出（JSONにあるがゲームコードで使われていないID）
   - IDの重複チェック（ファイル分割時に有用）

9. **差分コンパイル**
   - JSONファイルのタイムスタンプを比較し、変更がある場合のみコンパイル
   - 大量のテキストファイルがある場合のビルド高速化

10. **エクスポート機能**
    - テキストデータをCSV/TSVでエクスポートして翻訳者に渡す
    - 翻訳済みCSVをインポートしてJSONに変換
