import pyxel
from src.constants import SCENE_TITLE, SCENE_PLAY

class TitleScene:
    """タイトル画面の管理クラス"""
    def __init__(self, app):
        self.app = app

    def update(self):
        """タイトル画面の更新処理"""
        if pyxel.btnp(pyxel.KEY_RETURN):
            # Enterキーが押されたらプレイ画面に遷移
            self.app.scene = SCENE_PLAY
            # プレイ画面の初期化（マップ読み込みなど）を実行
            self.app.scenes[SCENE_PLAY].init_game()

    def draw(self):
        """タイトル画面の描画処理"""
        # タイトル文字（色をフレーム数で変化させて点滅させる）
        pyxel.text(50, 40, "SOKOBAN GAME", pyxel.frame_count % 16)
        
        # スタートの案内を点滅表示 (15フレーム周期)
        if pyxel.frame_count % 30 < 15:
            pyxel.text(40, 80, "PRESS ENTER TO START", 7)
