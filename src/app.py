import pyxel

import config
from core.scene_manager import SceneManager
from scenes.title import TitleScene
from scenes.game import GameScene
from scenes.opening_demo import OpeningDemoScene


class App:
    """ゲームアプリケーション本体。
    Pyxelの初期化・ゲームループの起動・シーン管理を統括する。
    """

    def __init__(self):
        pyxel.init(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, title="My Game")
        config.init_font()
        config.init_assets()
        config.init_text_manager()
        self._setup_builtin_sounds()

        # シーンマネージャーの初期化
        self.scene_manager = SceneManager()

        # 使用するシーンを全て登録する
        self.scene_manager.register("title", TitleScene)
        self.scene_manager.register("game", GameScene)
        self.scene_manager.register("opening_demo", OpeningDemoScene)
        # 新しいシーンが増えたらここに register を追加する

        # 最初に表示するシーンを指定
        self.scene_manager.change_scene("title")

        # ゲームループ開始（ここでブロッキング。以降は毎フレーム update/draw が呼ばれる）
        pyxel.run(self.update, self.draw)

    def _setup_builtin_sounds(self):
        """Pyxel内蔵音源の共通SE定義。"""
        pyxel.sounds[30].set("c3e3g3c4", "p", "7", "n", 10)
        pyxel.sounds[31].set("g3c4e4g4", "s", "7654", "n", 8)

    def update(self):
        """毎フレームの更新処理。アクティブシーンに委譲する。"""
        self.scene_manager.update()

    def draw(self):
        """毎フレームの描画処理。アクティブシーンに委譲する。"""
        self.scene_manager.draw()