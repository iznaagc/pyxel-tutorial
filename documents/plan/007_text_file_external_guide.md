# テキスト外部ファイル化 + エディタツール 運用ガイド

## 概要

ゲーム内のテキスト（メッセージ、選択肢、テロップ）をソースコードから分離し、
JSONファイルで管理するシステム。2種類のエディタツールを提供する。

| ツール | 用途 | 起動コマンド |
|--------|------|------------|
| **GUIエディタ** (PySide6) | テキスト編集・保存・コンパイルの主力ツール | `.venv/Scripts/python tools/gui_editor.py` |
| **Pyxelビューア** | ゲーム内UIでのプレビュー確認用 | `.venv/Scripts/python tools/editor_app.py` |

---

## ディレクトリ構成

```
pyxel/tutorial/
├── data/
│   ├── text/
│   │   └── demo.json              ← テキストソース（シーン別に分割可能）
│   └── compiled/
│       └── text_all.bin           ← 全ファイルマージ後のgzip圧縮バイナリ
├── tools/
│   ├── gui_editor.py              ← GUIエディタ本体（PySide6）
│   ├── compiler.py                ← コンパイラ（JSON → bin）
│   ├── editor_app.py              ← Pyxelプレビューア
│   ├── editor_config.py           ← Pyxelビューアの画面設定
│   ├── editor_harness.py          ← ビューアのスクリーンショット撮影
│   └── panels/                    ← ビューア用パネル
│       ├── base_panel.py
│       ├── text_panel.py
│       └── preview_panel.py
└── src/
    └── data/
        ├── __init__.py
        └── text_manager.py        ← ゲーム側ローダー（TextManager）
```

---

## GUIエディタ（メインツール）

### 起動

```bash
.venv/Scripts/python tools/gui_editor.py
```

### 画面構成

左ペイン（ファイルツリー）と右ペイン（編集フォーム）の2ペイン構成。

- **ファイルツリー**: ファイル → カテゴリ（Messages/Selections/Telops） → ID の3階層
- **編集フォーム**: 選択したIDのカテゴリに応じた専用フォームが表示される

### 操作一覧

| 操作 | 説明 |
|------|------|
| ツリーでID選択 | 右ペインに編集フォームが表示される |
| Ctrl+S | 全ファイル保存 |
| F5 | コンパイル実行（未保存の場合は先に自動保存） |
| F9 | JSONファイル再読み込み |
| Ctrl+Q | 終了 |
| Edit → Add ID | 選択中のカテゴリに新しいIDを追加 |
| Edit → Delete ID | 選択中のIDを削除 |

### カテゴリ別 編集フォーム

**Messages:**
- Name: キャラクター名（空欄で名前なし）
- Text: メッセージ本文（複数行対応）
- 自動送り (auto): チェックで有効
- ページ送り: `<` `>` ボタンで前後のページに移動
- `+` `-` ボタンでページの追加/削除

**Selections:**
- Items: 1行1選択肢のテキストエリア
- Cancel Index: ESCキー時の選択肢インデックス
- 半透明 (semi_transparent): チェックで有効
- Desc: 説明メッセージ（Name + Text）

**Telops:**
- Lines: 1行1テロップ行のテキストエリア（空行もそのまま保持）
- Scroll Speed: スクロール速度（0.1〜10.0）

---

## Pyxelビューア（プレビュー用）

ゲーム内の実際のUIコンポーネントでテキストを確認する。

```bash
.venv/Scripts/python tools/editor_app.py
```

| キー | 操作 |
|------|------|
| Up/Down | テキストID選択 |
| F5 | コンパイル実行 |
| F9 | JSONリロード |
| ESC | 終了 |

画面サイズ等は `tools/editor_config.py` で変更可能:

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `SCREEN_W` | 640 | 横幅（px） |
| `SCREEN_H` | 400 | 縦幅（px） |
| `DISPLAY_SCALE` | 2 | 表示倍率 |
| `TEXT_PANEL_W` | 200 | テキスト一覧パネル幅 |

---

## 典型的なワークフロー

### GUIエディタで編集する場合（推奨）

1. `gui_editor.py` を起動
2. ツリーからテキストIDを選択して編集
3. Ctrl+S で保存
4. F5 でコンパイル
5. ゲームを起動して確認

### VSCode + Pyxelビューアで作業する場合

1. `editor_app.py` を起動
2. VSCode で `data/text/demo.json` を編集・保存
3. ビューアで F9 → プレビュー確認
4. F5 でコンパイル

---

## テキストファイル分割

`data/text/` 内に複数のJSONファイルを置ける。コンパイラが全ファイルをマージして1つの `text_all.bin` を生成する。

### ファイル追加手順

1. `data/text/` に新しいJSONを作成（例: `chapter01.json`）:
   ```json
   {
     "version": 1,
     "file_id": "chapter01",
     "messages": { ... },
     "selections": { ... },
     "telops": { ... }
   }
   ```
