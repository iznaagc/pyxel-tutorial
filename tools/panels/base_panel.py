"""エディタパネルの基底クラス。"""


class BasePanel:
    """パネルの基底クラス。各パネルはこれを継承する。"""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_active = False

    def on_activate(self):
        """パネルがアクティブになった時に呼ばれる。"""
        self.is_active = True

    def on_deactivate(self):
        """パネルが非アクティブになった時に呼ばれる。"""
        self.is_active = False

    def update(self):
        """毎フレームの更新。サブクラスでオーバーライドする。"""
        pass

    def draw(self):
        """毎フレームの描画。サブクラスでオーバーライドする。"""
        pass
