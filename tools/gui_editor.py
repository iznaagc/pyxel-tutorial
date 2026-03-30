"""PySide6 テキストエディタ。

テキストデータの閲覧・編集・コンパイルを行うGUIアプリ。

使い方:
    .venv/Scripts/python tools/gui_editor.py
"""

import copy
import json
import os
import subprocess
import sys

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TOOLS_DIR, ".."))

TEXT_DIR = os.path.join(_PROJECT_ROOT, "data", "text")
COMPILER_PATH = os.path.join(_TOOLS_DIR, "compiler.py")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QStackedWidget, QPushButton,
    QStatusBar, QMenuBar, QListWidget, QMessageBox, QInputDialog,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import (
    QAction, QKeySequence, QFont, QFontDatabase, QPainter, QColor, QPen,
    QBrush, QPixmap, QUndoStack, QUndoCommand,
)

# カテゴリ表示名
CATEGORY_LABELS = {
    "messages": "Messages",
    "selections": "Selections",
    "telops": "Telops",
}
CATEGORIES = ["messages", "selections", "telops"]

# Pyxel パレット (16色)
PYXEL_PALETTE = [
    QColor(0, 0, 0),         # 0: Black
    QColor(43, 51, 95),       # 1: Dark Blue (bg)
    QColor(126, 32, 114),     # 2: Purple
    QColor(25, 149, 156),     # 3: Cyan
    QColor(139, 72, 82),      # 4: Red
    QColor(57, 92, 152),      # 5: Blue
    QColor(169, 193, 255),    # 6: Light Blue
    QColor(238, 238, 238),    # 7: White
    QColor(212, 24, 108),     # 8: Pink
    QColor(211, 132, 65),     # 9: Orange
    QColor(233, 195, 91),     # 10: Yellow
    QColor(112, 198, 169),    # 11: Light Green
    QColor(118, 150, 222),    # 12: Light Purple
    QColor(163, 163, 163),    # 13: Gray
    QColor(255, 151, 152),    # 14: Light Red
    QColor(237, 199, 176),    # 15: Tan
]

# ゲーム画面サイズ
GAME_WIDTH = 480
GAME_HEIGHT = 270

# フォントパス
FONT_PATH = os.path.join(_PROJECT_ROOT, "assets", "fonts", "madoufmg.ttf")

# 文字数上限
MSG_CHAR_LIMIT = 28

# メッセージウィンドウの定数 (src/ui/message_window.py と同じ)
MSG_X = 8
MSG_Y = 182
MSG_W = 464
MSG_H = 80
MSG_TEXT_PADDING = 8
MSG_LINE_HEIGHT = 20
MSG_MAX_LINES = 3
NAME_WINDOW_HEIGHT = 24
NAME_WINDOW_PADDING = 6

# 選択肢ウィンドウの定数 (src/ui/select_window.py と同じ)
SEL_TEXT_PADDING = 8
SEL_LINE_HEIGHT = 20
SEL_CURSOR_CHAR = ">"
SEL_CURSOR_MARGIN = 4

# テロップの定数 (src/ui/telop_window.py と同じ)
TELOP_LINE_HEIGHT = 24
TELOP_TEXT_PADDING = 8


