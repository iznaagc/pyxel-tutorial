import pyxel
from src.constants import SCENE_TITLE, SCENE_PLAY

class TitleScene:
    def __init__(self, app):
        self.app = app

    def update(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            # Transition to PLAY scene
            self.app.scene = SCENE_PLAY
            self.app.scenes[SCENE_PLAY].init_game()

    def draw(self):
        pyxel.text(50, 40, "SOKOBAN GAME", pyxel.frame_count % 16)
        if pyxel.frame_count % 30 < 15:
            pyxel.text(40, 80, "PRESS ENTER TO START", 7)
