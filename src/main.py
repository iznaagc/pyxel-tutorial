import pyxel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.constants import WINDOW_WIDTH, WINDOW_HEIGHT, SCENE_TITLE, SCENE_PLAY, SCENE_CLEAR
from src.assets import setup_assets
from src.scenes.title import TitleScene
from src.scenes.play import PlayScene
from src.scenes.clear import ClearScene

class App:
    def __init__(self):
        # Initialize Pyxel window
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Sokoban Tutorial")
        
        # Load all assets (images, sounds)
        setup_assets()
        
        self.current_level = 0
        
        # Initialize scene managers
        self.scenes = {
            SCENE_TITLE: TitleScene(self),
            SCENE_PLAY: PlayScene(self),
            SCENE_CLEAR: ClearScene(self)
        }
        
        self.scene = SCENE_TITLE

        # Start the application loop
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        # Delegate update to the active scene
        self.scenes[self.scene].update()

    def draw(self):
        pyxel.cls(0)
        
        # If we are in the clear scene, draw the play scene underneath it first
        if self.scene == SCENE_CLEAR:
            self.scenes[SCENE_PLAY].draw()
            
        # Delegate draw to the active scene
        self.scenes[self.scene].draw()

    def next_level(self):
        from src.constants import LEVELS
        if self.current_level < len(LEVELS) - 1:
            self.current_level += 1
            self.scene = SCENE_PLAY
            self.scenes[SCENE_PLAY].init_game()
        else:
            # All levels cleared
            self.current_level = 0
            self.scene = SCENE_TITLE

if __name__ == "__main__":
    App()
