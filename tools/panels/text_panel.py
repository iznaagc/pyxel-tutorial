"""テキスト一覧パネル。

カテゴリ（messages / selections / telops）でグループ分けして
テキストIDを一覧表示し、カーソルで選択する。
"""

import pyxel

from panels.base_panel import BasePanel

# カテゴリ定義（表示順）
CATEGORIES = [
    ("messages", "Messages"),
    ("selections", "Selections"),
    ("telops", "Telops"),
]

# 描画定数
ITEM_HEIGHT = 14
HEADER_HEIGHT = 18
CURSOR_CHAR = ">"
SCROLL_MARGIN = 2


class TextPanel(BasePanel):
    """テキスト一覧パネル。"""

    def __init__(self, x, y, width, height, font):
        super().__init__(x, y, width, height)
        self.font = font
        self._items = []       # [(category, id, display_label), ...]
        self._cursor = 0
        self._scroll_offset = 0
        self._on_select = None  # コールバック: (category, id) を引数に呼ばれる

    def set_data(self, data):
        """JSON データからアイテムリストを構築する。"""
        self._items = []
        for cat_key, cat_label in CATEGORIES:
            if cat_key not in data:
                continue
            entries = data[cat_key]
            # カテゴリヘッダー
            self._items.append((cat_key, None, f"-- {cat_label} --"))
            for entry_id in entries:
                self._items.append((cat_key, entry_id, f"  {entry_id}"))
        self._cursor = 0
        self._scroll_offset = 0
        # 最初の選択可能項目に移動
        self._skip_to_selectable(1)
        self._notify_selection()

    def set_on_select(self, callback):
        """選択変更時のコールバックを設定する。"""
        self._on_select = callback

    def _is_header(self, index):
        """指定インデックスがカテゴリヘッダーか。"""
        if 0 <= index < len(self._items):
            return self._items[index][1] is None
        return False

    def _skip_to_selectable(self, direction):
        """カーソルを次の選択可能項目（ヘッダー以外）にスキップする。"""
        for _ in range(len(self._items)):
            if not self._is_header(self._cursor):
                return
            self._cursor = (self._cursor + direction) % len(self._items)

    def _notify_selection(self):
        """現在選択中のアイテムをコールバックに通知する。"""
        if self._on_select and 0 <= self._cursor < len(self._items):
            cat, entry_id, _ = self._items[self._cursor]
            if entry_id is not None:
                self._on_select(cat, entry_id)

    def _max_visible(self):
        """表示可能な行数を返す。"""
        return (self.height - 4) // ITEM_HEIGHT

    def _ensure_visible(self):
        """カーソルが表示範囲内に収まるようにスクロールする。"""
        max_vis = self._max_visible()
        if self._cursor < self._scroll_offset + SCROLL_MARGIN:
            self._scroll_offset = max(0, self._cursor - SCROLL_MARGIN)
        if self._cursor >= self._scroll_offset + max_vis - SCROLL_MARGIN:
            self._scroll_offset = min(
                len(self._items) - max_vis,
                self._cursor - max_vis + SCROLL_MARGIN + 1,
            )
        self._scroll_offset = max(0, self._scroll_offset)

    def update(self):
        if not self.is_active or not self._items:
            return

        moved = False
        if pyxel.btnp(pyxel.KEY_UP, hold=10, repeat=5):
            self._cursor = (self._cursor - 1) % len(self._items)
            self._skip_to_selectable(-1)
            moved = True
        elif pyxel.btnp(pyxel.KEY_DOWN, hold=10, repeat=5):
            self._cursor = (self._cursor + 1) % len(self._items)
            self._skip_to_selectable(1)
            moved = True

        if moved:
            self._ensure_visible()
            self._notify_selection()

    def draw(self):
        font = self.font

        # パネル背景
        pyxel.rect(self.x, self.y, self.width, self.height, 0)

        # 枠線（アクティブ時は白、非アクティブは灰色）
        border_color = 7 if self.is_active else 13
        pyxel.rectb(self.x, self.y, self.width, self.height, border_color)

        # アイテム一覧
        max_vis = self._max_visible()
        for i in range(max_vis):
            idx = self._scroll_offset + i
            if idx >= len(self._items):
                break

            cat, entry_id, label = self._items[idx]
            draw_y = self.y + 2 + i * ITEM_HEIGHT

            if entry_id is None:
                # カテゴリヘッダー
                pyxel.text(self.x + 6, draw_y, label, 10, font)
            else:
                # 通常アイテム
                color = 7 if idx == self._cursor else 5
                if idx == self._cursor:
                    pyxel.text(self.x + 4, draw_y, CURSOR_CHAR, 7, font)
                pyxel.text(self.x + 14, draw_y, label, color, font)

        # スクロールインジケーター
        if self._scroll_offset > 0:
            pyxel.text(self.x + self.width - 12, self.y + 2, "^", 13, font)
        if self._scroll_offset + max_vis < len(self._items):
            pyxel.text(self.x + self.width - 12,
                       self.y + self.height - 12, "v", 13, font)
