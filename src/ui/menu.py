import pyxel

class Menu:
    """汎用メニューUI。カーソル選択に対応。"""

    def __init__(self, x, y, items):
        """
        Args:
            x, y: メニューの表示位置（左上）
            items: メニュー項目文字列のリスト
        """
        self.x = x
        self.y = y
        self.items = items
        self.cursor = 0  # 現在選択中のインデックス

    def update(self):
        """入力処理。上下キーでカーソル移動、Enterで決定。"""
        if pyxel.btnp(pyxel.KEY_UP):
            self.cursor = (self.cursor - 1) % len(self.items)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.cursor = (self.cursor + 1) % len(self.items)
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            return self.cursor  # 選択されたインデックスを返す
        return None  # まだ決定されていない

    def draw(self):
        """メニューを描画する。"""
        for i, item in enumerate(self.items):
            # カーソル位置に記号を表示
            prefix = "> " if i == self.cursor else "  "
            pyxel.text(self.x, self.y + i * 10, prefix + item, 7)