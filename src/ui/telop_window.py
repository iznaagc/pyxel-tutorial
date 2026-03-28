import pyxel

import config
from ui.window import BaseWindow


# --- デフォルト設定 ---
DEFAULT_SCROLL_SPEED = 1.0     # スクロール速度（px/frame）
DEFAULT_TELOP_LINE_HEIGHT = 24  # テロップ用行高さ（px）


class TelopWindow(BaseWindow):
    """テロップウィンドウ。
    テキストを下から上にスクロール表示する。

    用途:
    - オープニングのストーリーテキスト
    - スタッフロール / エンディング

    仕組み:
    - ウィンドウ自体を上方向に移動させることでスクロールを実現
    - テキストはウィンドウ内に静的に配置される
    - 画面外の行は描画をスキップする
    """

    def __init__(self, x=0, width=0,
                 text_color=7,
                 scroll_speed=DEFAULT_SCROLL_SPEED,
                 line_height=DEFAULT_TELOP_LINE_HEIGHT,
                 center=True):
        """
        Args:
            x: テキスト表示のx座標
            width: テキスト領域の幅（0で画面幅）
            text_color: テキストの色
            scroll_speed: スクロール速度（px/frame、小数可）
            line_height: 行の高さ（px）
            center: テキストを中央揃えにするか
        """
        if width <= 0:
            width = config.SCREEN_WIDTH

        super().__init__(
            x=x, y=0,
            width=width, height=0,
            text_color=text_color,
            has_border=False, has_bg=False,
            semi_transparent=False,
            auto_resize=False,
        )

        self.scroll_speed = scroll_speed
        self._line_height = line_height
        self._center = center

        self._scroll_y = 0.0       # float で滑らかなサブピクセルスクロール
        self._is_complete = False
        self._is_paused = False
        self._visible_height = config.SCREEN_HEIGHT

    # --- プロパティ ---

    @property
    def is_complete(self):
        """スクロールが完了したか。"""
        return self._is_complete

    @property
    def is_paused(self):
        """一時停止中か。"""
        return self._is_paused

    # --- 公開メソッド ---

    def show(self, lines):
        """テロップを開始する。

        Args:
            lines: テキスト行のリスト。空文字列で空行になる。
        """
        self._lines = lines
        self.height = len(lines) * self._line_height + self._text_padding * 2

        # 画面下端から開始
        self._scroll_y = float(self._visible_height)
        self.y = int(self._scroll_y)
        self._is_complete = False
        self._is_paused = False
        self.open()

    def pause(self):
        """スクロールを一時停止する。"""
        self._is_paused = True

    def resume(self):
        """スクロールを再開する。"""
        self._is_paused = False

    def skip(self):
        """スクロールをスキップして完了する。"""
        self._is_complete = True
        self.close()

    # --- update / draw ---

    def update(self):
        """スクロール位置を更新する。"""
        if not self.is_open or self._is_paused:
            return

        self._scroll_y -= self.scroll_speed
        self.y = int(self._scroll_y)

        # 全テキストが画面上端を通過したら完了
        if self._scroll_y + self.height < 0:
            self._is_complete = True
            self.close()

    def draw(self):
        """テロップを描画する。"""
        if not self.is_open:
            return

        # 背景・枠線（通常は非表示）
        super().draw()

        font = config.FONT

        for i, line in enumerate(self._lines):
            line_y = self.y + self._text_padding + i * self._line_height

            # 画面外の行はスキップ
            if line_y + self._line_height < 0:
                continue
            if line_y > self._visible_height:
                continue

            if not line:
                continue

            if self._center:
                text_w = font.text_width(line) if font else len(line) * 8
                text_x = self.x + (self.width - text_w) // 2
            else:
                text_x = self.x + self._text_padding

            pyxel.text(text_x, line_y, line, self.text_color, font)
