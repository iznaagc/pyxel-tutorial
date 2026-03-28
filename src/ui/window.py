import pyxel

import config


# テキスト描画のデフォルト値
DEFAULT_TEXT_PADDING = 8
DEFAULT_LINE_HEIGHT = 20

# アクティブ状態の枠線色
INACTIVE_BORDER_COLOR = 13  # Pyxelパレット13=暗いグレー


class BaseWindow:
    """ウィンドウの基底クラス。
    すべてのウィンドウに共通する描画・状態管理・テキスト表示機能を提供する。
    """

    def __init__(self, x, y, width, height,
                 bg_color=1, border_color=7, text_color=7,
                 has_border=True, has_bg=True, semi_transparent=False,
                 auto_resize=True):
        """
        Args:
            x: ウィンドウ左上のx座標
            y: ウィンドウ左上のy座標
            width: ウィンドウの幅
            height: ウィンドウの高さ
            bg_color: 背景色（デフォルト: 1=暗い青）
            border_color: 枠線の色（デフォルト: 7=白）
            text_color: テキストの色（デフォルト: 7=白）
            has_border: 枠線を描画するか（デフォルト: True）
            has_bg: 背景を描画するか（デフォルト: True）
            semi_transparent: 背景を半透明にするか（デフォルト: False）
            auto_resize: テキスト内容に合わせてサイズを自動調整するか（デフォルト: True）
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.has_border = has_border
        self.has_bg = has_bg
        self.semi_transparent = semi_transparent
        self.auto_resize = auto_resize

        self.is_open = False
        self.is_active = False

        # テキスト表示用（サブクラスで利用）
        self._text_padding = DEFAULT_TEXT_PADDING
        self._line_height = DEFAULT_LINE_HEIGHT
        self._lines = []

    def open(self):
        """ウィンドウを開く。"""
        self.is_open = True

    def close(self):
        """ウィンドウを閉じる。"""
        self.is_open = False
        self.is_active = False

    def activate(self):
        """このウィンドウをアクティブ（入力受付状態）にする。"""
        self.is_active = True

    def deactivate(self):
        """このウィンドウを非アクティブにする。"""
        self.is_active = False

    def update(self):
        """サブクラスでオーバーライドする。"""
        pass

    def _current_border_color(self):
        """現在の状態に応じた枠線色を返す。"""
        if self.is_active:
            return self.border_color
        return INACTIVE_BORDER_COLOR

    def draw(self):
        """ウィンドウの背景と枠線を描画する。"""
        if not self.is_open:
            return

        if self.has_bg:
            if self.semi_transparent:
                pyxel.dither(0.5)

            pyxel.rect(self.x, self.y, self.width, self.height, self.bg_color)

            if self.semi_transparent:
                pyxel.dither(1.0)

        if self.has_border:
            pyxel.rectb(self.x, self.y,
                        self.width, self.height,
                        self._current_border_color())

    # --- テキスト表示の共通機能 ---

    def set_lines(self, lines):
        """表示テキスト行を設定し、auto_resize が有効なら自動リサイズする。"""
        self._lines = lines
        if self.auto_resize:
            self._resize_to_fit()

    def _resize_to_fit(self):
        """テキスト内容に合わせてウィンドウサイズを調整する。"""
        font = config.FONT
        max_w = 0
        for line in self._lines:
            w = font.text_width(line) if font else len(line) * 8
            max_w = max(max_w, w)
        self.width = max_w + self._text_padding * 2
        self.height = len(self._lines) * self._line_height + self._text_padding * 2

    def _draw_text_lines(self):
        """格納済みテキスト行を描画する。"""
        font = config.FONT
        x = self.x + self._text_padding
        y = self.y + self._text_padding
        for i, line in enumerate(self._lines):
            pyxel.text(x, y + i * self._line_height, line, self.text_color, font)


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
                         bg_color, border_color, text_color,
                         has_border, semi_transparent,
                         auto_resize=False)
        self.close_key = close_key

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
        if not self.is_open or not self.is_active:
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

        # テキスト描画（共通メソッド使用）
        self._draw_text_lines()

        # ヒント行
        font = config.FONT
        hint = "ESC:CLOSE"
        hint_y = self.y + self.height - 22
        pyxel.text(self.x + self._text_padding, hint_y, hint,
                   self.text_color, font)


# 後方互換: 既存コードで Window を使っている箇所のため
Window = OverlayWindow