class PreviewPanel(QWidget):
    """QPainter でゲームUIを再現描画するプレビューパネル。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self._category = None   # "messages" | "selections" | "telops"
        self._data = None       # 現在のエントリデータ
        self._page = 0          # messages のページ番号
        self._warnings = []     # バリデーション警告リスト

        # ゲーム用フォント読み込み
        self._font_id = -1
        self._game_font = None
        if os.path.isfile(FONT_PATH):
            self._font_id = QFontDatabase.addApplicationFont(FONT_PATH)
            if self._font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(self._font_id)
                if families:
                    self._game_font = QFont(families[0], 12)
        # フォールバック
        if self._game_font is None:
            self._game_font = QFont("Yu Gothic UI", 10)

    def set_preview(self, category, data, page=0):
        """プレビュー対象を設定する。"""
        self._category = category
        self._data = data
        self._page = page
        self._warnings = self._validate(category, data)
        self.update()

    def get_warnings(self):
        """現在のバリデーション警告を返す。"""
        return self._warnings

    def _validate(self, category, data):
        """データのバリデーションを行い、警告リストを返す。"""
        warnings = []
        if category != "messages" or not isinstance(data, list):
            return warnings
        for i, msg in enumerate(data):
            text = msg if isinstance(msg, str) else msg.get("text", "")
            for li, line in enumerate(text.split("\n")):
                if len(line) > MSG_CHAR_LIMIT:
                    warnings.append(
                        f"Page {i+1}, Line {li+1}: {len(line)}文字 "
                        f"(上限{MSG_CHAR_LIMIT})")
        return warnings

    def clear_preview(self):
        """プレビューをクリアする。"""
        self._category = None
        self._data = None
        self.update()

    def set_page(self, page):
        """メッセージのページを切り替える。"""
        self._page = page
        self.update()

    def paintEvent(self, event):
        """ゲーム画面をスケーリングして描画する。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # ゲーム画面のオフスクリーンバッファ
        pixmap = QPixmap(GAME_WIDTH, GAME_HEIGHT)
        pixmap.fill(PYXEL_PALETTE[0])

        buf = QPainter(pixmap)
        buf.setRenderHint(QPainter.Antialiasing, False)

        if self._category and self._data:
            if self._category == "messages":
                self._draw_message(buf)
            elif self._category == "selections":
                self._draw_selection(buf)
            elif self._category == "telops":
                self._draw_telop(buf)
        else:
            # 何も選択されていない場合
            buf.setFont(self._game_font)
            buf.setPen(PYXEL_PALETTE[13])
            buf.drawText(GAME_WIDTH // 2 - 60, GAME_HEIGHT // 2,
                         "No Preview")

        buf.end()

        # ウィジェットサイズに合わせてスケーリング描画
        w = self.width()
        h = self.height()
        scale = min(w / GAME_WIDTH, h / GAME_HEIGHT)
        scaled_w = int(GAME_WIDTH * scale)
        scaled_h = int(GAME_HEIGHT * scale)
        offset_x = (w - scaled_w) // 2
        offset_y = (h - scaled_h) // 2

        # 黒で塗りつぶし
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))
        painter.drawPixmap(offset_x, offset_y, scaled_w, scaled_h, pixmap)

        # 枠線
        painter.setPen(QPen(PYXEL_PALETTE[13], 1))
        painter.drawRect(offset_x, offset_y, scaled_w - 1, scaled_h - 1)

        painter.end()

    # --- メッセージウィンドウ描画 ---

    def _draw_message(self, p):
        """メッセージウィンドウをゲーム風に描画する。"""
        if not self._data:
            return

        messages = self._data
        if not isinstance(messages, list) or not messages:
            return

        page = min(self._page, len(messages) - 1)
        msg = messages[page]

        if isinstance(msg, str):
            text = msg
            name = ""
            auto = False
        else:
            text = msg.get("text", "")
            name = msg.get("name", "")
            auto = msg.get("auto", False)

        # 半透明背景（ディザの代わりに半透明で表現）
        bg_color = QColor(PYXEL_PALETTE[1])
        bg_color.setAlpha(160)
        border_color = PYXEL_PALETTE[7]

        # 名前ウィンドウ
        if name:
            p.setFont(self._game_font)
            fm = p.fontMetrics()
            name_text_w = fm.horizontalAdvance(name)
            name_w = name_text_w + NAME_WINDOW_PADDING * 2
            name_x = MSG_X + 4
            name_y = MSG_Y - NAME_WINDOW_HEIGHT

            p.fillRect(name_x, name_y, name_w, NAME_WINDOW_HEIGHT, bg_color)
            p.setPen(QPen(border_color, 1))
            p.drawRect(name_x, name_y, name_w - 1, NAME_WINDOW_HEIGHT - 1)

            p.setPen(PYXEL_PALETTE[7])
            text_y = name_y + (NAME_WINDOW_HEIGHT - fm.height()) // 2 + fm.ascent()
            p.drawText(name_x + NAME_WINDOW_PADDING, text_y, name)

        # メッセージウィンドウ本体
        p.fillRect(MSG_X, MSG_Y, MSG_W, MSG_H, bg_color)
        p.setPen(QPen(border_color, 1))
        p.drawRect(MSG_X, MSG_Y, MSG_W - 1, MSG_H - 1)

        # テキスト描画
        p.setFont(self._game_font)
        p.setPen(PYXEL_PALETTE[7])
        lines = text.split("\n")[:MSG_MAX_LINES]
        fm = p.fontMetrics()
        for i, line in enumerate(lines):
            lx = MSG_X + MSG_TEXT_PADDING
            ly = MSG_Y + MSG_TEXT_PADDING + i * MSG_LINE_HEIGHT + fm.ascent()
            p.drawText(lx, ly, line)

            # 文字数超過行に赤枠表示
            if len(line) > MSG_CHAR_LIMIT:
                p.setPen(QPen(PYXEL_PALETTE[8], 2))  # Pink/Red
                rect_y = MSG_Y + MSG_TEXT_PADDING + i * MSG_LINE_HEIGHT - 2
                p.drawRect(lx - 2, rect_y,
                           MSG_W - MSG_TEXT_PADDING * 2 + 2,
                           MSG_LINE_HEIGHT - 1)
                p.setPen(PYXEL_PALETTE[7])  # 白に戻す

        # 送りアイコン
        icon_x = MSG_X + MSG_W - 18
        icon_y = MSG_Y + MSG_H - 20 + fm.ascent()
        p.setPen(PYXEL_PALETTE[7])
        p.drawText(icon_x, icon_y, "v")

        # auto 表示
        if auto:
            p.setPen(PYXEL_PALETTE[10])
            p.drawText(MSG_X + MSG_TEXT_PADDING, MSG_Y + MSG_H + fm.ascent() + 2,
                       "[AUTO]")

        # ページ表示
        p.setPen(PYXEL_PALETTE[13])
        page_text = f"Page {page + 1}/{len(messages)}"
        page_w = fm.horizontalAdvance(page_text)
        p.drawText(MSG_X + MSG_W - page_w - 4,
                   MSG_Y + MSG_H + fm.ascent() + 2, page_text)

    # --- 選択肢ウィンドウ描画 ---

    def _draw_selection(self, p):
        """選択肢ウィンドウをゲーム風に描画する。"""
        if not self._data:
            return

        items = self._data.get("items", [])
        if not items:
            return

        semi = self._data.get("semi_transparent", False)

        p.setFont(self._game_font)
        fm = p.fontMetrics()
        cursor_w = fm.horizontalAdvance(SEL_CURSOR_CHAR) + SEL_CURSOR_MARGIN

        # ウィンドウサイズ計算（auto_resize の再現）
        max_w = 0
        for item in items:
            w = fm.horizontalAdvance(item)
            max_w = max(max_w, w)
        win_w = cursor_w + max_w + SEL_TEXT_PADDING * 2
        win_h = len(items) * SEL_LINE_HEIGHT + SEL_TEXT_PADDING * 2

        # 画面中央に配置
        win_x = (GAME_WIDTH - win_w) // 2
        win_y = (GAME_HEIGHT - win_h) // 2

        # desc（説明メッセージ）があれば先にメッセージウィンドウを描画
        desc = self._data.get("desc")
        if desc:
            desc_text = desc.get("text", "")
            desc_name = desc.get("name", "")
            # メッセージウィンドウ位置に表示
            bg_color = QColor(PYXEL_PALETTE[1])
            bg_color.setAlpha(160)
            p.fillRect(MSG_X, MSG_Y, MSG_W, MSG_H, bg_color)
            p.setPen(QPen(PYXEL_PALETTE[7], 1))
            p.drawRect(MSG_X, MSG_Y, MSG_W - 1, MSG_H - 1)

            if desc_name:
                name_text_w = fm.horizontalAdvance(desc_name)
                name_w = name_text_w + NAME_WINDOW_PADDING * 2
                name_x = MSG_X + 4
                name_y = MSG_Y - NAME_WINDOW_HEIGHT
                p.fillRect(name_x, name_y, name_w, NAME_WINDOW_HEIGHT, bg_color)
                p.setPen(QPen(PYXEL_PALETTE[7], 1))
                p.drawRect(name_x, name_y, name_w - 1, NAME_WINDOW_HEIGHT - 1)
                p.setPen(PYXEL_PALETTE[7])
                ty = name_y + (NAME_WINDOW_HEIGHT - fm.height()) // 2 + fm.ascent()
                p.drawText(name_x + NAME_WINDOW_PADDING, ty, desc_name)

            p.setPen(PYXEL_PALETTE[7])
            desc_lines = desc_text.split("\n")[:MSG_MAX_LINES]
            for i, line in enumerate(desc_lines):
                p.drawText(MSG_X + MSG_TEXT_PADDING,
                           MSG_Y + MSG_TEXT_PADDING + i * MSG_LINE_HEIGHT + fm.ascent(),
                           line)

            # 選択肢ウィンドウを上側に配置
            win_y = MSG_Y - win_h - 8

        # 選択肢ウィンドウ背景
        bg_color = QColor(PYXEL_PALETTE[1])
        if semi:
            bg_color.setAlpha(160)
        p.fillRect(win_x, win_y, win_w, win_h, bg_color)
        p.setPen(QPen(PYXEL_PALETTE[7], 1))
        p.drawRect(win_x, win_y, win_w - 1, win_h - 1)

        # 選択肢描画
        p.setPen(PYXEL_PALETTE[7])
        tx = win_x + SEL_TEXT_PADDING
        for i, item in enumerate(items):
            iy = win_y + SEL_TEXT_PADDING + i * SEL_LINE_HEIGHT + fm.ascent()
            if i == 0:
                # 最初の項目にカーソル表示
                p.drawText(tx, iy, SEL_CURSOR_CHAR)
            p.drawText(tx + cursor_w, iy, item)

    # --- テロップ描画 ---

    def _draw_telop(self, p):
        """テロップをゲーム風に描画する。"""
        if not self._data:
            return

        lines = self._data.get("lines", [])
        if not lines:
            return

        p.setFont(self._game_font)
        fm = p.fontMetrics()

        # スクロール速度表示（左上に配置）
        speed = self._data.get("scroll_speed", 1.0)
        p.setPen(PYXEL_PALETTE[10])
        speed_text = f"scroll_speed: {speed}"
        p.drawText(4, fm.ascent() + 2, speed_text)

        # テロップ領域（上部にメタ情報の余白を確保）
        info_margin_top = fm.height() + 8
        info_margin_bottom = 4
        usable_h = GAME_HEIGHT - info_margin_top - info_margin_bottom
        total_h = len(lines) * TELOP_LINE_HEIGHT

        # 画面に収まらない場合は行間を縮小（フォントサイズも調整）
        if total_h > usable_h:
            line_h = usable_h // len(lines)
            # 行間がフォント高さより小さくなる場合はフォントを縮小
            if line_h < fm.height():
                scaled_font = QFont(self._game_font)
                scaled_font.setPointSize(max(6, int(self._game_font.pointSize() * line_h / fm.height())))
                p.setFont(scaled_font)
                fm = p.fontMetrics()
            start_y = info_margin_top
        else:
            line_h = TELOP_LINE_HEIGHT
            start_y = info_margin_top + (usable_h - total_h) // 2

        p.setPen(PYXEL_PALETTE[7])
        for i, line in enumerate(lines):
            if not line:
                continue
            text_w = fm.horizontalAdvance(line)
            text_x = (GAME_WIDTH - text_w) // 2
            text_y = start_y + i * line_h + fm.ascent()
            p.drawText(text_x, text_y, line)


