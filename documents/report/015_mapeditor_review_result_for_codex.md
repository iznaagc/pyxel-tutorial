# 015 Map Editor コードレビュー結果 & Codex 向け修正依頼書

レビュー実施者: Claude Code  
対象ブランチ: `task/asset-loading-support`  
レビュー対象: `tools/gui_editor.py`（タスク A〜J の実装）  
作成日: 2026-04-04

---

## 概要

タスク A〜J の実装は全体として仕様に沿っており、動作の基礎は成立している。
ただし以下の問題が確認された。重要度順に記載する。

---

## 問題一覧

### 問題 1【High】レイヤー操作・通行判定・イベント配置に Undo 対応なし

**1. 問題の要約**

`LayerPanel` のレイヤー追加・削除・並び替え、`MapPropertyPanel` の通行判定変更、`EditorWindow` のイベント配置がいずれも `QUndoCommand` を push せず直接 `_map_data` を変更している。  
レビュー依頼書の観点 3「Undo/Redo 整合性」に正面から抵触する。

**2. 該当箇所**

| 操作 | ファイル・行 |
|---|---|
| レイヤー追加 | `LayerPanel._add_layer()` ≈ 2039 行 |
| レイヤー削除 | `LayerPanel._remove_layer()` ≈ 2057 行 |
| レイヤー上下移動 | `LayerPanel._move_current()` ≈ 2070 行 |
| 通行判定変更 | `MapPropertyPanel._on_passability_toggled()` ≈ 1829 行 |
| イベント配置 | `EditorWindow._handle_map_event_double_click()` ≈ 4099 行 |

**3. 現状の挙動**

上記操作を行った後に Ctrl+Z を押しても操作は取り消されない。  
タイル描画（`PaintTileCommand`）やマップリサイズ（`ResizeMapCommand`）と異なり Undo スタックに積まれない。

**4. なぜ問題か**

ユーザーが誤ってレイヤーを削除したり、通行不可に設定したタイルを誤って変更した場合に元に戻せない。  
既存の Undo/Redo インフラ（`_undo_stack`）と整合が取れていない。

**5. 修正方針**

各操作に対応する `QUndoCommand` サブクラスを新設し、`_undo_stack.push()` を使用する。

```python
# 例: AddLayerCommand
class AddLayerCommand(QUndoCommand):
    def __init__(self, map_data, layer, description="Add Layer"):
        super().__init__(description)
        self._map_data = map_data
        self._layer = layer

    def redo(self):
        self._map_data["layers"].append(self._layer)

    def undo(self):
        self._map_data["layers"].remove(self._layer)
```

`RemoveLayerCommand`・`MoveLayerCommand`・`SetPassabilityCommand`・`PlaceEventCommand` についても同様。  
`LayerPanel` は `_add_layer` / `_remove_layer` / `_move_current` を `window()._undo_stack` 経由でコマンド push する形に変更する。  
または `Signal` を経由して `EditorWindow` 側でコマンドを生成してもよい。

---

### 問題 2【Medium】Undo/Redo 後にアクティブレイヤーが `MapCanvas` と `LayerPanel` で不一致になる

**1. 問題の要約**

Undo/Redo 後に `LayerPanel.set_data()` が呼ばれるが、`set_data()` 内の `_updating = True` 区間では `_on_current_row_changed` がシグナルを emit しないため、`MapCanvas._active_layer_idx` が更新されない。

**2. 該当箇所**

- `EditorWindow._on_undo_or_redo()` ≈ 3446〜3461 行
- `LayerPanel.set_data()` ≈ 1967〜1984 行（`_updating = True` で currentRowChanged をブロック）

**3. 現状の挙動**

Undo/Redo を実行すると `LayerPanel` の表示は更新されるが、`MapCanvas._active_layer_idx` は古い値のまま残る場合がある。  
その後の描画がアクティブレイヤーとして正しくないレイヤーに適用される。

**4. なぜ問題か**

レイヤーが複数ある状態で Undo/Redo を繰り返すと、見えているレイヤーと実際に編集対象のレイヤーがずれる。

**5. 修正方針**

`_on_undo_or_redo` の map モード処理に、`set_data()` 後の明示的なアクティブレイヤー同期を追加する。

```python
# _on_undo_or_redo 内 map モード処理（≈ 3452 行）に追加
if self._mode == "map":
    self._map_canvas.update()
    if self._current_map_path:
        map_data = self._map_file_data.get(self._current_map_path)
        if map_data:
            self._map_side._layer_panel.set_data(map_data)
            # ↓ 追加: アクティブレイヤーを明示的に同期する
            active_idx = self._map_canvas._active_layer_idx
            self._map_side._layer_panel.set_active_layer(active_idx)
            self._map_canvas.set_active_layer(active_idx)
            self._map_side._property_panel.set_data(map_data)
    self._dirty = True
    self._update_title()
    return
```

---

### 問題 3【Medium】`MapCanvas` が `TilesetPalette` のプライベート属性に直接アクセス

**1. 問題の要約**

`MapCanvas.paintEvent()` 内で `self._palette._tileset_pixmap` というプライベート属性に直接アクセスしている。

**2. 該当箇所**

`MapCanvas.paintEvent()` ≈ 1052 行:
```python
tileset_px = self._palette._tileset_pixmap
```

**3. 現状の挙動**

機能的には動作するが、`TilesetPalette._tileset_pixmap` の命名が変わると `MapCanvas` も壊れる。

