import pyxel

import config


class BaseWindow:
    """ウィンドウの基底クラス。
    すべてのウィンドウに共通する描画・状態管理機能を提供する。
    """

    def __init__(self, x, y, width, height,
                 bg_color=1, border_color=7,
                 has_border=True, semi_transparent=False):
        """
        Args:
            x: ウィンドウ左上のx座標
            y: ウィンドウ左上のy座標
            width: ウィンドウの幅
            height: ウィンドウの高さ
            bg_color: 背景色（デフォルト: 1=暗い青）
            border_color: 枠線の色（デフォルト: 7=白）
            has_border: 枠線を描画するか（デフォルト: True）
            semi_transparent: 背景を半透明にするか（デフォルト: False）
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.border_color = border_color
        self.has_border = has_border
        self.semi_transparent = semi_transparent

        self.is_open = False

    def open(self):
        """ウィンドウを開く。"""
        self.is_open = True

    def close(self):
        """ウィンドウを閉じる。"""
        self.is_open = False

    def update(self):
        """サブクラスでオーバーライドする。"""
        pass

    def draw(self):
        """ウィンドウの背景と枠線を描画する。"""
        if not self.is_open:
            return

        if self.semi_transparent:
            pyxel.dither(0.5)

        pyxel.rect(self.x, self.y, self.width, self.height, self.bg_color)

        if self.semi_transparent:
            pyxel.dither(1.0)

        if self.has_border:
            pyxel.rectb(self.x, self.y,
                        self.width, self.height, self.border_color)


class OverlayWindow(BaseWindow):
    """汎用オーバーレイウィンドウ。
    画面上に矩形のウィンドウを重ねて表示する。
    シーン遷移せずに情報表示や設定変更UIを出したいときに使う。
    """

    def __init__(self, x, y, width, height,
                 bg_color=1, border_color=7, text_color=7,
                 has_border=True, semi_transparent=False,
                 close_key=pyxel.KEY_ESCAPE):
        super().__init__(x, y, width, height,
                         bg_color, border_color,
                         has_border, semi_transparent)
        self.text_color = text_color
        self.close_key = close_key
        self._lines = []

    def open(self, lines=None):
        """ウィンドウを開く。

        Args:
            lines: ウィンドウ内に表示するテキストのリスト（省略時は前回の内容を維持）
        """
        super().open()
        if lines is not None:
            self._lines = lines

    def update(self):
        """ウィンドウが開いている間の入力処理。

        Returns:
            True: ウィンドウが閉じられた
            False: ウィンドウはまだ開いている
        """
        if not self.is_open:
            return False

        if pyxel.btnp(self.close_key):
            self.close()
            return True

        return False

    def draw(self):
        """ウィンドウを描画する。"""
        if not self.is_open:
            return

        super().draw()

        font = config.FONT
        text_x = self.x + 6
        text_y = self.y + 6
        for i, line in enumerate(self._lines):
            pyxel.text(text_x, text_y + i * 20, line, self.text_color, font)

        hint = "ESC:CLOSE"
        hint_y = self.y + self.height - 22
        pyxel.text(text_x, hint_y, hint, self.text_color, font)


# 後方互換: 既存コードで Window を使っている箇所のため
Window = OverlayWindow
