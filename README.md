# Pyxel 倉庫番 チュートリアル・プロジェクト

このプロジェクトは、Python用のレトロゲームエンジン **Pyxel** を使用して、2Dパズルゲーム「倉庫番」を作成する学習用プロジェクトです。

## プロジェクトの概要
タイトル画面、複数ステージ、ドット絵グラフィック、効果音、そして「1手戻す(Undo)」機能を備えた、実践的なミニゲーム構成になっています。

## セットアップと実行方法

### 1. 動作環境
- Python 3.14 (推奨)
- Pyxel バージョン 2.x 以上

### 2. インストール
仮想環境を作成し、必要なパッケージをインストールします。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. ゲームの起動
```powershell
python src/main.py
```

## 基本操作
- **十字キー**: プレイヤーの移動 / 箱を移動させる
- **Zキー**: 1手戻す（Undo）
- **Rキー**: 現在のステージを最初からやり直す
- **Enterキー**: シーンの切り替え（タイトル開始、クリア後の次へ）
- **Qキー**: ゲームを終了する

## ディレクトリ構成
- `src/`: ソースコード本体
- `assets/`: リソースファイル（※現在はコード内で生成）
- `documents/`: 各ソースコードの詳細解説ドキュメント
- `HISTORY.md`: 開発の全ステップの記録
- `Rule.md`: 開発および設計ルール
- `AGENT.md`: AIエージェント用の指示書

## 各コードの解説
詳細は `documents/` ディレクトリ内の各ファイルを参照してください。
- [main.py の役割](documents/main.md)
- [定義データ (constants.py)](documents/constants.md)
- [リソース初期化 (assets.py)](documents/assets.md)
- [画面別ロジック (scenes.md)](documents/scenes.md)