**4. なぜ問題か**

カプセル化の原則に反する。`TilesetPalette` には既に `get_tileset_pixmap()` という公開メソッドがある（≈ 692 行）。

**5. 修正方針**

```python
# 変更前
tileset_px = self._palette._tileset_pixmap

# 変更後
tileset_px = self._palette.get_tileset_pixmap()
```

---

### 問題 4【Low】`_new_map` のファイル名サニタイズが不十分

**1. 問題の要約**

`_new_map()` のファイル名生成がスペースのアンダースコア変換のみで、パス区切り文字や OS 予約名に対応していない。

**2. 該当箇所**

`EditorWindow._new_map()` ≈ 4209 行:
```python
fname = name.replace(" ", "_") + ".json"
```

**3. 現状の挙動**

ユーザーが `../evil` や `CON`（Windows 予約名）等を入力するとパスが意図しない場所を指したりエラーになる。

**4. なぜ問題か**

開発者ツールなので実害は限定的だが、予期しないクラッシュや書き込みエラーが起きる可能性がある。

**5. 修正方針**

```python
import re
# 英数字・ハイフン・アンダースコード以外を除去
safe = re.sub(r"[^\w\-]", "_", name)
fname = safe + ".json"
```

---

### 問題 5【Low】`MinimapWidget` のタイル単位描画によるパフォーマンスリスク

**1. 問題の要約**

`MinimapWidget.paintEvent()` は全レイヤーの全タイルを毎フレーム 1px 単位で描画する二重ループを持つ。  
マップが大きい（例: 200×200）場合、パン/ズーム中に大量の `fillRect` が発生する。

**2. 該当箇所**

`MinimapWidget.paintEvent()` ≈ 2122〜2135 行

**3. 現状の挙動**

小〜中規模マップ（仕様書のデフォルト 20×15 等）では問題ない。  
最大サイズ（999×999）では 100 万回の `fillRect` 呼び出しが毎 pan/zoom で発生する。

**4. なぜ問題か**

マップ編集中に UI がフリーズする可能性がある。

**5. 修正方針**

マップデータが変化したときのみ `QPixmap` にキャッシュを作成し、`paintEvent` ではキャッシュを描画するようにする。

```python
class MinimapWidget(QWidget):
    def __init__(self, map_canvas, parent=None):
        ...
        self._cache_pixmap = None  # キャッシュ

    def invalidate_cache(self):
        """マップデータ変化時に呼ぶ"""
        self._cache_pixmap = None
        self.update()

    def paintEvent(self, event):
        if self._cache_pixmap is None:
            self._rebuild_cache()
        # キャッシュを描画 + ビューポート矩形を描画
        ...
```

---

## 残留リスク

1. **レイヤー削除後の `_active_layer_idx` の境界値**  
   レイヤーを削除後、`_active_layer_idx` が範囲外になる可能性がある。現在 `set_active_layer()` に clamp はあるが（≈ 932 行）、`LayerPanel._remove_layer()` が `active_layer_changed.emit(new_row)` を発行してから `set_data()` で再構築するまでの間にキャンバスが古いインデックスを参照するタイミングがある。

2. **イベントの重複配置**  
   `_handle_map_event_double_click` は既存イベントがあるセルは `EventEditor` を開く。ただし `events` リストに同一 `(x, y)` のエントリが複数ある場合（手動 JSON 編集等）、`_find_map_event_at` は最初の 1 件しか返さず、2 件目以降は編集・削除できない。

3. **マップモードのツールショートカットとテキストモードの競合**  
   `P / R / B / S` キーショートカットは `MapCanvas.keyPressEvent` で処理される（`setFocusPolicy(Qt.StrongFocus)`）。テキストモード時にキャンバスが非表示でもキーイベントが届く可能性が残る（非表示ウィジェットは通常フォーカスを持たないため実害は少ないが確認推奨）。

---

## テスト不足

- レイヤーを追加 → タイル描画 → レイヤーを削除 → Undo の連続操作テスト（実装後）
- 通行判定を変更 → Undo/Redo の往復テスト（実装後）
- イベントを配置 → テキストモードに切り替え → 再度マップモードに戻った後の events データ整合テスト
- ResizeMap → Undo → Redo を複数回繰り返した後のデータ整合テスト

---

## 将来的なリファクタリング候補

現状の `tools/gui_editor.py` は約 4278 行で、テキスト編集系とマップ編集系が混在している。  
短期的に分割を検討すべき領域:

| 候補ファイル | 含めるクラス |
|---|---|
| `tools/map_commands.py` | `PaintTileCommand`, `ResizeMapCommand`, 追加予定コマンド群 |
| `tools/map_canvas.py` | `MapCanvas`, `MinimapWidget` |
| `tools/map_panels.py` | `TilesetPalette`, `MapPropertyPanel`, `LayerPanel`, `MapSidePanel` |

ただし分割は機能追加より後で、動作確認が揃ってから行うことを推奨する。

---

## まとめ

- **即対応推奨（High）**: 問題 1（Undo 対応漏れ）
- **対応推奨（Medium）**: 問題 2（Undo/Redo 後のアクティブレイヤー不一致）、問題 3（プライベート属性アクセス）
- **余裕があれば対応（Low）**: 問題 4〜5

特に問題 1 のレイヤー操作 Undo は「マップ編集中にレイヤーを誤って削除したら元に戻せない」という実用上重大な欠陥のため、優先的に対処することを推奨する。
