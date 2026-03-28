# プロジェクトルール

- 作業開始時に `AGENT.md` も確認し、そちらの指示もこのリポジトリのルールとして扱うこと

## スクリーンショット

- pyxel-mcpやharnessで撮影したスクリーンショットは `screenshots/` ディレクトリに保存すること
- ファイル名は内容がわかる英語の命名にする（例: `title_screen.png`, `msg_alice_complete.png`）
- 一時ディレクトリ（/tmp等）に残さず、必ずプロジェクト内に保存する
- **機能追加・改修後は都度スクリーンショットを撮影して記録として残す（恒久ルール）**

## スクリーンショット撮影ハーネス

pyxel-mcp が使えない場合でも `src/test_harness.py` で自動撮影できる。

### 実行方法

```bash
cd src && ../.venv/Scripts/python test_harness.py
```

### 仕組み

- Pyxel の `pyxel.run()` ループ内で各UI状態を直接構築・描画する
- 描画した次のフレームの `update()` で `pyxel.pget()` を使い画面バッファを読み取る
- Pillow (`PIL.Image`) でパレット変換して PNG に保存する（2倍スケール）
- Pyxel には入力シミュレーション API がないため、UIコンポーネントを直接操作（`open()` / `_char_index` 設定など）して目的の表示状態を作る

### 新しい撮影対象の追加方法

`test_harness.py` の `ScreenshotHarness` クラスに以下を追加する:

1. **描画関数を追加** — `_draw_xxx(self)` メソッドを作成。`pyxel.cls(0)` → ヘッダー描画 → UIコンポーネントの構築・描画を行う
2. **ショットリストに登録** — `_define_shots()` に `("ファイル名", self._draw_xxx)` を追加

```python
# 例: 新しいウィンドウの撮影を追加
def _draw_new_feature(self):
    pyxel.cls(0)
    self._header()
    # UIコンポーネントを構築して描画
    window = SomeWindow(x=100, y=50, ...)
    window.open()
    window.draw()

def _define_shots(self):
    return [
        # ... 既存のショット ...
        ("new_feature", self._draw_new_feature),
    ]
```

### 依存パッケージ

- `Pillow` が必要（`pip install Pillow`）
- pyxel のパレット色定義はハーネス内の `PALETTE` 定数で管理している
