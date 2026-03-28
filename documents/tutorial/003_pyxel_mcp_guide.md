# pyxel-mcp 利用ガイド

pyxel-mcpは、Pyxelゲームの開発をAIアシスタント（Claude等）と連携して行うためのMCPサーバーです。
ゲーム画面のスクリーンショット取得、入力シミュレーション、オーディオ解析などをAIが直接実行できるようになります。

## 1. セットアップ

### 1.1 インストール

```bash
pip install pyxel-mcp
```

これにより `pyxel` と `pyxel-mcp` の両方がインストールされます。

### 1.2 MCP設定ファイルの作成

プロジェクトルートに `.mcp.json` を作成します:

```json
{
  "mcpServers": {
    "pyxel": {
      "command": "uvx",
      "args": ["pyxel-mcp"]
    }
  }
}
```

`uvx` がインストールされていない場合は、以下の形式でも利用できます:

```json
{
  "mcpServers": {
    "pyxel": {
      "command": "python",
      "args": ["-m", "pyxel_mcp.server"]
    }
  }
}
```

### 1.3 Claude Codeでの利用

Claude Codeを起動すると `.mcp.json` が自動的に読み込まれ、pyxel-mcpのツールが利用可能になります。
`/mcp` コマンドでMCPサーバーの接続状況を確認できます。

## 2. 主要ツール一覧

### 2.1 画面キャプチャ系

| ツール名 | 説明 |
|---------|------|
| `run_and_capture` | スクリプトを実行し、指定フレーム後のスクリーンショットを取得 |
| `capture_frames` | 複数フレームのスクリーンショットを一括取得 |
| `play_and_capture` | キー入力をシミュレートしながらスクリーンショットを取得 |
| `compare_frames` | 2つのフレーム間の差分を比較 |

### 2.2 解析系

| ツール名 | 説明 |
|---------|------|
| `inspect_layout` | 画面レイアウト・テキスト配置のバランスを解析 |
| `inspect_screen` | 画面をカラーインデックスのグリッドとして取得 |
| `inspect_state` | ゲームオブジェクトの属性をJSON形式で取得 |
| `inspect_sprite` | スプライトのピクセルデータと対称性を検査 |
| `inspect_palette` | パレット使用状況を確認 |
| `inspect_tilemap` | タイルマップの内容を検査 |
| `inspect_bank` | イメージバンクの内容を検査 |

### 2.3 その他

| ツール名 | 説明 |
|---------|------|
| `pyxel_info` | Pyxelのインストール情報・サンプルパスを表示 |
| `validate_script` | スクリプトをAST解析してエラーやアンチパターンを検出（実行なし） |
| `render_audio` | サウンド/ミュージックをWAVに変換して波形解析 |

## 3. ツールの使い方

### 3.1 run_and_capture — 基本的なスクリーンショット

```
run_and_capture(
    script_path="E:/path/to/main.py",
    frames=60,     # 60フレーム後にキャプチャ（デフォルト: 60）
    scale=2,       # 拡大倍率（デフォルト: 2）
    timeout=10     # タイムアウト秒数（デフォルト: 10）
)
```

タイトル画面やメニュー画面など、入力不要の画面確認に使います。

### 3.2 play_and_capture — 入力シミュレーション付きキャプチャ

```
play_and_capture(
    script_path="E:/path/to/main.py",
    inputs='[
        {"frame": 5, "keys": ["KEY_RETURN"]},
        {"frame": 6, "keys": []},
        {"frame": 35, "keys": ["KEY_RETURN"]},
        {"frame": 36, "keys": []}
    ]',
    frames="30,50,80,120",  # キャプチャするフレーム番号
    scale=2,
    timeout=30
)
```

**inputs の形式:**
- `frame`: キー状態を変更するフレーム番号
- `keys`: 押下するキーのリスト（`KEY_RETURN`, `KEY_SPACE`, `KEY_UP` 等）
- `mouse_x`, `mouse_y`: マウス座標（省略可）

キーは指定フレームから次のエントリまで押し続けられます。キーを離すには `"keys": []` を指定します。

**キーの押下と離し:**
ボタン押下（`btnp`）を正しく検出させるには、1フレームだけキーを押して次のフレームで離す必要があります:
```json
[
    {"frame": 5, "keys": ["KEY_RETURN"]},
    {"frame": 6, "keys": []}
]
```

### 3.3 capture_frames — アニメーション確認

```
capture_frames(
    script_path="E:/path/to/main.py",
    frames="1,15,30,60",   # キャプチャフレーム（カンマ区切り）
    scale=2,
    timeout=30
)
```

入力なしで複数フレームのスクリーンショットを取得します。アニメーションやエフェクトの確認に便利です。

### 3.4 validate_script — 構文チェック

```
validate_script(
    script_path="E:/path/to/main.py"
)
```

実行せずにAST解析でエラーを検出します。`run_and_capture` より高速です。

### 3.5 inspect_state — デバッグ用状態取得

```
inspect_state(
    script_path="E:/path/to/main.py",
    frames="60",          # 状態を取得するフレーム
    attributes="",        # 特定属性のみ取得する場合に指定
    timeout=10
)
```

Appインスタンスの属性をJSON形式で取得し、ゲームの内部状態をデバッグできます。

## 4. 実践例: メッセージウィンドウのテスト

本プロジェクトでのテスト手順を例示します。

### 4.1 タイトル画面の確認

```
run_and_capture(script_path="src/main.py", frames=60)
```

### 4.2 メッセージウィンドウデモの確認

```
play_and_capture(
    script_path="src/main.py",
    inputs='[
        {"frame": 5, "keys": ["KEY_RETURN"]},
        {"frame": 6, "keys": []},
        {"frame": 35, "keys": ["KEY_RETURN"]},
        {"frame": 36, "keys": []},
        {"frame": 170, "keys": ["KEY_RETURN"]},
        {"frame": 171, "keys": []},
        {"frame": 300, "keys": ["KEY_RETURN"]},
        {"frame": 301, "keys": []}
    ]',
    frames="30,50,120,200,280,370,530,600"
)
```

この入力シーケンスの意味:
1. フレーム5: Enterで「START」を選択 → ゲーム画面へ
2. フレーム35: Enterでメッセージデモ開始
3. フレーム170: Enterで1つ目のメッセージを送る
4. フレーム300: Enterで2つ目のメッセージを送る
5. 3つ目は自動送り（60フレーム後に自動遷移）
6. 4つ目のメッセージ後、Enterでウィンドウクローズ

## 5. 利用可能なキー定数

pyxel-mcpの `inputs` で使用できる主要なキー定数:

| キー | 定数名 |
|-----|--------|
| Enter | `KEY_RETURN` |
| Space | `KEY_SPACE` |
| Escape | `KEY_ESCAPE` |
| 矢印キー | `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT` |
| 文字キー | `KEY_A` 〜 `KEY_Z` |

全キー定数はPyxelの `__init__.pyi` を参照してください。

## 6. トラブルシューティング

### MCPサーバーに接続できない

- `uvx` がインストールされているか確認: `which uvx`
- `.mcp.json` がプロジェクトルートにあるか確認
- Claude Codeの `/mcp` コマンドで接続状況を確認

### スクリーンショットが取得できない

- `timeout` を増やしてみる（デフォルト10秒）
- `validate_script` で構文エラーがないか確認
- スクリプトのパスが絶対パスであるか確認

### キー入力が反映されない

- `btnp()` を使っている場合、キーを1フレームだけ押して次フレームで離す
- フレーム番号が正しいか確認（ゲーム開始までにかかるフレーム数を考慮）
