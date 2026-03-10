import pyxel
from src.constants import SCENE_TITLE, LEVELS

class ClearScene:
    def __init__(self, app):
        self.app = app
        self.played_clear_sound = False
        self.all_clear = False

    def on_enter(self):
        self.played_clear_sound = False
        self.all_clear = (self.app.current_level >= len(LEVELS) - 1)

    def update(self):
        if not self.played_clear_sound:
            pyxel.play(0, 2)
            self.played_clear_sound = True
            
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.all_clear:
                self.app.current_level = 0
                self.app.scene = SCENE_TITLE
            else:
                self.app.next_level()

    def draw(self):
        # We rely on the App rendering the play scene underneath before calling this
        # Overlay clear text
        pyxel.rect(20, 35, 120, 30, 0)
        pyxel.rectb(20, 35, 120, 30, 10)
        
        if self.all_clear:
            pyxel.text(40, 40, "ALL STAGES CLEAR!", 10)
            if pyxel.frame_count % 30 < 15:
                pyxel.text(45, 55, "PRESS ENTER TO END", 7)
        else:
            pyxel.text(50, 40, "STAGE CLEAR!", 10)
            if pyxel.frame_count % 30 < 15:
                pyxel.text(45, 55, "PRESS ENTER FOR NEXT", 7)