2. `file_id` は各ファイルで一意にする
3. テキストIDは全ファイル通して一意でなければならない（重複時はコンパイルエラー）
4. `messages`, `selections`, `telops` は空 `{}` でもOK

### ID重複エラーの例

```
ID重複: messages.msg_basic が demo.json と chapter01.json の両方に存在します
```

---

## JSONスキーマ

### ファイル構造

```json
{
  "version": 1,
  "file_id": "demo",
  "messages": { ... },
  "selections": { ... },
  "telops": { ... }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| version | int | Yes | スキーマバージョン（現在は `1`） |
| file_id | string | Yes | ファイル識別子（一意） |
| messages | object | Yes | メッセージデータ |
| selections | object | Yes | 選択肢データ |
| telops | object | Yes | テロップデータ |

### messages

```json
"msg_basic": [
  {"text": "テキスト\n改行もOK", "name": "キャラ名"},
  {"text": "自動送り", "name": "説明", "auto": true},
  "名前なしメッセージ（文字列だけでもOK）"
]
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| text | string | Yes | 表示テキスト（`\n`で改行、最大3行） |
| name | string | No | 名前ウィンドウに表示する名前 |
| auto | boolean | No | true で自動送り |

### selections

```json
"select_yesno": {
  "items": ["はい", "いいえ"],
  "cancel_index": 1,
  "semi_transparent": false,
  "desc": {"text": "説明テキスト", "name": "説明"}
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| items | string[] | Yes | 選択肢テキストの配列 |
| cancel_index | int | No | ESCキー時に選ばれるインデックス |
| semi_transparent | boolean | No | 半透明ウィンドウ |
| desc | object | No | 説明メッセージ（text, name） |

### telops

```json
"telop_story": {
  "lines": ["", "遥かなる時の彼方──", ""],
  "scroll_speed": 0.8
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

座標（x, y）やスタイル（semi_transparent等の表示制御）はコード側に書く。

---

## コンパイラ仕様

```bash
.venv/Scripts/python tools/compiler.py
```

- `data/text/` 内の全 `.json` を読み込み
- 各ファイルをバリデーション（version, file_id, 必須キー, データ構造）
- 全ファイルの messages / selections / telops をマージ
- **ID重複チェック**（重複時はエラー、どのファイル由来か表示）
- マージ結果を gzip 圧縮して `data/compiled/text_all.bin` に出力

---

## 依存パッケージ

| パッケージ | 用途 |
|-----------|------|
| PySide6-Essentials | GUIエディタ |
| Pillow | スクリーンショットハーネス |
| pyxel | ゲーム本体 + Pyxelビューア |

```bash
.venv/Scripts/pip install PySide6-Essentials Pillow pyxel
```

---

## 今後の改善提案

### 優先度: 高

1. **GUIエディタ: プレビューパネル追加**
   - 現在は編集フォームのみで、ゲーム内での見た目は確認できない
   - QPainter でゲームUIを再現描画する右ペインを追加
   - ウィンドウ枠・テキスト・名前ウィンドウを Pyxel パレットカラーで描画
   - 編集と同時にリアルタイムでプレビュー更新

2. **GUIエディタ: Undo/Redo**
   - 現在は編集操作の取り消しができない
   - QUndoStack を使ったコマンドパターンで実装

3. **GUIエディタ: テキスト検索（Ctrl+F）**
   - テキスト内容やIDをインクリメンタル検索
   - 大量のテキストIDがある場合に必須

### 優先度: 中

4. **GUIエディタ: IDリネーム機能**
   - 現在は追加・削除のみでリネームができない
   - ゲームコード側のID参照も合わせて更新する仕組みがあると理想的

5. **GUIエディタ: ファイル間ID移動**
   - ドラッグ&ドロップでIDを別ファイルに移動
   - リファクタリング時に便利

6. **多言語対応（i18n）**
   - 言語別にディレクトリを分けて管理: `data/text/ja/`, `data/text/en/`
   - TextManager で言語切り替え
   - GUIエディタで言語を並べて比較編集

7. **バリデーション強化**
   - 1行あたりの文字数チェック（MessageWindowの表示幅を超えないか警告）
   - 未使用ID検出（JSONにあるがゲームコードで参照されていないID）
   - GUIエディタのステータスバーに警告表示

### 優先度: 低

8. **差分コンパイル**
   - JSONファイルのタイムスタンプ比較で変更がある場合のみコンパイル

9. **エクスポート/インポート**
   - CSV/TSVでエクスポートして翻訳者に渡す → インポートしてJSONに戻す

10. **エディタのゲーム制作ツールへの拡張**
    - PySide6 ベースなのでタブやドッキングウィンドウで拡張しやすい
    - 将来的にイベントエディタ・マップエディタ・スプライトエディタを追加
    - QDockWidget で各エディタをドッキング可能な構成にする
