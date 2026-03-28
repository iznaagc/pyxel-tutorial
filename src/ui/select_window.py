import pyxel

import config
from ui.window import BaseWindow


# --- カーソルリピート定数 ---
REPEAT_INITIAL_WAIT = 10   # 長押し開始までの待機フレーム数
REPEAT_INTERVAL = 5        # リピート移動の間隔フレーム数

# --- 描画定数 ---
CURSOR_CHAR = ">"
CURSOR_MARGIN = 4          # カーソル文字とラベルの間のスペース（px）
SCROLL_INDICATOR_HEIGHT = 10  # スクロールインジケータの高さ（px）

# --- ページ送り定数 ---
PAGE_NEXT_LABEL = "次のページへ >"
PAGE_PREV_LABEL = "< 前のページへ"
PAGE_NAV_COLOR = 10        # ナビ項目の文字色（Pyxelパレット10=黄色）


class SelectWindow(BaseWindow):
    """選択肢ウィンドウ。
    プレイヤーに選択肢を提示し、カーソルで選ばせるウィンドウ。

    機能:
    - カーソル移動（上下キー、ループ対応）
    - 長押しリピート（初回待機後に連続移動）
    - 決定キーで選択確定
    - キャンセルキーで指定位置を返す
    - テキスト内容に合わせた自動リサイズ
    - スクロール（max_visible で表示上限、カーソル追従でスクロール）
    - ページ送り（page_size でページ分割、ナビ項目で切り替え）
    """

    def __init__(self, x, y, items,
                 width=0, height=0,
                 bg_color=1, border_color=7, text_color=7,
                 has_border=True, semi_transparent=False,
                 auto_resize=True,
                 confirm_key=pyxel.KEY_RETURN,
                 cancel_key=pyxel.KEY_ESCAPE,
                 cancel_index=-1,
                 initial_cursor=0,
                 max_visible=0,
                 page_size=0):
        """
        Args:
            x, y: ウィンドウ左上の座標
            items: 選択肢のリスト。各要素は str または {"label": str, ...} の dict
            width, height: ウィンドウサイズ（auto_resize=True なら自動計算）
            cancel_key: キャンセルキー（デフォルト: ESC）
            cancel_index: キャンセル時に返すインデックス（-1 でキャンセル無効）
            initial_cursor: 初期カーソル位置（元のアイテムインデックス）
            max_visible: スクロール表示上限（0=制限なし、page_sizeと排他）
            page_size: 1ページあたりの表示項目数（0=ページ送りなし、max_visibleと排他）
        """
        super().__init__(x, y, width, height,
                         bg_color, border_color, text_color,
                         has_border, semi_transparent,
                         auto_resize=auto_resize)

        self.confirm_key = confirm_key
        self.cancel_key = cancel_key
        self.cancel_index = cancel_index
        self.max_visible = max_visible
        self.page_size = page_size

        # 選択肢を正規化（str or dict → ラベル文字列リスト）
        self._items = []
        for item in items:
            if isinstance(item, str):
                self._items.append(item)
            else:
                self._items.append(item.get("label", ""))

        # カーソル状態（スクロールモード用）
        self._cursor = initial_cursor
        self._selected = None

        # スクロール状態
        self._scroll_offset = 0

        # ページ送り状態
        self._current_page = 0
        self._page_cursor = 0

        # ページ送りモードなら初期カーソルからページを計算
        if self._has_pagination:
            self._goto_item(initial_cursor)

        # 自動リサイズ
        if self.auto_resize:
            self._resize_to_fit_items()

    # =================================================================
    # プロパティ
    # =================================================================

    @property
    def cursor(self):
        """現在のカーソルが指す元アイテムのインデックス。
        ページ送りモードでナビ項目上の場合は -1。
        """
        if self._has_pagination:
            _, index_map = self._build_page_display()
            if 0 <= self._page_cursor < len(index_map):
                idx = index_map[self._page_cursor]
                return idx if idx is not None else -1
            return -1
        return self._cursor

    @cursor.setter
    def cursor(self, value):
        if self._has_pagination:
            self._goto_item(value)
        else:
            self._cursor = value % len(self._items)

    @property
    def selected(self):
        """最後に確定された選択インデックス。未選択なら None。"""
        return self._selected

    @property
    def item_count(self):
        """選択肢の数。"""
        return len(self._items)

    @property
    def _visible_count(self):
        """スクロールモードで実際に表示する項目数。"""
        if self.max_visible > 0:
            return min(self.max_visible, len(self._items))
        return len(self._items)

    @property
    def _has_scroll(self):
        """スクロールが必要か。"""
        return (self.max_visible > 0
                and not self._has_pagination
                and len(self._items) > self.max_visible)

    @property
    def _has_pagination(self):
        """ページ送りが有効か。"""
        return self.page_size > 0 and len(self._items) > self.page_size

    @property
    def _total_pages(self):
        """総ページ数。"""
        if self.page_size <= 0:
            return 1
        return (len(self._items) + self.page_size - 1) // self.page_size

    # =================================================================
    # 公開メソッド
    # =================================================================

    def open(self, items=None, initial_cursor=0):
        """ウィンドウを開く。

        Args:
            items: 新しい選択肢リスト（省略時は前回の内容を維持）
            initial_cursor: カーソル初期位置（元のアイテムインデックス）
        """
        if items is not None:
            self._items = []
            for item in items:
                if isinstance(item, str):
                    self._items.append(item)
                else:
                    self._items.append(item.get("label", ""))
            if self.auto_resize:
                self._resize_to_fit_items()

        self._selected = None

        if self._has_pagination:
            self._goto_item(initial_cursor)
        else:
            self._cursor = initial_cursor
            self._scroll_offset = 0
            self._adjust_scroll()

        super().open()

    def reset(self):
        """カーソル位置と選択結果をリセットする。"""
        self._cursor = 0
        self._scroll_offset = 0
        self._current_page = 0
        self._page_cursor = 0
        self._selected = None

    # =================================================================
    # ページ送り内部メソッド
    # =================================================================

    def _build_page_display(self):
        """現在ページの表示項目リストとインデックスマップを構築する。

        Returns:
            (labels, index_map): labels は表示文字列リスト、
            index_map は各要素の元インデックス（ナビ項目は None）
        """
        if not self._has_pagination:
            return list(self._items), list(range(len(self._items)))

        start = self._current_page * self.page_size
        end = min(start + self.page_size, len(self._items))

        labels = []
        index_map = []

        # 前ページナビ
        if self._current_page > 0:
            labels.append(PAGE_PREV_LABEL)
            index_map.append(None)

        # 実アイテム
        for i in range(start, end):
            labels.append(self._items[i])
            index_map.append(i)

        # 次ページナビ
        if self._current_page < self._total_pages - 1:
            labels.append(PAGE_NEXT_LABEL)
            index_map.append(None)

        return labels, index_map

    def _goto_item(self, item_index):
        """指定アイテムインデックスのページ・カーソル位置に移動する。"""
        if len(self._items) == 0:
            self._current_page = 0
            self._page_cursor = 0
            return

        item_index = max(0, min(item_index, len(self._items) - 1))
        self._current_page = item_index // self.page_size

        # ページ内でのカーソル位置を計算
        page_start = self._current_page * self.page_size
        item_offset = item_index - page_start

        # 前ページナビがある場合はオフセット+1
        if self._current_page > 0:
            item_offset += 1

        self._page_cursor = item_offset

    def _navigate_page(self, direction):
        """ページを切り替える。direction: 1=次, -1=前。"""
        self._current_page += direction
        self._current_page = max(0, min(self._current_page,
                                        self._total_pages - 1))

        display, _ = self._build_page_display()

        if direction > 0:
            # 次ページ: 最初の実アイテムにカーソル
            self._page_cursor = 1 if self._current_page > 0 else 0
        else:
            # 前ページ: 最後の実アイテムにカーソル
            # (次ページナビがある場合はその手前)
            if self._current_page < self._total_pages - 1:
                self._page_cursor = len(display) - 2
            else:
                self._page_cursor = len(display) - 1

    # =================================================================
    # スクロール内部メソッド
    # =================================================================

    def _adjust_scroll(self):
        """カーソル位置に応じてスクロールオフセットを調整する。"""
        if not self._has_scroll:
            self._scroll_offset = 0
            return

        if self._cursor < self._scroll_offset:
            self._scroll_offset = self._cursor

        if self._cursor >= self._scroll_offset + self.max_visible:
            self._scroll_offset = self._cursor - self.max_visible + 1

        max_offset = len(self._items) - self.max_visible
        self._scroll_offset = max(0, min(self._scroll_offset, max_offset))

    # =================================================================
    # リサイズ
    # =================================================================

    def _resize_to_fit_items(self):
        """選択肢の内容に合わせてウィンドウサイズを調整する。"""
        font = config.FONT
        cursor_w = self._get_cursor_width()

        # 幅: 全アイテム＋ナビラベルの最大幅
        max_w = 0
        for label in self._items:
            w = font.text_width(label) if font else len(label) * 8
            max_w = max(max_w, w)

        if self._has_pagination:
            for nav_label in (PAGE_PREV_LABEL, PAGE_NEXT_LABEL):
                w = font.text_width(nav_label) if font else len(nav_label) * 8
                max_w = max(max_w, w)

        self.width = cursor_w + max_w + self._text_padding * 2

        # 高さ
        if self._has_pagination:
            # ページ内の最大表示行数 = page_size + ナビ項目数
            nav_count = min(2, self._total_pages - 1)
            max_display = self.page_size + nav_count
            self.height = max_display * self._line_height + self._text_padding * 2
        elif self._has_scroll:
            visible = self._visible_count
            self.height = visible * self._line_height + self._text_padding * 2
            self.height += SCROLL_INDICATOR_HEIGHT * 2
        else:
            self.height = (len(self._items) * self._line_height
                           + self._text_padding * 2)

    def _get_cursor_width(self):
        """カーソル文字＋マージンの描画幅を返す。"""
        font = config.FONT
        char_w = font.text_width(CURSOR_CHAR) if font else 8
        return char_w + CURSOR_MARGIN

    # =================================================================
    # update
    # =================================================================

    def update(self):
        """入力処理。選択が確定したらインデックスを返す。

        Returns:
            int: 選択されたインデックス（確定時）
            None: まだ選択されていない
        """
        if not self.is_open or not self.is_active:
            return None

        if self._has_pagination:
            return self._update_pagination()
        else:
            return self._update_scroll()

    def _update_scroll(self):
        """スクロールモード（及び通常モード）の入力処理。"""
        # カーソル移動
        if pyxel.btnp(pyxel.KEY_UP, REPEAT_INITIAL_WAIT, REPEAT_INTERVAL):
            self._cursor = (self._cursor - 1) % len(self._items)
            self._adjust_scroll()
        if pyxel.btnp(pyxel.KEY_DOWN, REPEAT_INITIAL_WAIT, REPEAT_INTERVAL):
            self._cursor = (self._cursor + 1) % len(self._items)
            self._adjust_scroll()

        # 決定
        if pyxel.btnp(self.confirm_key) or pyxel.btnp(pyxel.KEY_SPACE):
            self._selected = self._cursor
            self.close()
            return self._selected

        # キャンセル
        if self.cancel_index >= 0 and pyxel.btnp(self.cancel_key):
            self._selected = self.cancel_index
            self.close()
            return self._selected

        return None

    def _update_pagination(self):
        """ページ送りモードの入力処理。"""
        display, index_map = self._build_page_display()
        display_count = len(display)

        # カーソル移動（ページ内でループ）
        if pyxel.btnp(pyxel.KEY_UP, REPEAT_INITIAL_WAIT, REPEAT_INTERVAL):
            self._page_cursor = (self._page_cursor - 1) % display_count
        if pyxel.btnp(pyxel.KEY_DOWN, REPEAT_INITIAL_WAIT, REPEAT_INTERVAL):
            self._page_cursor = (self._page_cursor + 1) % display_count

        # 決定
        if pyxel.btnp(self.confirm_key) or pyxel.btnp(pyxel.KEY_SPACE):
            idx = index_map[self._page_cursor]
            if idx is None:
                # ナビ項目 → ページ切り替え
                if (self._page_cursor == 0
                        and self._current_page > 0):
                    self._navigate_page(-1)
                else:
                    self._navigate_page(1)
            else:
                # 実アイテム → 選択確定
                self._selected = idx
                self.close()
                return self._selected

        # キャンセル
        if self.cancel_index >= 0 and pyxel.btnp(self.cancel_key):
            self._selected = self.cancel_index
            self.close()
            return self._selected

        return None

    # =================================================================
    # draw
    # =================================================================

    def draw(self):
        """選択肢ウィンドウを描画する。"""
        if not self.is_open:
            return

        # 背景・枠線（BaseWindow）
        super().draw()

        if self._has_pagination:
            self._draw_pagination()
        else:
            self._draw_scroll()

    def _draw_scroll(self):
        """スクロールモード（及び通常モード）の描画。"""
        font = config.FONT
        cursor_w = self._get_cursor_width()
        x = self.x + self._text_padding
        y = self.y + self._text_padding

        if self._has_scroll:
            self._draw_scroll_indicator_up(x, y, cursor_w)
            y += SCROLL_INDICATOR_HEIGHT

        visible = self._visible_count
        for vi in range(visible):
            item_index = self._scroll_offset + vi
            if item_index >= len(self._items):
                break
            label = self._items[item_index]
            iy = y + vi * self._line_height

            if item_index == self._cursor:
                pyxel.text(x, iy, CURSOR_CHAR, self.text_color, font)
                pyxel.text(x + cursor_w, iy, label, self.text_color, font)
            else:
                pyxel.text(x + cursor_w, iy, label, self.text_color, font)

        if self._has_scroll:
            bottom_y = y + visible * self._line_height
            self._draw_scroll_indicator_down(x, bottom_y, cursor_w)

    def _draw_pagination(self):
        """ページ送りモードの描画。"""
        font = config.FONT
        cursor_w = self._get_cursor_width()
        x = self.x + self._text_padding
        y = self.y + self._text_padding

        display, index_map = self._build_page_display()

        for vi, label in enumerate(display):
            iy = y + vi * self._line_height
            is_nav = index_map[vi] is None
            color = PAGE_NAV_COLOR if is_nav else self.text_color

            if vi == self._page_cursor:
                pyxel.text(x, iy, CURSOR_CHAR, color, font)
                pyxel.text(x + cursor_w, iy, label, color, font)
            else:
                pyxel.text(x + cursor_w, iy, label, color, font)

        # ページインジケータ（右下）
        page_text = f"{self._current_page + 1}/{self._total_pages}"
        page_w = font.text_width(page_text) if font else len(page_text) * 8
        px = self.x + self.width - page_w - self._text_padding
        py = self.y + self.height - config.FONT_SIZE - 4
        pyxel.text(px, py, page_text, 13, font)

    def _draw_scroll_indicator_up(self, x, y, cursor_w):
        """上方向にスクロール可能なことを示すインジケータ。"""
        if self._scroll_offset > 0:
            font = config.FONT
            center_x = (x + cursor_w
                        + (self.width - self._text_padding * 2 - cursor_w) // 2)
            pyxel.text(center_x - 4, y, "...", 13, font)

    def _draw_scroll_indicator_down(self, x, y, cursor_w):
        """下方向にスクロール可能なことを示すインジケータ。"""
        if self._scroll_offset + self.max_visible < len(self._items):
            font = config.FONT
            center_x = (x + cursor_w
                        + (self.width - self._text_padding * 2 - cursor_w) // 2)
            pyxel.text(center_x - 4, y, "...", 13, font)