class EditCommand(QUndoCommand):
    """テキスト編集のUndoコマンド。

    エントリ全体のスナップショットを保存し、Undo/Redo で差し替える。
    """

    def __init__(self, file_data, filepath, category, entry_id,
                 old_value, new_value, description="Edit"):
        super().__init__(description)
        self._file_data = file_data
        self._filepath = filepath
        self._category = category
        self._entry_id = entry_id
        self._old_value = old_value
        self._new_value = new_value

    def redo(self):
        self._apply(self._new_value)

    def undo(self):
        self._apply(self._old_value)

    def _apply(self, value):
        """データを in-place で差し替える（参照を維持）。"""
        target = self._file_data[self._filepath][self._category][self._entry_id]
        source = copy.deepcopy(value)
        if isinstance(target, list):
            target.clear()
            target.extend(source)
        elif isinstance(target, dict):
            target.clear()
            target.update(source)
        else:
            # フォールバック: 参照差し替え（通常は到達しない）
            self._file_data[self._filepath][self._category][self._entry_id] = source


class FileTreePanel(QTreeWidget):
    """ファイル→カテゴリ→ID の3階層ツリー。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Text Files")
        self.setIndentation(16)

    def load_files(self, file_data_map):
        """{ filepath: data } からツリーを構築する。"""
        self.clear()
        for filepath, data in sorted(file_data_map.items()):
            filename = os.path.basename(filepath)
            file_item = QTreeWidgetItem(self, [filename])
            file_item.setData(0, Qt.UserRole, {"type": "file", "path": filepath})
            file_item.setExpanded(True)

            for cat in CATEGORIES:
                if cat not in data or not data[cat]:
                    continue
                cat_item = QTreeWidgetItem(file_item, [CATEGORY_LABELS[cat]])
                cat_item.setData(0, Qt.UserRole, {
                    "type": "category", "category": cat, "path": filepath,
                })
                cat_item.setExpanded(True)

                for entry_id in data[cat]:
                    id_item = QTreeWidgetItem(cat_item, [entry_id])
                    id_item.setData(0, Qt.UserRole, {
                        "type": "entry", "category": cat,
                        "entry_id": entry_id, "path": filepath,
                    })


class MessageEditor(QWidget):
    """Messages 編集フォーム。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None  # list of message entries
        self._page = 0
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ページナビ
        nav = QHBoxLayout()
        self._btn_prev = QPushButton("<")
        self._btn_prev.setFixedWidth(30)
        self._btn_prev.clicked.connect(self._prev_page)
        self._btn_next = QPushButton(">")
        self._btn_next.setFixedWidth(30)
        self._btn_next.clicked.connect(self._next_page)
        self._page_label = QLabel("Page 0/0")
        nav.addWidget(self._btn_prev)
        nav.addWidget(self._page_label)
        nav.addWidget(self._btn_next)
        nav.addStretch()

        # ページ追加/削除
        self._btn_add = QPushButton("+")
        self._btn_add.setFixedWidth(30)
        self._btn_add.setToolTip("ページ追加")
        self._btn_add.clicked.connect(self._add_page)
        self._btn_del = QPushButton("-")
        self._btn_del.setFixedWidth(30)
        self._btn_del.setToolTip("ページ削除")
        self._btn_del.clicked.connect(self._del_page)
        nav.addWidget(self._btn_add)
        nav.addWidget(self._btn_del)
        layout.addLayout(nav)

        # 名前
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("(名前なし)")
        self._name_edit.textChanged.connect(self._on_changed)
        name_row.addWidget(self._name_edit)
        layout.addLayout(name_row)

        # テキスト
        layout.addWidget(QLabel("Text:"))
        self._text_edit = QTextEdit()
        self._text_edit.setFont(QFont("Yu Gothic UI", 11))
        self._text_edit.textChanged.connect(self._on_changed)
        layout.addWidget(self._text_edit)

        # auto チェック
        self._auto_check = QCheckBox("自動送り (auto)")
        self._auto_check.stateChanged.connect(self._on_changed)
        layout.addWidget(self._auto_check)

    def set_data(self, messages):
        """メッセージリストをセットする。"""
        self._data = messages
        self._page = 0
        self._show_page()

    def _show_page(self):
        if not self._data:
            return
        self._updating = True
        page = self._data[self._page]
        if isinstance(page, str):
            self._name_edit.setText("")
            self._text_edit.setPlainText(page)
            self._auto_check.setChecked(False)
        else:
            self._name_edit.setText(page.get("name", ""))
            self._text_edit.setPlainText(page.get("text", ""))
            self._auto_check.setChecked(page.get("auto", False))

        self._page_label.setText(f"Page {self._page + 1}/{len(self._data)}")
        self._btn_prev.setEnabled(self._page > 0)
        self._btn_next.setEnabled(self._page < len(self._data) - 1)
        self._updating = False

    def _on_changed(self):
        if self._updating or not self._data:
            return
        name = self._name_edit.text().strip()
        text = self._text_edit.toPlainText()
        auto = self._auto_check.isChecked()

        if not name and not auto:
            self._data[self._page] = text
        else:
            entry = {"text": text}
            if name:
                entry["name"] = name
            if auto:
                entry["auto"] = True
            self._data[self._page] = entry

        # 親ウィンドウに変更通知
        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._show_page()
            self._notify_page_change()

    def _next_page(self):
        if self._data and self._page < len(self._data) - 1:
            self._page += 1
            self._show_page()
            self._notify_page_change()

    def _notify_page_change(self):
        """ページ切り替え時にプレビューを更新する。"""
        window = self.window()
        if hasattr(window, "_update_preview"):
            window._update_preview()

    def _add_page(self):
        if self._data is not None:
            self._data.append("新しいメッセージ")
            self._page = len(self._data) - 1
            self._show_page()
            window = self.window()
            if hasattr(window, "mark_dirty"):
                window.mark_dirty()

    def _del_page(self):
        if self._data and len(self._data) > 1:
            del self._data[self._page]
            if self._page >= len(self._data):
                self._page = len(self._data) - 1
            self._show_page()
            window = self.window()
            if hasattr(window, "mark_dirty"):
                window.mark_dirty()


