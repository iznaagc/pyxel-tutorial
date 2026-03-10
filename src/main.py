import pyxel
import sys
import os

# プロジェクトルートディレクトリを検索パスに追加
# （srcディレクトリの外から実行しても、各モジュールのインポートが通るようにするため）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.constants import WINDOW_WIDTH, WINDOW_HEIGHT, SCENE_TITLE, SCENE_PLAY, SCENE_CLEAR
from src.assets import setup_assets
from src.scenes.title import TitleScene
from src.scenes.play import PlayScene
from src.scenes.clear import ClearScene

class App:
    """ゲーム全体の管理（オーケストレーター）クラス"""
    def __init__(self):
        # Pyxelウィンドウの初期化（横幅、高さ、タイトル）
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Sokoban Tutorial")
        
        # 画像や音声などのアセットを初期ロード
        setup_assets()
        
        self.current_level = 0 # 現在のレベル番号
        
        # 各シーンの管理インスタンスを作成
        self.scenes = {
            SCENE_TITLE: TitleScene(self),
            SCENE_PLAY: PlayScene(self),
            SCENE_CLEAR: ClearScene(self)
        }
        
        # 最初のシーンをタイトル画面に設定
        self.scene = SCENE_TITLE

        # メインループの開始（updateとdrawを繰り返し実行する）
        pyxel.run(self.update, self.draw)

    def update(self):
        """全体の更新処理（フレームごとに実行）"""
        # Qキーでいつでもゲーム終了
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        # 現在アクティブなシーンのupdate処理を実行
        self.scenes[self.scene].update()

    def draw(self):
        """全体の描画処理（フレームごとに実行）"""
        # 画面を黒(0)でクリア
        pyxel.cls(0)
        
        # クリア画面の時だけ、背面にプレイ画面を描画し続ける（透けて見えるようにするため）
        if self.scene == SCENE_CLEAR:
            self.scenes[SCENE_PLAY].draw()
            
        # 現在アクティブなシーンのdraw処理を呼び出す
        self.scenes[self.scene].draw()

    def next_level(self):
        """次のレベルへ進む処理"""
        from src.constants import LEVELS
        if self.current_level < len(LEVELS) - 1:
            # 次のレベルがある場合
            self.current_level += 1
            self.scene = SCENE_PLAY
            self.scenes[SCENE_PLAY].init_game() # 新しいマップで初期化
        else:
            # 全てのレベルをクリアした場合、タイトルへ戻る
            self.current_level = 0
            self.scene = SCENE_TITLE

if __name__ == "__main__":
    # アプリケーションの起動
    App()
