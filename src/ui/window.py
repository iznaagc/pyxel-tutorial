import pyxel


class Window:
    """汎用オーバーレイウィンドウ。
    画面上に矩形のウィンドウを重ねて表示する。
    シーン遷移せずに情報表示や設定変更UIを出したいときに使う。
    """

    def __init__(self, x, y, width, height,
                 bg_color=1, border_color=7, text_color=7,
                 close_key=pyxel.KEY_ESCAPE):
        """
        Args:
            x: ウィンドウ左上のx座標
            y: ウィンドウ左上のy座標
            width: ウィンドウの幅
            height: ウィンドウの高さ
            bg_color: 背景色（デフォルト: 1=暗い青）
            border_color: 枠線の色（デフォルト: 7=白）
            text_color: テキスト色（デフォルト: 7=白）
            close_key: 閉じるキー（デフォルト: Escキー）
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.close_key = close_key

        # ウィンドウの開閉状態
        self.is_open = False

        # ウィンドウ内に表示するテキスト行のリスト
        self._lines = []

    def open(self, lines=None):
        """ウィンドウを開く。

        Args:
            lines: ウィンドウ内に表示するテキストのリスト（省略時は前回の内容を維持）
        """
        self.is_open = True
        if lines is not None:
            self._lines = lines

    def close(self):
        """ウィンドウを閉じる。"""
        self.is_open = False

    def update(self):
        """ウィンドウが開いている間の入力処理。

        Returns:
            True: ウィンドウが閉じられた（呼び出し元でメニュー操作を再開してよい）
            False: ウィンドウはまだ開いている
        """
        if not self.is_open:
            return False

        if pyxel.btnp(self.close_key):
            self.close()
            return True

        return False

    def draw(self):
        """ウィンドウを描画する。is_open が False なら何もしない。"""
        if not self.is_open:
            return

        # 背景の矩形
        pyxel.rect(self.x, self.y, self.width, self.height, self.bg_color)
        # 枠線
        pyxel.rectb(self.x, self.y, self.width, self.height, self.border_color)

        # テキスト描画（ウィンドウ内側に余白4pxを取る）
        text_x = self.x + 4
        text_y = self.y + 4
        for i, line in enumerate(self._lines):
            pyxel.text(text_x, text_y + i * 10, line, self.text_color)

        # 閉じ方のヒント（ウィンドウ下部）
        hint = "ESC:CLOSE"
        hint_y = self.y + self.height - 10
        pyxel.text(text_x, hint_y, hint, self.text_color)