class SelectionEditor(QWidget):
    """Selections 編集フォーム。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # アイテムリスト
        layout.addWidget(QLabel("Items:"))
        self._items_edit = QTextEdit()
        self._items_edit.setFont(QFont("Yu Gothic UI", 11))
        self._items_edit.setPlaceholderText("1行に1つの選択肢")
        self._items_edit.textChanged.connect(self._on_changed)
        layout.addWidget(self._items_edit)

        # cancel_index
        ci_row = QHBoxLayout()
        ci_row.addWidget(QLabel("Cancel Index:"))
        self._cancel_spin = QSpinBox()
        self._cancel_spin.setMinimum(-1)
        self._cancel_spin.valueChanged.connect(self._on_changed)
        ci_row.addWidget(self._cancel_spin)
        ci_row.addStretch()
        layout.addLayout(ci_row)

        # semi_transparent
        self._semi_check = QCheckBox("半透明 (semi_transparent)")
        self._semi_check.stateChanged.connect(self._on_changed)
        layout.addWidget(self._semi_check)

        # desc
        layout.addWidget(QLabel("Desc (説明メッセージ):"))
        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Name:"))
        self._desc_name = QLineEdit()
        self._desc_name.textChanged.connect(self._on_changed)
        desc_row.addWidget(self._desc_name)
        layout.addLayout(desc_row)
        self._desc_text = QTextEdit()
        self._desc_text.setFont(QFont("Yu Gothic UI", 11))
        self._desc_text.setMaximumHeight(80)
        self._desc_text.setPlaceholderText("(説明なし)")
        self._desc_text.textChanged.connect(self._on_changed)
        layout.addWidget(self._desc_text)

    def set_data(self, sel_data):
        self._data = sel_data
        self._updating = True

        items = sel_data.get("items", [])
        self._items_edit.setPlainText("\n".join(items))
        self._cancel_spin.setMaximum(max(len(items) - 1, 0))
        self._cancel_spin.setValue(sel_data.get("cancel_index", -1))
        self._semi_check.setChecked(sel_data.get("semi_transparent", False))

        desc = sel_data.get("desc")
        if desc:
            self._desc_name.setText(desc.get("name", ""))
            self._desc_text.setPlainText(desc.get("text", ""))
        else:
            self._desc_name.setText("")
            self._desc_text.setPlainText("")

        self._updating = False

    def _on_changed(self):
        if self._updating or not self._data:
            return
        items = [line for line in self._items_edit.toPlainText().split("\n") if line]
        self._data["items"] = items
        self._cancel_spin.setMaximum(max(len(items) - 1, 0))
        self._data["cancel_index"] = self._cancel_spin.value()

        if self._semi_check.isChecked():
            self._data["semi_transparent"] = True
        else:
            self._data.pop("semi_transparent", None)

        desc_name = self._desc_name.text().strip()
        desc_text = self._desc_text.toPlainText().strip()
        if desc_name or desc_text:
            self._data["desc"] = {}
            if desc_name:
                self._data["desc"]["name"] = desc_name
            if desc_text:
                self._data["desc"]["text"] = desc_text
        else:
            self._data.pop("desc", None)

        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()


class TelopEditor(QWidget):
    """Telops 編集フォーム。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # lines
        layout.addWidget(QLabel("Lines (1行に1テロップ行、空行=空白行):"))
        self._lines_edit = QTextEdit()
        self._lines_edit.setFont(QFont("Yu Gothic UI", 11))
        self._lines_edit.textChanged.connect(self._on_changed)
        layout.addWidget(self._lines_edit)

        # scroll_speed
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Scroll Speed:"))
        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 10.0)
        self._speed_spin.setSingleStep(0.1)
        self._speed_spin.setDecimals(1)
        self._speed_spin.valueChanged.connect(self._on_changed)
        speed_row.addWidget(self._speed_spin)
        speed_row.addStretch()
        layout.addLayout(speed_row)

    def set_data(self, telop_data):
        self._data = telop_data
        self._updating = True

        lines = telop_data.get("lines", [])
        self._lines_edit.setPlainText("\n".join(lines))
        self._speed_spin.setValue(telop_data.get("scroll_speed", 1.0))

        self._updating = False

    def _on_changed(self):
        if self._updating or not self._data:
            return
        # テロップは空行も意味があるので strip しない
        raw = self._lines_edit.toPlainText()
        self._data["lines"] = raw.split("\n")
        self._data["scroll_speed"] = self._speed_spin.value()

        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()


