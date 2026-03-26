import pyxel

from scenes.base import Scene


class GameScene(Scene):
    """ゲーム画面の仮実装。Escでタイトルに戻る。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.scene_manager.change_scene("title")

    def draw(self):
        pyxel.cls(0)
        pyxel.text(100, 120, "GAME SCENE", 7)
        pyxel.text(80, 140, "Press ESC to return", 5)