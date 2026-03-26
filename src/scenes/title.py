import pyxel


from scenes.base import Scene
from ui.menu import Menu
from ui.window import Window



class TitleScene(Scene):
    """タイトルシーン。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)

        # メニュー(画面中央付近に配置)
        self.menu = Menu(
            x=100,
            y=120,
            items=[
                "START",
                "OPTION",
                "QUIT",
            ]
        )

        # オプションウィンドウ(画面中央にオーバレイ)
        self.option_window = Window(
            x=48,
            y=48,
            width=160,
            height=160
        )

    def update(self):
        # ウィンドウが開いている間はウィンドウの入力のみ処理する
        if self.option_window.is_open:
            self.option_window.update()
            return
        
        # メニュー0入力処理
        selected = self.menu.update()
        if selected == 0: # START
            self.scene_manager.change_scene("game")
        elif selected == 1: # OPTION
            self.option_window.open(lines=["~ OPTION MENU ~", "", "No settings yet."])
        elif selected == 2: # QUIT
            pyxel.quit()


    def draw(self):
        pyxel.cls(0)

        # タイトルテキスト
        pyxel.text(90, 40, "My GAME TITLE", 7)

        # メニュー描画(ウィンドウが開いていても描画する)
        self.menu.draw()

        # オプションウィンドウ描画(開いていれば前面に描画)
        self.option_window.draw()