class EditorWindow(QMainWindow):
    """メインウィンドウ。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Editor")
        self.resize(1300, 700)

        self._file_data = {}  # { filepath: data }
        self._dirty = False
        self._current_entry = None  # (filepath, category, entry_id)
        self._undo_stack = QUndoStack(self)
        self._snapshot = None  # Undo 用の変更前スナップショット
        self._pushing_undo = False  # push 中の再帰防止フラグ

        self._setup_ui()
        self._setup_menu()
        self._load_all_files()

        self._closing = False
        self._undo_stack.cleanChanged.connect(self._on_undo_clean_changed)
        self._undo_stack.indexChanged.connect(lambda _: self._on_undo_or_redo())

    def _setup_ui(self):
        # メインコンテナ（検索バー + スプリッター）
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 検索バー（初期非表示）
        self._search_bar = QWidget()
        self._search_bar.setMaximumHeight(30)
        search_layout = QHBoxLayout(self._search_bar)
        search_layout.setContentsMargins(4, 2, 4, 2)
        search_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("ID or text...")
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.returnPressed.connect(self._search_next)
        search_layout.addWidget(self._search_input)
        self._search_count_label = QLabel("")
        search_layout.addWidget(self._search_count_label)
        btn_prev = QPushButton("<")
        btn_prev.setFixedWidth(30)
        btn_prev.setToolTip("Previous (Shift+Enter)")
        btn_prev.clicked.connect(self._search_prev)
        search_layout.addWidget(btn_prev)
        btn_next = QPushButton(">")
        btn_next.setFixedWidth(30)
        btn_next.setToolTip("Next (Enter)")
        btn_next.clicked.connect(self._search_next)
        search_layout.addWidget(btn_next)
        btn_close = QPushButton("x")
        btn_close.setFixedWidth(24)
        btn_close.clicked.connect(self._close_search)
        search_layout.addWidget(btn_close)
        self._search_bar.hide()
        main_layout.addWidget(self._search_bar)

        self._search_results = []  # [(filepath, category, entry_id), ...]
        self._search_index = -1

        # メインスプリッター (3ペイン)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)

        # 左: ファイルツリー
        self._tree = FileTreePanel()
        self._tree.currentItemChanged.connect(self._on_tree_selected)
        self._tree.setMinimumWidth(180)
        splitter.addWidget(self._tree)

        # 中央: 編集エリア（スタックウィジェット）
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)

        self._id_label = QLabel("Select an item from the tree")
        self._id_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        center_layout.addWidget(self._id_label)

        self._stack = QStackedWidget()

        # 空ページ
        self._empty_page = QLabel("Select a text entry to edit")
        self._empty_page.setAlignment(Qt.AlignCenter)
        self._stack.addWidget(self._empty_page)

        # Messages 編集
        self._msg_editor = MessageEditor()
        self._stack.addWidget(self._msg_editor)

        # Selections 編集
        self._sel_editor = SelectionEditor()
        self._stack.addWidget(self._sel_editor)

        # Telops 編集
        self._telop_editor = TelopEditor()
        self._stack.addWidget(self._telop_editor)

        center_layout.addWidget(self._stack)
        splitter.addWidget(center)

        # 右: プレビューパネル
        self._preview = PreviewPanel()
        splitter.addWidget(self._preview)

        splitter.setSizes([200, 500, 400])

        # ステータスバー
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File メニュー
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._save_all)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Tools メニュー
        tools_menu = menubar.addMenu("Tools")

        compile_action = QAction("Compile (F5)", self)
        compile_action.setShortcut(QKeySequence("F5"))
        compile_action.triggered.connect(self._compile)
        tools_menu.addAction(compile_action)

        reload_action = QAction("Reload (F9)", self)
        reload_action.setShortcut(QKeySequence("F9"))
        reload_action.triggered.connect(self._reload_files)
        tools_menu.addAction(reload_action)

        tools_menu.addSeparator()

        unused_action = QAction("Find Unused IDs...", self)
        unused_action.triggered.connect(self._find_unused_ids)
        tools_menu.addAction(unused_action)

        # Edit メニュー
        edit_menu = menubar.addMenu("Edit")

        self._undo_action = self._undo_stack.createUndoAction(self, "Undo")
        self._undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        edit_menu.addAction(self._undo_action)

        self._redo_action = self._undo_stack.createRedoAction(self, "Redo")
        self._redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

        add_id_action = QAction("Add ID...", self)
        add_id_action.triggered.connect(self._add_id)
        edit_menu.addAction(add_id_action)

        del_id_action = QAction("Delete ID", self)
        del_id_action.setShortcut(QKeySequence("Delete"))
        del_id_action.triggered.connect(self._delete_id)
        edit_menu.addAction(del_id_action)

        edit_menu.addSeparator()

        search_action = QAction("Search (Ctrl+F)", self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self._toggle_search)
        edit_menu.addAction(search_action)

    def _load_all_files(self):
        """data/text/ 内の全JSONを読み込む。"""
        self._file_data.clear()
        if not os.path.isdir(TEXT_DIR):
            self._statusbar.showMessage(f"Directory not found: {TEXT_DIR}", 5000)
            return

        for fname in sorted(os.listdir(TEXT_DIR)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(TEXT_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._file_data[fpath] = data
            except Exception as e:
                self._statusbar.showMessage(f"Load error: {fname}: {e}", 5000)

        self._tree.load_files(self._file_data)
        self._dirty = False
        self._update_title()
        self._statusbar.showMessage(
            f"Loaded {len(self._file_data)} file(s)", 3000)

    def _reload_files(self):
        self._load_all_files()
        self._undo_stack.clear()
        self._snapshot = None
        self._current_entry = None
        self._stack.setCurrentWidget(self._empty_page)
        self._id_label.setText("Select an item from the tree")

    def _on_tree_selected(self, current, previous):
        if not current:
            return
        info = current.data(0, Qt.UserRole)
        if not info or info["type"] != "entry":
            self._stack.setCurrentWidget(self._empty_page)
            self._id_label.setText("Select a text entry to edit")
            self._current_entry = None
            self._preview.clear_preview()
            return

        cat = info["category"]
        entry_id = info["entry_id"]
        filepath = info["path"]
        data = self._file_data[filepath]
        entry_data = data[cat][entry_id]

        # 前のエントリの変更を確定
        self._flush_undo()

        self._current_entry = (filepath, cat, entry_id)
        self._snapshot = copy.deepcopy(entry_data)
        self._id_label.setText(f"{os.path.basename(filepath)} > {CATEGORY_LABELS[cat]} > {entry_id}")

        if cat == "messages":
            self._msg_editor.set_data(entry_data)
            self._stack.setCurrentWidget(self._msg_editor)
        elif cat == "selections":
            self._sel_editor.set_data(entry_data)
            self._stack.setCurrentWidget(self._sel_editor)
        elif cat == "telops":
            self._telop_editor.set_data(entry_data)
            self._stack.setCurrentWidget(self._telop_editor)

        self._update_preview()

    def _flush_undo(self):
        """現在のエントリへの変更が未コミットなら UndoStack に push する。"""
        if not self._current_entry or self._snapshot is None:
            return
        filepath, cat, entry_id = self._current_entry
        if filepath not in self._file_data:
            return
        current_data = self._file_data[filepath][cat].get(entry_id)
        if current_data is None:
            return
        current_copy = copy.deepcopy(current_data)
        if current_copy != self._snapshot:
            cmd = EditCommand(
                self._file_data, filepath, cat, entry_id,
                self._snapshot, current_copy,
                f"Edit {cat}.{entry_id}",
            )
            self._pushing_undo = True
            self._undo_stack.push(cmd)
            self._pushing_undo = False
            self._snapshot = copy.deepcopy(current_copy)

    def mark_dirty(self):
        self._dirty = True
        self._update_title()
        self._update_preview()
        # 変更をデバウンスして UndoStack に push
        if not hasattr(self, "_undo_timer"):
            self._undo_timer = QTimer(self)
            self._undo_timer.setSingleShot(True)
            self._undo_timer.setInterval(500)
            self._undo_timer.timeout.connect(self._flush_undo)
        self._undo_timer.start()

    def _update_title(self):
        marker = " *" if self._dirty else ""
        self.setWindowTitle(f"Text Editor{marker}")

    def _on_undo_clean_changed(self, clean):
        """UndoStack の clean 状態変化時。"""
        if not clean:
            self._dirty = True
            self._update_title()

    def _on_undo_or_redo(self):
        """Undo/Redo 実行後にエディタUIを再読み込みする。"""
        if self._pushing_undo or self._closing:
            return
        if not self._current_entry:
            return
        filepath, cat, entry_id = self._current_entry
        if filepath not in self._file_data:
            return
        data = self._file_data[filepath]
        if entry_id not in data.get(cat, {}):
            return
        entry_data = data[cat][entry_id]
        self._snapshot = copy.deepcopy(entry_data)

        # エディタの表示を更新（_updating フラグで再帰防止）
        if cat == "messages":
            self._msg_editor.set_data(entry_data)
        elif cat == "selections":
            self._sel_editor.set_data(entry_data)
        elif cat == "telops":
            self._telop_editor.set_data(entry_data)

        self._dirty = True
        self._update_title()
        self._update_preview()

    def _update_preview(self):
        """現在の編集内容でプレビューを更新する。"""
        if not self._current_entry:
            self._preview.clear_preview()
            return

        filepath, cat, entry_id = self._current_entry
        data = self._file_data[filepath]
        entry_data = data[cat][entry_id]

        page = 0
        if cat == "messages":
            page = self._msg_editor._page

        self._preview.set_preview(cat, entry_data, page)

        # バリデーション警告をステータスバーに表示
        warnings = self._preview.get_warnings()
        if warnings:
            self._statusbar.showMessage(
                f"Warning: {warnings[0]}" +
                (f" (+{len(warnings)-1} more)" if len(warnings) > 1 else ""))
        else:
            # 警告がなく、他のメッセージもなければクリア
            if "Warning:" in (self._statusbar.currentMessage() or ""):
                self._statusbar.clearMessage()

    def _save_all(self):
        """変更を全ファイルに保存する。"""
        # 未確定の変更を flush
        self._flush_undo()

        for filepath, data in self._file_data.items():
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self._statusbar.showMessage(f"Save error: {e}", 5000)
                return

        self._dirty = False
        self._update_title()
        self._undo_stack.setClean()
        self._statusbar.showMessage(
            f"Saved {len(self._file_data)} file(s)", 3000)

    def _compile(self):
        """コンパイラを実行する。"""
        # 未保存があれば先に保存
        if self._dirty:
            self._save_all()

        self._statusbar.showMessage("Compiling...")
        QApplication.processEvents()

        try:
            result = subprocess.run(
                [sys.executable, COMPILER_PATH],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                self._statusbar.showMessage("Compile OK!", 5000)
            else:
                err = result.stderr.strip().split("\n")[-1] if result.stderr else "Unknown error"
                self._statusbar.showMessage(f"Compile error: {err}", 5000)
        except Exception as e:
            self._statusbar.showMessage(f"Compile error: {e}", 5000)

    def _find_unused_ids(self):
        """src/ ディレクトリ内で参照されていないIDを検出する。"""
        src_dir = os.path.join(_PROJECT_ROOT, "src")
        if not os.path.isdir(src_dir):
            QMessageBox.information(self, "Unused IDs",
                                    f"Source directory not found: {src_dir}")
            return

        # src/ 内の全Pythonファイルの内容を読み込む
        src_contents = []
        for root, dirs, files in os.walk(src_dir):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            src_contents.append(f.read())
                    except Exception:
                        pass
        all_source = "\n".join(src_contents)

        # 全IDを収集し、ソースコード内に出現するか検査
        unused = []
        for filepath, data in self._file_data.items():
            filename = os.path.basename(filepath)
            for cat in CATEGORIES:
                if cat not in data:
                    continue
                for entry_id in data[cat]:
                    if entry_id not in all_source:
                        unused.append(f"{filename} > {CATEGORY_LABELS[cat]} > {entry_id}")

        if not unused:
            QMessageBox.information(self, "Unused IDs",
                                    "All IDs are referenced in src/.")
        else:
            msg = f"{len(unused)} unused ID(s) found:\n\n"
            msg += "\n".join(unused[:50])
            if len(unused) > 50:
                msg += f"\n... and {len(unused) - 50} more"
            QMessageBox.warning(self, "Unused IDs", msg)

        self._statusbar.showMessage(
            f"Unused ID check: {len(unused)} unused", 5000)

    def _add_id(self):
        """選択中のカテゴリに新しいIDを追加する。"""
        item = self._tree.currentItem()
        if not item:
            return
        info = item.data(0, Qt.UserRole)
        if not info:
            return

        # カテゴリまたはエントリから所属を特定
        if info["type"] == "category":
            cat = info["category"]
            filepath = info["path"]
        elif info["type"] == "entry":
            cat = info["category"]
            filepath = info["path"]
        else:
            self._statusbar.showMessage("Select a category or entry first", 3000)
            return

        new_id, ok = QInputDialog.getText(self, "Add ID", f"New {cat} ID:")
        if not ok or not new_id.strip():
            return
        new_id = new_id.strip()

        data = self._file_data[filepath]
        if new_id in data[cat]:
            QMessageBox.warning(self, "Error", f"ID '{new_id}' already exists")
            return

        # デフォルトデータ作成
        if cat == "messages":
            data[cat][new_id] = ["新しいメッセージ"]
        elif cat == "selections":
            data[cat][new_id] = {"items": ["選択肢1"], "cancel_index": 0}
        elif cat == "telops":
            data[cat][new_id] = {"lines": ["テロップテキスト"], "scroll_speed": 1.0}

        self.mark_dirty()
        self._tree.load_files(self._file_data)
        self._statusbar.showMessage(f"Added: {cat}.{new_id}", 3000)

    def _delete_id(self):
        """選択中のIDを削除する。"""
        if not self._current_entry:
            return
        filepath, cat, entry_id = self._current_entry

        reply = QMessageBox.question(
            self, "Delete",
            f"Delete {cat}.{entry_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        data = self._file_data[filepath]
        del data[cat][entry_id]
        self._current_entry = None
        self.mark_dirty()
        self._tree.load_files(self._file_data)
        self._stack.setCurrentWidget(self._empty_page)
        self._statusbar.showMessage(f"Deleted: {cat}.{entry_id}", 3000)

    # --- 検索機能 ---

    def _toggle_search(self):
        """検索バーの表示/非表示を切り替える。"""
        if self._search_bar.isVisible():
            self._close_search()
        else:
            self._search_bar.show()
            self._search_input.setFocus()
            self._search_input.selectAll()

    def _close_search(self):
        """検索バーを閉じる。"""
        self._search_bar.hide()
        self._search_results.clear()
        self._search_index = -1
        self._search_count_label.setText("")

    def _on_search_changed(self, text):
        """検索テキスト変更時のインクリメンタル検索。"""
        self._search_results.clear()
        self._search_index = -1

        query = text.strip().lower()
        if not query:
            self._search_count_label.setText("")
            return

        # 全エントリを検索
        for filepath, data in self._file_data.items():
            for cat in CATEGORIES:
                if cat not in data:
                    continue
                for entry_id, entry_data in data[cat].items():
                    if self._entry_matches(query, entry_id, cat, entry_data):
                        self._search_results.append((filepath, cat, entry_id))

        count = len(self._search_results)
        self._search_count_label.setText(f"{count} hit(s)")

        if count > 0:
            self._search_index = 0
            self._navigate_to_search_result()

    def _entry_matches(self, query, entry_id, cat, entry_data):
        """エントリが検索クエリにマッチするか判定する。"""
        # ID名で検索
        if query in entry_id.lower():
            return True

        # テキスト内容で検索
        if cat == "messages":
            for msg in entry_data:
                if isinstance(msg, str):
                    if query in msg.lower():
                        return True
                else:
                    if query in msg.get("text", "").lower():
                        return True
                    if query in msg.get("name", "").lower():
                        return True
        elif cat == "selections":
            for item in entry_data.get("items", []):
                if query in item.lower():
                    return True
            desc = entry_data.get("desc")
            if desc:
                if query in desc.get("text", "").lower():
                    return True
                if query in desc.get("name", "").lower():
                    return True
        elif cat == "telops":
            for line in entry_data.get("lines", []):
                if query in line.lower():
                    return True

        return False

    def _search_next(self):
        """次の検索結果に移動する。"""
        if not self._search_results:
            return
        self._search_index = (self._search_index + 1) % len(self._search_results)
        self._navigate_to_search_result()

    def _search_prev(self):
        """前の検索結果に移動する。"""
        if not self._search_results:
            return
        self._search_index = (self._search_index - 1) % len(self._search_results)
        self._navigate_to_search_result()

    def _navigate_to_search_result(self):
        """現在の検索結果にツリーのカーソルを移動する。"""
        if self._search_index < 0 or self._search_index >= len(self._search_results):
            return

        filepath, cat, entry_id = self._search_results[self._search_index]
        self._search_count_label.setText(
            f"{self._search_index + 1}/{len(self._search_results)}")

        # ツリーアイテムを探してセレクトする
        root = self._tree.topLevelItem(0)
        for fi in range(self._tree.topLevelItemCount()):
            file_item = self._tree.topLevelItem(fi)
            file_info = file_item.data(0, Qt.UserRole)
            if file_info and file_info.get("path") == filepath:
                for ci in range(file_item.childCount()):
                    cat_item = file_item.child(ci)
                    cat_info = cat_item.data(0, Qt.UserRole)
                    if cat_info and cat_info.get("category") == cat:
                        for ei in range(cat_item.childCount()):
                            entry_item = cat_item.child(ei)
                            entry_info = entry_item.data(0, Qt.UserRole)
                            if entry_info and entry_info.get("entry_id") == entry_id:
                                self._tree.setCurrentItem(entry_item)
                                return

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                self._save_all()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        self._closing = True
        self._undo_stack.clear()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = EditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
