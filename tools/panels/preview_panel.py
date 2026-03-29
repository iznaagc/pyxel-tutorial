"""プレビューパネル。

選択されたテキストIDに応じて、実際のゲームUIコンポーネントで
プレビュー表示する。
"""

import pyxel

from panels.base_panel import BasePanel
from ui.message_window import MessageWindow
from ui.select_window import SelectWindow
from ui.telop_window import TelopWindow


# テロップの静止表示用スクロール位置（画面中央付近）
TELOP_PREVIEW_SCROLL_RATIO = 0.3


class PreviewPanel(BasePanel):
    """プレビューパネル。"""

    def __init__(self, x, y, width, height, font):
        super().__init__(x, y, width, height)
        self.font = font
        self._category = None
        self._entry_id = None
        self._data = None

        # プレビュー用UIコンポーネント
        self._msg_window = None
        self._select_window = None
        self._telop_window = None
        self._info_lines = []  # メタ情報表示用

    def set_data(self, data):
        """JSON データへの参照を保持する。"""
        self._data = data

    def show_preview(self, category, entry_id):
        """指定カテゴリ・IDのプレビューを表示する。"""
        self._category = category
        self._entry_id = entry_id
        self._msg_window = None
        self._select_window = None
        self._telop_window = None
        self._info_lines = []

        if not self._data or category not in self._data:
            return
        entries = self._data[category]
        if entry_id not in entries:
            return

        entry = entries[entry_id]

        if category == "messages":
            self._preview_messages(entry_id, entry)
        elif category == "selections":
            self._preview_selection(entry_id, entry)
        elif category == "telops":
            self._preview_telop(entry_id, entry)

    def _preview_messages(self, msg_id, messages):
        """メッセージのプレビュー。全文表示状態で表示する。"""
        self._info_lines = [
            f"ID: {msg_id}",
            f"Pages: {len(messages)}",
        ]

        # 最初のメッセージをプレビュー
        if messages:
            mw = MessageWindow()
            mw.show(messages)
            # 全文表示状態にする
            mw._char_index = mw._total_chars
            mw._display_complete = True
            mw.activate()
            self._msg_window = mw

    def _preview_selection(self, sel_id, sel_data):
        """選択肢のプレビュー。"""
        items = sel_data["items"]
        cancel_idx = sel_data.get("cancel_index", -1)
        semi = sel_data.get("semi_transparent", False)

        self._info_lines = [
            f"ID: {sel_id}",
            f"Items: {len(items)}",
            f"Cancel: {cancel_idx}",
        ]
        if semi:
            self._info_lines.append("Semi-transparent: Yes")
        if "desc" in sel_data:
            desc = sel_data["desc"]
            name = desc.get("name", "")
            self._info_lines.append(f"Desc: [{name}]")

        # 選択肢ウィンドウをプレビュー領域内に配置
        sw = SelectWindow(
            x=self.x + 10, y=self.y + 70,
            items=items,
            cancel_index=cancel_idx,
            semi_transparent=semi,
        )
        sw.open()
        sw.activate()
        self._select_window = sw

        # descがある場合はメッセージウィンドウも表示
        if "desc" in sel_data:
            mw = MessageWindow()
            mw.show([sel_data["desc"]])
            mw._char_index = mw._total_chars
            mw._display_complete = True
            self._msg_window = mw

    def _preview_telop(self, telop_id, telop_data):
        """テロップのプレビュー。途中位置で静止表示する。"""
        lines = telop_data["lines"]
        speed = telop_data.get("scroll_speed", 1.0)

        self._info_lines = [
            f"ID: {telop_id}",
            f"Lines: {len(lines)}",
            f"Speed: {speed}",
        ]

        telop = TelopWindow(scroll_speed=speed, text_color=7)
        telop.show(lines)
        # 途中位置で静止表示（メタ情報の下から表示されるよう調整）
        info_offset = 50
        total_h = len(lines) * 24
        telop._scroll_y = -(total_h * TELOP_PREVIEW_SCROLL_RATIO
                            - self.height // 2) + info_offset
        telop.y = int(telop._scroll_y)
        telop.pause()
        self._telop_window = telop

    def update(self):
        pass

    def draw(self):
        font = self.font

        # パネル背景
        pyxel.rect(self.x, self.y, self.width, self.height, 0)

        # 枠線
        border_color = 7 if self.is_active else 13
        pyxel.rectb(self.x, self.y, self.width, self.height, border_color)

        if not self._entry_id:
            pyxel.text(self.x + 10, self.y + 10,
                       "Select an item to preview", 5, font)
            return

        # メタ情報
        for i, line in enumerate(self._info_lines):
            pyxel.text(self.x + 6, self.y + 4 + i * 12, line, 13, font)

        # プレビュー描画
        if self._telop_window:
            self._telop_window.draw()
        if self._select_window:
            self._select_window.draw()
        if self._msg_window:
            self._msg_window.draw()
