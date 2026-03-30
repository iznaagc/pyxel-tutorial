# 010 エディタ機能拡張: プレビュー・Undo/Redo・検索

## 概要

009 で作成した PySide6 テキストエディタ (`tools/gui_editor.py`) に、以下の3機能を追加した。

1. **プレビューパネル** — QPainter でゲーム画面の UI を再現描画
2. **Undo/Redo** — QUndoStack によるコマンドパターンの編集履歴管理
3. **テキスト検索 (Ctrl+F)** — ID名・テキスト内容のインクリメンタル検索

---

## 1. プレビューパネル (PreviewPanel)

### 目的

エディタ上でテキストを編集しながら、右ペインでゲーム中のメッセージウィンドウ・選択肢ウィンドウ・テロップの見た目をリアルタイム確認できるようにする。

### 実装方針

- `QWidget` を継承した `PreviewPanel` クラスを作成
- `paintEvent()` 内で **480x270 の QPixmap** にゲーム画面を描画し、ウィジェットサイズに合わせてスケーリング表示
- Pyxel の 16色パレットを `QColor` の定数配列 `PYXEL_PALETTE` として定義
- ゲーム用フォント `assets/fonts/madoufmg.ttf` を `QFontDatabase.addApplicationFont()` で登録して使用

### レイアウト変更

従来の **2ペイン**（ツリー | エディタ）から **3ペイン**（ツリー | エディタ | プレビュー）に変更。

```
┌────────┬──────────────┬──────────────┐
│  Tree  │   Editor     │   Preview    │
│ (200)  │   (500)      │   (400)      │
│        │              │  ┌────────┐  │
│        │              │  │480x270 │  │
│        │              │  │Scaled  │  │
│        │              │  └────────┘  │
└────────┴──────────────┴──────────────┘
```

`QSplitter` に3つのウィジェットを追加し、初期幅を `[200, 500, 400]` に設定。ウィンドウサイズも `1300x700` に拡大。

### 描画の詳細

#### メッセージウィンドウ (`_draw_message`)

ゲーム中の `src/ui/message_window.py` の見た目を再現する:

| 要素 | 位置・サイズ | 色 |
|------|------------|-----|
| メッセージ枠 | x=8, y=182, w=464, h=80 | 背景: パレット1(半透明), 枠: パレット7 |
| 名前ウィンドウ | x=12, y=158, h=24 | 同上 |
| テキスト | padding=8px, line_height=20px, 最大3行 | パレット7 (白) |
| 送りアイコン | 右下に "v" | パレット7 |
| auto 表示 | 左下に "[AUTO]" | パレット10 (黄) |
| ページ表示 | 右下に "Page N/M" | パレット13 (灰) |

半透明は `QColor.setAlpha(160)` で表現（ゲーム中の `pyxel.dither(0.5)` に相当）。

#### 選択肢ウィンドウ (`_draw_selection`)

| 要素 | 説明 |
|------|------|
| 自動サイズ | 最長テキスト幅 + カーソル幅 + padding から計算 |
| 配置 | 画面中央（desc がある場合はメッセージウィンドウの上） |
| カーソル | 先頭項目に ">" を表示 |
| desc 対応 | desc がある場合、下部にメッセージウィンドウも同時描画 |

#### テロップ (`_draw_telop`)

| 要素 | 説明 |
|------|------|
| テキスト | 中央揃え、全行を画面内に表示 |
| scroll_speed | 左上に黄色で表示 |
| 自動縮小 | 行数が多く画面に収まらない場合、行間を縮小し、フォントサイズも自動調整 |

テロップはゲーム中ではスクロールするが、プレビューでは**全行を静的に表示**する方針とした。

### プレビュー更新タイミング

- ツリーでエントリ選択時
- エディタで内容変更時 (`mark_dirty` → `_update_preview`)
- メッセージのページ切り替え時 (`_prev_page` / `_next_page` → `_notify_page_change`)

---

## 2. Undo/Redo (QUndoStack + EditCommand)

### 目的

テキスト編集の取り消し・やり直しを Ctrl+Z / Ctrl+Y で行えるようにする。

### 設計

Qt のコマンドパターン (`QUndoStack` + `QUndoCommand`) を採用。

```
EditCommand
├── _old_value: deepcopy（変更前のエントリデータ）
├── _new_value: deepcopy（変更後のエントリデータ）
├── redo(): _apply(_new_value)
└── undo(): _apply(_old_value)
```

#### スナップショット方式

- エントリ選択時に `_snapshot = deepcopy(entry_data)` で変更前状態を保存
- 編集操作が発生すると `mark_dirty()` が呼ばれ、500ms デバウンスタイマーを起動
- タイマー発火時に `_flush_undo()` で現在のデータと `_snapshot` を比較し、差分があれば `EditCommand` を push

#### in-place 更新（重要な設計判断）

`EditCommand._apply()` でデータを差し替える際、**オブジェクト参照を維持する**ことが極めて重要。

**問題**: 当初 `redo()` でデータオブジェクトを丸ごと置き換えていた:
```python
# NG: 参照が切断される
self._file_data[filepath][cat][entry_id] = deepcopy(new_value)
```

`QUndoStack.push()` は内部で `redo()` を呼ぶため、push 直後にエディタの `_data` 参照が旧オブジェクトを指したまま切断される。結果、2回目以降の編集が `_file_data` に反映されない。

