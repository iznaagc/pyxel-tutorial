import pyxel
from src.constants import SCENE_PLAY, SCENE_CLEAR, SCENE_TITLE, TILE_SIZE, LEVELS, WINDOW_WIDTH, WINDOW_HEIGHT

class PlayScene:
    def __init__(self, app):
        self.app = app
        self.walls = []
        self.goals = []
        self.boxes = []
        self.player_x = 0
        self.player_y = 0
        self.offset_x = 0
        self.offset_y = 0
        self.history = []

    def init_game(self):
        self.walls = []
        self.goals = []
        self.boxes = []
        self.history = []
        
        # Load current level map
        current_map = LEVELS[self.app.current_level]
        map_width = 0
        map_height = len(current_map)
        
        for y, row in enumerate(current_map):
            map_width = max(map_width, len(row))
            for x, char in enumerate(row):
                if char == '#':
                    self.walls.append((x, y))
                elif char == '.':
                    self.goals.append((x, y))
                elif char == '$':
                    self.boxes.append((x, y))
                elif char == '@':
                    self.player_x = x
                    self.player_y = y
                    
        self.offset_x = (WINDOW_WIDTH - (map_width * TILE_SIZE)) // 2
        self.offset_y = (WINDOW_HEIGHT - (map_height * TILE_SIZE)) // 2

    def save_state(self):
        # Deep copy boxes coordinates to history
        self.history.append({
            'px': self.player_x,
            'py': self.player_y,
            'boxes': list(self.boxes)
        })

    def undo_state(self):
        if len(self.history) > 0:
            last_state = self.history.pop()
            self.player_x = last_state['px']
            self.player_y = last_state['py']
            self.boxes = list(last_state['boxes'])
            pyxel.play(0, 0) # play move sound for feedback

    def update(self):
        dx = 0
        dy = 0
        
        if pyxel.btnp(pyxel.KEY_UP): dy = -1
        elif pyxel.btnp(pyxel.KEY_DOWN): dy = 1
        elif pyxel.btnp(pyxel.KEY_LEFT): dx = -1
        elif pyxel.btnp(pyxel.KEY_RIGHT): dx = 1
        elif pyxel.btnp(pyxel.KEY_Z): self.undo_state()
            
        if dx != 0 or dy != 0:
            nx = self.player_x + dx
            ny = self.player_y + dy
            
            if (nx, ny) in self.walls:
                pass
            elif (nx, ny) in self.boxes:
                bx = nx + dx
                by = ny + dy
                
                if (bx, by) not in self.walls and (bx, by) not in self.boxes:
                    self.save_state()
                    self.boxes.remove((nx, ny))
                    self.boxes.append((bx, by))
                    self.player_x = nx
                    self.player_y = ny
                    pyxel.play(0, 1) # Push sound
            else:
                self.save_state()
                self.player_x = nx
                self.player_y = ny
                pyxel.play(0, 0) # Move sound

        # Check Win Condition
        if len(self.boxes) > 0 and len(self.goals) > 0:
            won = True
            for box in self.boxes:
                if box not in self.goals:
                    won = False
                    break
            if won:
                self.app.scene = SCENE_CLEAR
                self.app.scenes[SCENE_CLEAR].on_enter()

        if pyxel.btnp(pyxel.KEY_C):
            self.app.scene = SCENE_CLEAR
            self.app.scenes[SCENE_CLEAR].on_enter()
        if pyxel.btnp(pyxel.KEY_R):
            self.init_game()

    def draw(self):
        pyxel.text(5, 5, "Z:Undo R:Retry C:Clear(Debug)", 13)
        
        def scr_x(gx): return self.offset_x + gx * TILE_SIZE
        def scr_y(gy): return self.offset_y + gy * TILE_SIZE
        
        # 1. Draw floor everywhere inside the map bounds
        current_map = LEVELS[self.app.current_level]
        map_width = len(current_map[0])
        map_height = len(current_map)
        for y in range(map_height):
            for x in range(map_width):
                pyxel.blt(scr_x(x), scr_y(y), 0, 0, 0, 8, 8)
        
        # 2. Draw Goals
        for gx, gy in self.goals:
            pyxel.blt(scr_x(gx), scr_y(gy), 0, 16, 0, 8, 8, 0)
            
        # 3. Draw Walls
        for wx, wy in self.walls:
            pyxel.blt(scr_x(wx), scr_y(wy), 0, 8, 0, 8, 8, 0)
            
        # 4. Draw Boxes
        for bx, by in self.boxes:
            pyxel.blt(scr_x(bx), scr_y(by), 0, 24, 0, 8, 8, 0)
            
        # 5. Draw Player
        pyxel.blt(scr_x(self.player_x), scr_y(self.player_y), 0, 32, 0, 8, 8, 0)
