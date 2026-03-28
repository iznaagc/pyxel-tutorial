import pyxel

import config
from ui.window import BaseWindow


# --- 定数 ---

# メッセージウィンドウのデフォルトサイズ・位置（480x270画面下部に配置）
MSG_WINDOW_X = 8
MSG_WINDOW_Y = 182
MSG_WINDOW_WIDTH = 464
MSG_WINDOW_HEIGHT = 80

# 名前ウィンドウのサイズ
NAME_WINDOW_HEIGHT = 24
NAME_WINDOW_PADDING = 6

# 顔グラフィックのサイズ
FACE_SIZE = 56
FACE_PADDING = 6

# テキスト関連
TEXT_PADDING = 8
LINE_HEIGHT = 20
MAX_LINES = 3

# テキスト表示速度（フレーム数 / 1文字）
TEXT_SPEED_FAST = 1
TEXT_SPEED_NORMAL = 2
TEXT_SPEED_SLOW = 4

# メッセージ送りアイコンのアニメーション
ICON_BLINK_INTERVAL = 20


class MessageWindow(BaseWindow):
    """メッセージウィンドウ。
    キャラクターの会話や説明テキストを表示するためのウィンドウ。

    機能:
    - 1文字ずつテキスト表示（表示速度変更可能）
    - キャラクター名の表示（左上に名前ウィンドウ）
    - 顔グラフィックの表示（ウィンドウ左側）
    - メッセージキュー（複数メッセージの連続表示）
    - メッセージ送りアイコンのアニメーション表示
    - 自動送り機能
    """

    def __init__(self, x=MSG_WINDOW_X, y=MSG_WINDOW_Y,
                 width=MSG_WINDOW_WIDTH, height=MSG_WINDOW_HEIGHT,
                 bg_color=1, border_color=7, text_color=7,
                 has_border=True, semi_transparent=True,
                 confirm_key=pyxel.KEY_RETURN,
                 text_speed=TEXT_SPEED_NORMAL):
        """
        Args:
            confirm_key: 決定キー（デフォルト: Enterキー）
            text_speed: テキスト表示速度（フレーム/文字、小さいほど速い）
        """
        super().__init__(x, y, width, height,
                         bg_color, border_color,
                         has_border, semi_transparent)
        self.text_color = text_color
        self.confirm_key = confirm_key
        self.text_speed = text_speed

        # メッセージキュー: 各要素は dict
        # {"text": str, "name": str|None, "face": tuple|None, "auto": bool}
        self._queue = []

        # 現在表示中のメッセージ情報
        self._current_msg = None
        self._lines = []           # 現在のメッセージを行分割したリスト
        self._char_index = 0       # 表示済み文字数
        self._total_chars = 0      # 現在メッセージの総文字数
        self._frame_counter = 0    # テキスト表示用フレームカウンタ
        self._display_complete = False  # 現在メッセージの表示完了フラグ

        # 自動送り
        self._auto_advance = False
        self._auto_wait_frames = 60  # 自動送り時の待機フレーム数
        self._auto_counter = 0

    # --- 公開メソッド ---

    def show(self, messages):
        """メッセージを設定してウィンドウを開く。

        Args:
            messages: メッセージのリスト。各要素は以下の形式:
                - str: テキストのみ（名前・顔グラなし）
                - dict: {
                    "text": str,            # 表示テキスト（必須）
                    "name": str|None,       # キャラクター名（省略可）
                    "face": tuple|None,     # 顔グラ (img, u, v, w, h)（省略可）
                    "auto": bool,           # 自動送り（省略時False）
                  }
        """
        self._queue.clear()
        for msg in messages:
            if isinstance(msg, str):
                self._queue.append({
                    "text": msg, "name": None, "face": None, "auto": False
                })
            else:
                self._queue.append({
                    "text": msg.get("text", ""),
                    "name": msg.get("name"),
                    "face": msg.get("face"),
                    "auto": msg.get("auto", False),
                })
        self.open()
        self._advance_message()

    def set_text_speed(self, speed):
        """テキスト表示速度を変更する。

        Args:
            speed: フレーム/文字（TEXT_SPEED_FAST, TEXT_SPEED_NORMAL, TEXT_SPEED_SLOW）
        """
        self.text_speed = speed

    @property
    def is_busy(self):
        """メッセージ表示中（キューが残っている or テキスト表示途中）か。"""
        return self.is_open

    # --- 内部メソッド ---

    def _advance_message(self):
        """キューから次のメッセージを取り出して表示開始する。"""
        if not self._queue:
            self.close()
            return

        self._current_msg = self._queue.pop(0)
        self._auto_advance = self._current_msg["auto"]
        self._auto_counter = 0

        # テキストを行分割（最大3行）
        raw_text = self._current_msg["text"]
        self._lines = self._split_lines(raw_text)
        self._total_chars = sum(len(line) for line in self._lines)
        self._char_index = 0
        self._frame_counter = 0
        self._display_complete = False

    def _split_lines(self, text):
        """テキストを改行文字で分割し、最大MAX_LINES行にする。"""
        lines = text.split("\n")
        return lines[:MAX_LINES]

    def _get_text_area_x(self):
        """テキスト描画開始のx座標を返す（顔グラの有無で変わる）。"""
        if self._current_msg and self._current_msg["face"]:
            return self.x + FACE_PADDING + FACE_SIZE + FACE_PADDING + 2
        return self.x + TEXT_PADDING

    # --- update / draw ---

    def update(self):
        """メッセージウィンドウの入力・状態更新。"""
        if not self.is_open or self._current_msg is None:
            return

        if not self._display_complete:
            # テキスト表示途中
            self._frame_counter += 1
            if self._frame_counter >= self.text_speed:
                self._frame_counter = 0
                self._char_index += 1
                if self._char_index >= self._total_chars:
                    self._char_index = self._total_chars
                    self._display_complete = True

            # 決定キーで即時表示完了
            if pyxel.btnp(self.confirm_key) or pyxel.btnp(pyxel.KEY_SPACE):
                self._char_index = self._total_chars
                self._display_complete = True
        else:
            # テキスト表示完了後
            if self._auto_advance:
                self._auto_counter += 1
                if self._auto_counter >= self._auto_wait_frames:
                    self._advance_message()
            else:
                if pyxel.btnp(self.confirm_key) or pyxel.btnp(pyxel.KEY_SPACE):
                    self._advance_message()

    def draw(self):
        """メッセージウィンドウを描画する。"""
        if not self.is_open or self._current_msg is None:
            return

        # ウィンドウ背景・枠線（BaseWindow）
        super().draw()

        # 顔グラフィック
        self._draw_face()

        # 名前ウィンドウ
        self._draw_name_window()

        # テキスト描画（1文字ずつ）
        self._draw_text()

        # メッセージ送りアイコン
        if self._display_complete and not self._auto_advance:
            self._draw_next_icon()

    def _draw_face(self):
        """顔グラフィックを描画する。"""
        face = self._current_msg.get("face")
        if not face:
            return

        img, u, v, w, h = face
        face_x = self.x + FACE_PADDING
        face_y = self.y + (self.height - h) // 2

        # 顔グラの背景枠
        pyxel.rectb(face_x - 1, face_y - 1, w + 2, h + 2, self.border_color)
        pyxel.blt(face_x, face_y, img, u, v, w, h, colkey=0)

    def _draw_name_window(self):
        """キャラクター名ウィンドウを描画する。"""
        name = self._current_msg.get("name")
        if not name:
            return

        font = config.FONT
        # 名前ウィンドウのサイズを名前の実際の描画幅に合わせる
        name_text_w = font.text_width(name) if font else len(name) * 4
        name_width = name_text_w + NAME_WINDOW_PADDING * 2
        name_x = self.x + 4
        name_y = self.y - NAME_WINDOW_HEIGHT

        # 半透明の場合はditherを適用
        if self.semi_transparent:
            pyxel.dither(0.5)

        pyxel.rect(name_x, name_y, name_width, NAME_WINDOW_HEIGHT,
                   self.bg_color)

        if self.semi_transparent:
            pyxel.dither(1.0)

        if self.has_border:
            pyxel.rectb(name_x, name_y, name_width, NAME_WINDOW_HEIGHT,
                        self.border_color)

        # 名前テキスト
        text_x = name_x + NAME_WINDOW_PADDING
        text_y = name_y + (NAME_WINDOW_HEIGHT - config.FONT_SIZE) // 2
        pyxel.text(text_x, text_y, name, self.text_color, font)

    def _draw_text(self):
        """テキストを1文字ずつ描画する。"""
        font = config.FONT
        text_x = self._get_text_area_x()
        text_y = self.y + TEXT_PADDING
        chars_drawn = 0

        for i, line in enumerate(self._lines):
            y = text_y + i * LINE_HEIGHT
            # この行で表示する文字数を計算
            remaining = self._char_index - chars_drawn
            if remaining <= 0:
                break
            visible = line[:remaining]
            pyxel.text(text_x, y, visible, self.text_color, font)
            chars_drawn += len(line)

    def _draw_next_icon(self):
        """メッセージ送りアイコン（▼）をアニメーション付きで描画する。"""
        # 点滅アニメーション
        if (pyxel.frame_count // (ICON_BLINK_INTERVAL // 2)) % 2 == 0:
            font = config.FONT
            icon_x = self.x + self.width - 18
            # 上下に揺れるアニメーション
            bounce = (pyxel.frame_count // 8) % 2
            icon_y = self.y + self.height - 20 + bounce
            pyxel.text(icon_x, icon_y, "v", self.text_color, font)
