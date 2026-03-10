import pyxel

class App:
    def __init__(self):
        # Initialize Pyxel window (width, height, title)
        pyxel.init(160, 120, title="Pyxel Tutorial")
        
        # Load resources if you have any in assets/
        # pyxel.load("../assets/my_resource.pyxres")

        # Initial game state setup here
        self.x = 0

        # Start the application loop
        pyxel.run(self.update, self.draw)

    def update(self):
        # Handle game logic and user input here
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        self.x = (self.x + 1) % pyxel.width

    def draw(self):
        # Handle rendering here
        pyxel.cls(0) # Clear screen with color 0 (black)
        pyxel.text(55, 41, "Hello, Pyxel!", pyxel.frame_count % 16)
        pyxel.rect(self.x, 60, 10, 10, 9)

if __name__ == "__main__":
    App()