**解決**: in-place で中身を入れ替え、参照を維持する:
```python
# OK: 参照が維持される
def _apply(self, value):
    target = self._file_data[filepath][cat][entry_id]
    source = deepcopy(value)
    if isinstance(target, list):
        target.clear()
        target.extend(source)    # messages (list)
    elif isinstance(target, dict):
        target.clear()
        target.update(source)    # selections, telops (dict)
```

#### 再帰防止

`_pushing_undo` フラグで `push()` → `redo()` → `indexChanged` → `_on_undo_or_redo()` の再帰を防止:

```
push() 開始
  └── _pushing_undo = True
  └── redo() 実行（データ in-place 更新）
  └── indexChanged シグナル発火
       └── _on_undo_or_redo() → _pushing_undo が True なので return
  └── _pushing_undo = False
```

ユーザーが Ctrl+Z / Ctrl+Y を押した場合は `_pushing_undo` が False なので、`_on_undo_or_redo()` が実行されてエディタ UI を再読み込みする。

#### シャットダウン時のクラッシュ防止

`closeEvent()` で `_closing = True` を設定し、`_undo_stack.clear()` が発火する `indexChanged` を無視する。

### メニュー

Edit メニューに `createUndoAction()` / `createRedoAction()` で自動生成されるアクションを追加。Qt が Undo/Redo 可否に応じてメニュー項目を自動的に有効/無効にする。

---

## 3. テキスト検索 (Ctrl+F)

### 目的

多数のエントリの中から目的のテキストを素早く見つけられるようにする。

### UI

画面上部に検索バーを配置（初期非表示、Ctrl+F でトグル）:

```
┌─ Search: [___________] 1/5  < > x ─┐
```

| 要素 | 説明 |
|------|------|
| テキスト入力 | プレースホルダー "ID or text..." |
| カウント表示 | "N/M" 形式（現在位置/総ヒット数） |
| < > ボタン | 前/次の結果に移動 |
| x ボタン | 検索バーを閉じる |

### 検索対象

全ファイル × 全カテゴリのエントリを横断検索する:

| カテゴリ | 検索対象フィールド |
|---------|-------------------|
| messages | エントリID, text, name |
| selections | エントリID, items[], desc.text, desc.name |
| telops | エントリID, lines[] |

### 検索方式

- **インクリメンタル**: テキスト入力の度に全エントリを走査
- **大文字小文字無視**: `query.lower()` で比較
- **結果ナビゲーション**: ツリーアイテムの `data(0, Qt.UserRole)` からファイル/カテゴリ/エントリIDを照合し、`setCurrentItem()` で選択

### キーバインド

| キー | 動作 |
|------|------|
| Ctrl+F | 検索バー表示/非表示 |
| Enter | 次の結果に移動 |
| < / > ボタン | 前/次の結果に移動 |

---

## 追加した定数・クラス一覧

### 定数

| 定数名 | 値 | 用途 |
|--------|-----|------|
| `PYXEL_PALETTE` | QColor[16] | Pyxel 16色パレット |
| `GAME_WIDTH/HEIGHT` | 480/270 | ゲーム画面サイズ |
| `FONT_PATH` | assets/fonts/madoufmg.ttf | ゲーム用フォント |
| `MSG_X/Y/W/H` | 8/182/464/80 | メッセージウィンドウ位置 |
| `SEL_*` | 各種 | 選択肢ウィンドウ定数 |
| `TELOP_*` | 各種 | テロップ定数 |

### クラス

| クラス | 親クラス | 役割 |
|--------|---------|------|
| `PreviewPanel` | QWidget | QPainter によるゲームUI再現描画 |
| `EditCommand` | QUndoCommand | エントリ単位の Undo/Redo コマンド |

### EditorWindow に追加したメンバー

| メンバー | 型 | 用途 |
|---------|-----|------|
| `_preview` | PreviewPanel | プレビューパネル |
| `_undo_stack` | QUndoStack | Undo/Redo スタック |
| `_snapshot` | deepcopy | 変更前スナップショット |
| `_pushing_undo` | bool | push 中の再帰防止 |
| `_closing` | bool | シャットダウン中フラグ |
| `_search_bar` | QWidget | 検索バー |
| `_search_input` | QLineEdit | 検索テキスト入力 |
| `_search_results` | list | 検索結果リスト |
| `_search_index` | int | 現在の検索結果インデックス |

---

## スクリーンショット

| ファイル | 内容 |
|---------|------|
| `screenshots/gui_editor_preview_message.png` | メッセージプレビュー表示 |
| `screenshots/gui_editor_preview_selection.png` | 選択肢プレビュー表示 |
| `screenshots/gui_editor_preview_telop.png` | テロッププレビュー表示 |
| `screenshots/gui_editor_search.png` | テキスト検索UI |

---

## 学んだこと・注意点

### QUndoStack の push() は redo() を呼ぶ

`QUndoStack.push(cmd)` は内部で `cmd.redo()` を実行する。エディタが既にデータを直接編集している場合、`redo()` でデータ参照を置き換えるとエディタの `_data` が切断される。**in-place 更新**（`clear()` + `extend()`/`update()`）で回避した。

### シグナルの発火タイミングに注意

`push()` → `redo()` → `indexChanged` の連鎖で意図しないUI更新が走る。`_pushing_undo` フラグで制御した。同様に、ウィンドウ破棄後にシグナルが発火すると `RuntimeError: Internal C++ object already deleted` が発生するため、`_closing` フラグで防止した。

### テロップの行数とプレビュー表示

テロップはゲーム中ではスクロール表示だが、プレビューでは全行を一覧表示する。21行あるテロップ（21 * 24px = 504px）はゲーム画面(270px)に収まらないため、行間とフォントサイズを自動縮小するロジックを実装した。
