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
MAP_DIR = os.path.join(_PROJECT_ROOT, "data", "maps")
CHAR_DIR = os.path.join(_PROJECT_ROOT, "data", "characters")
TILESET_DIR = os.path.join(_PROJECT_ROOT, "assets", "tilesets")
SPRITE_DIR = os.path.join(_PROJECT_ROOT, "assets", "images", "sprite")
COMPILER_PATH = os.path.join(_TOOLS_DIR, "compiler.py")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QStackedWidget, QPushButton,
    QStatusBar, QMenuBar, QListWidget, QMessageBox, QInputDialog,
    QAbstractItemView, QComboBox, QFormLayout, QScrollArea, QGroupBox,
)
from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import (
    QAction, QKeySequence, QFont, QFontDatabase, QPainter, QColor, QPen,
    QBrush, QPixmap, QUndoStack, QUndoCommand, QActionGroup, QImage,
)

# カテゴリ表示名
CATEGORY_LABELS = {
    "messages": "Messages",
    "selections": "Selections",
    "telops": "Telops",
    "events": "Events",
}
CATEGORIES = ["messages", "selections", "telops", "events"]

EVENT_CMD_FIELDS = {
    "wait": [("duration", "Duration", "int", 60)],
    "message": [("id", "Message ID", "str", "")],
    "selection": [("id", "Selection ID", "str", "")],
    "telop": [("id", "Telop ID", "str", "")],
    "show_picture": [
        ("no", "Picture No", "int", 1),
        ("file", "File", "str", ""),
        ("x", "X", "int", 0),
        ("y", "Y", "int", 0),
        ("opacity", "Opacity", "int", 100),
        ("colkey", "Color Key", "int_or_none", None),
    ],
    "move_picture": [
        ("no", "Picture No", "int", 1),
        ("x", "X", "int_or_none", None),
        ("y", "Y", "int_or_none", None),
        ("opacity", "Opacity", "int_or_none", None),
        ("duration", "Duration", "int", 60),
    ],
    "erase_picture": [("no", "Picture No", "int", 1)],
    "fadein": [("duration", "Duration", "int", 60)],
    "fadeout": [("duration", "Duration", "int", 60)],
    "play_bgm": [("file", "File", "str", "")],
    "stop_bgm": [("fadeout", "Fadeout (ms)", "int", 0)],
    "play_se": [
        ("sound_no", "Sound No", "int", 0),
        ("ch", "Channel", "int", 3),
    ],
    "change_scene": [("scene", "Scene", "str", "")],
}

STAT_KEYS = ["hp", "mp", "str", "vit", "int", "mnd", "luk"]
STAT_LABELS = {
    "hp": "HP",
    "mp": "MP",
    "str": "STR",
    "vit": "VIT",
    "int": "INT",
    "mnd": "MND",
    "luk": "LUK",
}
PHYSICAL_SKILL_KEYS = ["dagger", "sword", "katana", "axe", "spear", "staff", "claw", "bow"]
PHYSICAL_SKILL_LABELS = {
    "dagger": "短剣",
    "sword": "剣",
    "katana": "刀",
    "axe": "斧",
    "spear": "槍",
    "staff": "棍",
    "claw": "爪",
    "bow": "弓",
}
MAGIC_SKILL_KEYS = ["healing", "elemental", "buff", "debuff"]
MAGIC_SKILL_LABELS = {
    "healing": "回復",
    "elemental": "元素",
    "buff": "強化",
    "debuff": "弱体",
}
GRAPHIC_CUT_SIZE = 32
DEFAULT_CHARACTER = {
    "name": "新規キャラクター",
    "initial_job": 0,
    "personality": 0,
    "graphics": {
        "face": {"image": "", "selection_id": 0},
        "walk": {"image": "", "selection_id": 0},
        "battle": {"image": "", "selection_id": 0},
    },
    "base_stats": {key: 0 for key in STAT_KEYS},
    "growth_rates": {
        "stats": {key: 0 for key in STAT_KEYS},
        "physical_skills": {key: 0 for key in PHYSICAL_SKILL_KEYS},
        "magic_skills": {key: 0 for key in MAGIC_SKILL_KEYS},
    },
}

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
            elif self._category == "events":
                self._draw_events(buf)
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

    def _draw_events(self, p):
        """イベントコマンド概要を簡易表示する。"""
        if not isinstance(self._data, list):
            return

        p.setFont(self._game_font)
        p.setPen(PYXEL_PALETTE[7])
        p.drawText(16, 24, "Event Commands")
        p.setPen(PYXEL_PALETTE[11])
        p.drawText(16, 46, f"{len(self._data)} command(s)")

        y = 76
        for index, cmd in enumerate(self._data[:8]):
            p.setPen(PYXEL_PALETTE[6])
            p.drawText(16, y, f"{index + 1:02d}. {cmd.get('cmd', '(unknown)')}")
            y += 22

        if len(self._data) > 8:
            p.setPen(PYXEL_PALETTE[13])
            p.drawText(16, y + 4, f"... and {len(self._data) - 8} more")


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


class MapEditCommand(QUndoCommand):
    """マップ全体編集のUndoコマンド。"""

    def __init__(self, map_file_data, filepath, old_value, new_value, description="Edit Map"):
        super().__init__(description)
        self._map_file_data = map_file_data
        self._filepath = filepath
        self._old_value = old_value
        self._new_value = new_value

    def redo(self):
        self._apply(self._new_value)

    def undo(self):
        self._apply(self._old_value)

    def _apply(self, value):
        target = self._map_file_data[self._filepath]
        source = copy.deepcopy(value)
        target.clear()
        target.update(source)


class RenameCommand(QUndoCommand):
    """IDリネームのUndoコマンド。"""

    def __init__(self, file_data, filepath, category, old_id, new_id,
                 description="Rename"):
        super().__init__(description)
        self._file_data = file_data
        self._filepath = filepath
        self._category = category
        self._old_id = old_id
        self._new_id = new_id

    def redo(self):
        self._rename(self._old_id, self._new_id)

    def undo(self):
        self._rename(self._new_id, self._old_id)

    def _rename(self, from_id, to_id):
        """辞書のキーをリネームする（順序を維持）。"""
        cat_dict = self._file_data[self._filepath][self._category]
        new_dict = {}
        for key, value in cat_dict.items():
            if key == from_id:
                new_dict[to_id] = value
            else:
                new_dict[key] = value
        cat_dict.clear()
        cat_dict.update(new_dict)


class FileTreePanel(QTreeWidget):
    """ファイル→カテゴリ→ID の3階層ツリー。"""

    rename_requested = Signal(QTreeWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Text Files")
        self.setIndentation(16)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """右クリックコンテキストメニューを表示する。"""
        item = self.itemAt(pos)
        if not item:
            return
        info = item.data(0, Qt.UserRole)
        if not info or info["type"] != "entry":
            return

        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        rename_action = menu.addAction("Rename ID...")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == rename_action:
            self.rename_requested.emit(item)
        menu.deleteLater()

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


class EventEditor(QWidget):
    """Events 編集フォーム。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._updating = False
        self._field_widgets = {}
        self._current_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        header.addWidget(QLabel("Commands:"))
        header.addStretch()
        self._btn_add = QPushButton("Add Command")
        self._btn_add.clicked.connect(self._add_command)
        header.addWidget(self._btn_add)
        self._btn_del = QPushButton("Delete Command")
        self._btn_del.clicked.connect(self._delete_command)
        header.addWidget(self._btn_del)
        layout.addLayout(header)

        body = QHBoxLayout()
        layout.addLayout(body, 1)

        self._cmd_list = QListWidget()
        self._cmd_list.setDragDropMode(QAbstractItemView.InternalMove)
        self._cmd_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._cmd_list.currentRowChanged.connect(self._on_cmd_selected)
        self._cmd_list.model().rowsMoved.connect(self._on_rows_moved)
        body.addWidget(self._cmd_list, 1)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Command Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(list(EVENT_CMD_FIELDS.keys()))
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        type_row.addWidget(self._type_combo, 1)
        detail_layout.addLayout(type_row)

        self._field_form = QFormLayout()
        detail_layout.addLayout(self._field_form)
        detail_layout.addStretch()
        body.addWidget(detail, 2)

    def set_data(self, event_list):
        self._data = event_list
        self._updating = True
        self._refresh_command_list()
        if self._data:
            next_row = min(max(self._current_index, 0), len(self._data) - 1)
            self._cmd_list.setCurrentRow(next_row)
        else:
            self._current_index = -1
            self._build_fields(None, None)
        self._updating = False

    def _refresh_command_list(self):
        self._cmd_list.clear()
        if not isinstance(self._data, list):
            return
        for index, cmd in enumerate(self._data):
            self._cmd_list.addItem(f"{index + 1:02d}: {cmd.get('cmd', '(unknown)')}")

    def _clear_fields(self):
        while self._field_form.rowCount():
            self._field_form.removeRow(0)
        self._field_widgets.clear()

    def _build_fields(self, cmd_type, cmd):
        self._clear_fields()
        if not cmd_type or cmd is None:
            return

        for key, label, field_type, default in EVENT_CMD_FIELDS.get(cmd_type, []):
            if field_type == "str":
                widget = QLineEdit()
                widget.setText(str(cmd.get(key, default)))
                widget.textChanged.connect(self._on_changed)
                self._field_form.addRow(label + ":", widget)
                self._field_widgets[key] = (field_type, widget)
            elif field_type == "int":
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
                widget.setValue(int(cmd.get(key, default)))
                widget.valueChanged.connect(self._on_changed)
                self._field_form.addRow(label + ":", widget)
                self._field_widgets[key] = (field_type, widget)
            elif field_type == "int_or_none":
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)

                enabled = QCheckBox("Enabled")
                spin = QSpinBox()
                spin.setRange(-999999, 999999)

                value = cmd.get(key, default)
                enabled.setChecked(value is not None)
                spin.setEnabled(value is not None)
                spin.setValue(0 if value is None else int(value))

                def toggle_optional(state, spinbox=spin):
                    spinbox.setEnabled(bool(state))
                    self._on_changed()

                enabled.stateChanged.connect(toggle_optional)
                spin.valueChanged.connect(self._on_changed)

                row_layout.addWidget(enabled)
                row_layout.addWidget(spin, 1)
                self._field_form.addRow(label + ":", row)
                self._field_widgets[key] = (field_type, enabled, spin)

    def _selected_command(self):
        if not isinstance(self._data, list):
            return None
        row = self._cmd_list.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row]

    def _on_cmd_selected(self, row):
        self._current_index = row
        cmd = self._selected_command()
        self._updating = True
        if cmd is None:
            self._build_fields(None, None)
        else:
            cmd_type = cmd.get("cmd", "wait")
            combo_index = self._type_combo.findText(cmd_type)
            if combo_index >= 0:
                self._type_combo.setCurrentIndex(combo_index)
            self._build_fields(cmd_type, cmd)
        self._updating = False

    def _on_type_changed(self, cmd_type):
        if self._updating:
            return
        cmd = self._selected_command()
        if cmd is None:
            return

        new_cmd = {"cmd": cmd_type}
        for key, _label, _field_type, default in EVENT_CMD_FIELDS.get(cmd_type, []):
            if default is not None:
                new_cmd[key] = copy.deepcopy(default)

        cmd.clear()
        cmd.update(new_cmd)
        self._refresh_command_list()
        self._cmd_list.setCurrentRow(self._current_index)
        self._build_fields(cmd_type, cmd)
        self._mark_dirty()

    def _on_changed(self):
        if self._updating:
            return
        cmd = self._selected_command()
        if cmd is None:
            return

        cmd_type = cmd.get("cmd")
        updated = {"cmd": cmd_type}
        for key, _label, field_type, _default in EVENT_CMD_FIELDS.get(cmd_type, []):
            widget_info = self._field_widgets.get(key)
            if field_type == "str":
                updated[key] = widget_info[1].text()
            elif field_type == "int":
                updated[key] = widget_info[1].value()
            elif field_type == "int_or_none":
                enabled, spin = widget_info[1], widget_info[2]
                updated[key] = spin.value() if enabled.isChecked() else None

        cmd.clear()
        cmd.update(updated)
        self._refresh_command_list()
        self._cmd_list.setCurrentRow(self._current_index)
        self._mark_dirty()

    def _on_rows_moved(self, _src_parent, start, end, _dst_parent, row):
        if self._updating or not isinstance(self._data, list) or start != end:
            return
        moved = self._data.pop(start)
        if row > start:
            row -= 1
        self._data.insert(row, moved)
        self._refresh_command_list()
        self._cmd_list.setCurrentRow(row)
        self._mark_dirty()

    def _add_command(self):
        if not isinstance(self._data, list):
            return
        self._data.append({"cmd": "wait", "duration": 60})
        self._refresh_command_list()
        self._cmd_list.setCurrentRow(len(self._data) - 1)
        self._mark_dirty()

    def _delete_command(self):
        if not isinstance(self._data, list):
            return
        row = self._cmd_list.currentRow()
        if row < 0 or row >= len(self._data):
            return
        del self._data[row]
        self._refresh_command_list()
        if self._data:
            self._cmd_list.setCurrentRow(min(row, len(self._data) - 1))
        else:
            self._current_index = -1
            self._build_fields(None, None)
        self._mark_dirty()

    def _mark_dirty(self):
        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()


def _create_default_map(name="New Map", width=20, height=15, tile_size=16):
    """空のマップデータを生成する。"""
    return {
        "version": 1,
        "name": name,
        "width": width,
        "height": height,
        "tile_size": tile_size,
        "tileset": "",
        "layers": [{
            "name": "ground",
            "visible": True,
            "tiles": [[0 for _ in range(width)] for _ in range(height)],
        }],
    }


class TilesetPalette(QWidget):
    """タイルセットを一覧表示する簡易パレット。"""

    tile_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self._tile_size = 16
        self._tileset_name = ""
        self._image = QImage()
        self._selected_tile = 1
        self._scale = 2

    def load_tileset(self, tileset_name, tile_size):
        self._tileset_name = tileset_name or ""
        self._tile_size = max(1, int(tile_size or 16))
        image_path = os.path.join(TILESET_DIR, self._tileset_name) if self._tileset_name else ""
        self._image = QImage(image_path) if image_path and os.path.isfile(image_path) else QImage()
        self.update()

    def set_selected_tile(self, tile_id):
        self._selected_tile = max(1, int(tile_id))
        self.update()

    def selected_tile(self):
        return self._selected_tile

    def mousePressEvent(self, event):
        if self._image.isNull() or event.button() != Qt.LeftButton:
            return
        cols = max(1, self._image.width() // self._tile_size)
        col = int(event.position().x()) // (self._tile_size * self._scale)
        row = int(event.position().y()) // (self._tile_size * self._scale)
        tile_id = row * cols + col + 1
        if col < 0 or row < 0 or tile_id < 1:
            return
        max_tiles = cols * max(1, self._image.height() // self._tile_size)
        if tile_id > max_tiles:
            return
        self._selected_tile = tile_id
        self.tile_selected.emit(tile_id)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        if self._image.isNull():
            painter.setPen(QColor(220, 220, 220))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Tileset")
            return

        scaled = QPixmap.fromImage(self._image).scaled(
            self._image.width() * self._scale,
            self._image.height() * self._scale,
            Qt.IgnoreAspectRatio,
            Qt.FastTransformation,
        )
        painter.drawPixmap(0, 0, scaled)

        cols = max(1, self._image.width() // self._tile_size)
        rows = max(1, self._image.height() // self._tile_size)
        cell = self._tile_size * self._scale
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        for x in range(cols + 1):
            painter.drawLine(x * cell, 0, x * cell, rows * cell)
        for y in range(rows + 1):
            painter.drawLine(0, y * cell, cols * cell, y * cell)

        tile_index = self._selected_tile - 1
        sx = (tile_index % cols) * cell
        sy = (tile_index // cols) * cell
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawRect(sx, sy, cell, cell)

    def sizeHint(self):
        if self._image.isNull():
            return super().sizeHint()
        return self._image.size() * self._scale


class MapCanvas(QWidget):
    """単純なマップ描画/ペン編集キャンバス。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.StrongFocus)
        self._map_data = None
        self._tileset_name = ""
        self._tileset_image = QImage()
        self._selected_tile = 1
        self._zoom = 2
        self._painting = False
        self._tool = "pen"
        self._erase_mode = False
        self._active_layer_idx = 0
        self._drag_start = None
        self._drag_current = None
        self._selection_start = None
        self._selection_end = None
        self._clipboard_tiles = None
        self._paste_origin = None

    def set_map_data(self, map_data):
        self._map_data = map_data
        self._load_tileset()
        self.update()

    def set_selected_tile(self, tile_id):
        self._selected_tile = max(1, int(tile_id))

    def set_active_layer(self, index):
        self._active_layer_idx = max(0, int(index))
        self.update()

    def set_tool(self, tool):
        self._tool = tool
        self._drag_start = None
        self._drag_current = None
        if tool != "select":
            self._selection_start = None
            self._selection_end = None
            self._paste_origin = None
        self.update()

    def set_erase_mode(self, enabled):
        self._erase_mode = bool(enabled)
        self.update()

    def _load_tileset(self):
        self._tileset_name = self._map_data.get("tileset", "") if self._map_data else ""
        path = os.path.join(TILESET_DIR, self._tileset_name) if self._tileset_name else ""
        self._tileset_image = QImage(path) if path and os.path.isfile(path) else QImage()

    def _tile_rect(self, col, row):
        tile_size = self._map_data.get("tile_size", 16) * self._zoom
        return QRectF(col * tile_size, row * tile_size, tile_size, tile_size)

    def _tile_at_pos(self, pos):
        if not self._map_data:
            return None
        tile_size = self._map_data.get("tile_size", 16) * self._zoom
        col = int(pos.x()) // tile_size
        row = int(pos.y()) // tile_size
        if 0 <= row < self._map_data.get("height", 0) and 0 <= col < self._map_data.get("width", 0):
            return row, col
        return None

    def _paint_tile(self, row, col, tile_value):
        if not self._map_data:
            return
        layers = self._map_data.get("layers", [])
        if not layers:
            return
        layer_idx = min(self._active_layer_idx, len(layers) - 1)
        tiles = layers[layer_idx]["tiles"]
        if tiles[row][col] == tile_value:
            return
        tiles[row][col] = tile_value
        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()
        self.update()

    def _apply_rect(self, start, end, tile_value):
        if not self._map_data or start is None or end is None:
            return
        sr, sc = start
        er, ec = end
        top, bottom = sorted((sr, er))
        left, right = sorted((sc, ec))
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                self._paint_tile(row, col, tile_value)

    def _apply_bucket(self, start, tile_value):
        if not self._map_data or start is None:
            return
        layers = self._map_data.get("layers", [])
        if not layers:
            return
        layer_idx = min(self._active_layer_idx, len(layers) - 1)
        tiles = layers[layer_idx]["tiles"]
        height = self._map_data.get("height", 0)
        width = self._map_data.get("width", 0)
        sr, sc = start
        target = tiles[sr][sc]
        if target == tile_value:
            return
        queue = [(sr, sc)]
        visited = set()
        changes = 0
        while queue and changes < 10000:
            row, col = queue.pop()
            if (row, col) in visited:
                continue
            visited.add((row, col))
            if not (0 <= row < height and 0 <= col < width):
                continue
            if tiles[row][col] != target:
                continue
            tiles[row][col] = tile_value
            changes += 1
            queue.extend([(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)])
        if changes:
            window = self.window()
            if hasattr(window, "mark_dirty"):
                window.mark_dirty()
            self.update()

    def _selection_bounds(self):
        if self._selection_start is None or self._selection_end is None:
            return None
        sr, sc = self._selection_start
        er, ec = self._selection_end
        return min(sr, er), min(sc, ec), max(sr, er), max(sc, ec)

    def _copy_selection(self):
        bounds = self._selection_bounds()
        if not self._map_data or bounds is None:
            return
        top, left, bottom, right = bounds
        layers = self._map_data.get("layers", [])
        if not layers:
            return
        layer_idx = min(self._active_layer_idx, len(layers) - 1)
        tiles = layers[layer_idx]["tiles"]
        self._clipboard_tiles = [
            [tiles[row][col] for col in range(left, right + 1)]
            for row in range(top, bottom + 1)
        ]

    def _paste_tiles(self, origin):
        if not self._map_data or not self._clipboard_tiles:
            return
        start_row, start_col = origin
        layers = self._map_data.get("layers", [])
        if not layers:
            return
        layer_idx = min(self._active_layer_idx, len(layers) - 1)
        tiles = layers[layer_idx]["tiles"]
        height = self._map_data.get("height", 0)
        width = self._map_data.get("width", 0)
        for row_offset, row_tiles in enumerate(self._clipboard_tiles):
            row = start_row + row_offset
            if not (0 <= row < height):
                continue
            for col_offset, tile_value in enumerate(row_tiles):
                col = start_col + col_offset
                if 0 <= col < width:
                    tiles[row][col] = tile_value
        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()
        self.update()

    def _delete_selection(self):
        bounds = self._selection_bounds()
        if not self._map_data or bounds is None:
            return
        top, left, bottom, right = bounds
        layers = self._map_data.get("layers", [])
        if not layers:
            return
        layer_idx = min(self._active_layer_idx, len(layers) - 1)
        tiles = layers[layer_idx]["tiles"]
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                tiles[row][col] = 0
        window = self.window()
        if hasattr(window, "mark_dirty"):
            window.mark_dirty()
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_B:
            self.set_tool("pen")
        elif key == Qt.Key_R:
            self.set_tool("rect")
        elif key == Qt.Key_F:
            self.set_tool("bucket")
        elif key == Qt.Key_S:
            self.set_tool("select")
        elif key == Qt.Key_E:
            self.set_erase_mode(not self._erase_mode)
        elif key == Qt.Key_Delete:
            self._delete_selection()
        elif event.matches(QKeySequence.Copy):
            self._copy_selection()
        elif event.matches(QKeySequence.Paste):
            if self._clipboard_tiles and self._selection_bounds() is not None:
                top, left, _bottom, _right = self._selection_bounds()
                self._paste_origin = (top, left)
            elif self._clipboard_tiles:
                self._paste_origin = (0, 0)
            self.update()
        elif key == Qt.Key_Escape:
            if self._paste_origin is not None:
                self._paste_origin = None
                self.update()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        pos = self._tile_at_pos(event.position())
        if pos is None:
            return
        self.setFocus()
        tile_value = 0 if (self._erase_mode or event.button() == Qt.RightButton) else self._selected_tile
        if self._tool == "bucket" and event.button() in (Qt.LeftButton, Qt.RightButton):
            self._apply_bucket(pos, tile_value)
            return
        if self._tool == "select" and event.button() == Qt.LeftButton:
            if self._paste_origin is not None and self._clipboard_tiles:
                self._paste_tiles(pos)
                self._paste_origin = None
                self._selection_start = pos
                rows = len(self._clipboard_tiles)
                cols = len(self._clipboard_tiles[0]) if rows else 0
                self._selection_end = (pos[0] + rows - 1, pos[1] + cols - 1)
                return
            self._selection_start = pos
            self._selection_end = pos
            self.update()
            return
        if self._tool == "rect" and event.button() in (Qt.LeftButton, Qt.RightButton):
            self._drag_start = pos
            self._drag_current = pos
            self.update()
            return
        self._painting = True
        row, col = pos
        self._paint_tile(row, col, tile_value)

    def mouseMoveEvent(self, event):
        buttons = event.buttons()
        pos = self._tile_at_pos(event.position())
        if pos is None:
            return
        if self._tool == "select" and self._selection_start is not None:
            if self._paste_origin is not None and self._clipboard_tiles:
                self._paste_origin = pos
                self.update()
                return
            self._selection_end = pos
            self.update()
            return
        if self._tool == "rect" and self._drag_start is not None:
            self._drag_current = pos
            self.update()
            return
        if not self._painting:
            return
        row, col = pos
        tile_value = 0 if (self._erase_mode or (buttons & Qt.RightButton)) else self._selected_tile
        if self._tool == "pen" and buttons & (Qt.LeftButton | Qt.RightButton):
            self._paint_tile(row, col, tile_value)

    def mouseReleaseEvent(self, event):
        if self._tool == "select":
            self.update()
            return
        if self._tool == "rect" and self._drag_start is not None:
            tile_value = 0 if (self._erase_mode or event.button() == Qt.RightButton) else self._selected_tile
            self._apply_rect(self._drag_start, self._drag_current, tile_value)
            self._drag_start = None
            self._drag_current = None
            self.update()
        self._painting = False

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self._zoom = min(8, self._zoom + 1)
        else:
            self._zoom = max(1, self._zoom - 1)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        if not self._map_data:
            painter.setPen(QColor(220, 220, 220))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Map Selected")
            return

        width = self._map_data.get("width", 0)
        height = self._map_data.get("height", 0)
        tile_size = self._map_data.get("tile_size", 16)
        draw_size = tile_size * self._zoom
        cols_in_tileset = max(1, self._tileset_image.width() // tile_size) if not self._tileset_image.isNull() else 1

        for row in range(height):
            for col in range(width):
                rect = self._tile_rect(col, row)
                painter.fillRect(rect, QColor(55, 55, 55))
                for layer in self._map_data.get("layers", []):
                    if not layer.get("visible", True):
                        continue
                    tiles = layer.get("tiles", [])
                    if row >= len(tiles) or col >= len(tiles[row]):
                        continue
                    tile_id = tiles[row][col]
                    if tile_id > 0 and not self._tileset_image.isNull():
                        idx = tile_id - 1
                        sx = (idx % cols_in_tileset) * tile_size
                        sy = (idx // cols_in_tileset) * tile_size
                        src = QRectF(sx, sy, tile_size, tile_size)
                        painter.drawImage(rect, self._tileset_image, src)
                painter.setPen(QPen(QColor(80, 80, 80), 1))
                painter.drawRect(rect)

        if self._drag_start is not None and self._drag_current is not None:
            sr, sc = self._drag_start
            er, ec = self._drag_current
            top, bottom = sorted((sr, er))
            left, right = sorted((sc, ec))
            preview = QRectF(
                left * draw_size,
                top * draw_size,
                (right - left + 1) * draw_size,
                (bottom - top + 1) * draw_size,
            )
            painter.fillRect(preview, QColor(255, 255, 0, 50))
            painter.setPen(QPen(QColor(255, 220, 0), 2))
            painter.drawRect(preview)

        bounds = self._selection_bounds()
        if bounds is not None:
            top, left, bottom, right = bounds
            selection_rect = QRectF(
                left * draw_size,
                top * draw_size,
                (right - left + 1) * draw_size,
                (bottom - top + 1) * draw_size,
            )
            painter.fillRect(selection_rect, QColor(0, 180, 255, 40))
            painter.setPen(QPen(QColor(0, 200, 255), 2, Qt.DashLine))
            painter.drawRect(selection_rect)

        if self._paste_origin is not None and self._clipboard_tiles:
            start_row, start_col = self._paste_origin
            rows = len(self._clipboard_tiles)
            cols = len(self._clipboard_tiles[0]) if rows else 0
            paste_rect = QRectF(
                start_col * draw_size,
                start_row * draw_size,
                cols * draw_size,
                rows * draw_size,
            )
            painter.fillRect(paste_rect, QColor(0, 255, 120, 40))
            painter.setPen(QPen(QColor(0, 255, 120), 2, Qt.DashLine))
            painter.drawRect(paste_rect)
            if not self._tileset_image.isNull() and rows and cols:
                tile_size = self._map_data.get("tile_size", 16)
                cols_in_tileset = max(1, self._tileset_image.width() // tile_size)
                for row_offset, row_tiles in enumerate(self._clipboard_tiles):
                    for col_offset, tile_id in enumerate(row_tiles):
                        if tile_id <= 0:
                            continue
                        idx = tile_id - 1
                        sx = (idx % cols_in_tileset) * tile_size
                        sy = (idx // cols_in_tileset) * tile_size
                        src = QRectF(sx, sy, tile_size, tile_size)
                        dest = QRectF(
                            (start_col + col_offset) * draw_size,
                            (start_row + row_offset) * draw_size,
                            draw_size,
                            draw_size,
                        )
                        painter.setOpacity(0.7)
                        painter.drawImage(dest, self._tileset_image, src)
                        painter.setOpacity(1.0)

        painter.setPen(QColor(230, 230, 230))
        painter.drawText(
            8, 16,
            f"Tool: {self._tool} {'(eraser)' if self._erase_mode else ''} Layer: {self._active_layer_idx}"
        )

        self.resize(width * draw_size + 2, height * draw_size + 2)


class MapPropertyPanel(QWidget):
    """マップ基本プロパティ。"""

    changed = Signal()
    tileset_changed = Signal(str)
    tool_changed = Signal(str)
    erase_mode_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._updating = False

        layout = QFormLayout(self)
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_changed)
        layout.addRow("Name:", self._name_edit)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 999)
        self._width_spin.valueChanged.connect(self._on_changed)
        layout.addRow("Width:", self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(1, 999)
        self._height_spin.valueChanged.connect(self._on_changed)
        layout.addRow("Height:", self._height_spin)

        self._tile_size_spin = QSpinBox()
        self._tile_size_spin.setRange(1, 128)
        self._tile_size_spin.valueChanged.connect(self._on_changed)
        layout.addRow("Tile Size:", self._tile_size_spin)

        self._tileset_combo = QComboBox()
        self._reload_tilesets()
        self._tileset_combo.currentTextChanged.connect(self._on_tileset_changed)
        layout.addRow("Tileset:", self._tileset_combo)

        self._tool_combo = QComboBox()
        self._tool_combo.addItems(["pen", "rect", "bucket", "select"])
        self._tool_combo.currentTextChanged.connect(self.tool_changed.emit)
        layout.addRow("Tool:", self._tool_combo)

        self._erase_check = QCheckBox("Eraser Mode (E)")
        self._erase_check.toggled.connect(self.erase_mode_changed.emit)
        layout.addRow("", self._erase_check)

    def _reload_tilesets(self):
        self._tileset_combo.clear()
        self._tileset_combo.addItem("")
        if os.path.isdir(TILESET_DIR):
            for fname in sorted(os.listdir(TILESET_DIR)):
                if fname.lower().endswith(".png"):
                    self._tileset_combo.addItem(fname)

    def set_data(self, map_data):
        self._data = map_data
        self._updating = True
        self._reload_tilesets()
        self._name_edit.setText(map_data.get("name", ""))
        self._width_spin.setValue(int(map_data.get("width", 20)))
        self._height_spin.setValue(int(map_data.get("height", 15)))
        self._tile_size_spin.setValue(int(map_data.get("tile_size", 16)))
        tileset_name = map_data.get("tileset", "")
        if tileset_name and self._tileset_combo.findText(tileset_name) < 0:
            self._tileset_combo.addItem(tileset_name)
        self._tileset_combo.setCurrentText(tileset_name)
        self._updating = False

    def _on_tileset_changed(self, value):
        if self._updating or not self._data:
            return
        self._data["tileset"] = value
        self.tileset_changed.emit(value)
        self.changed.emit()

    def _on_changed(self):
        if self._updating or not self._data:
            return
        self._data["name"] = self._name_edit.text()
        self._data["width"] = self._width_spin.value()
        self._data["height"] = self._height_spin.value()
        self._data["tile_size"] = self._tile_size_spin.value()
        self.changed.emit()


class LayerPanel(QWidget):
    """マップレイヤーの簡易操作パネル。"""

    active_layer_changed = Signal(int)
    layers_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_current_row_changed)
        layout.addWidget(self._list)

        buttons = QHBoxLayout()
        self._btn_add = QPushButton("+")
        self._btn_add.clicked.connect(self._add_layer)
        buttons.addWidget(self._btn_add)
        self._btn_del = QPushButton("-")
        self._btn_del.clicked.connect(self._delete_layer)
        buttons.addWidget(self._btn_del)
        self._btn_toggle = QPushButton("Toggle")
        self._btn_toggle.clicked.connect(self._toggle_visible)
        buttons.addWidget(self._btn_toggle)
        layout.addLayout(buttons)

    def set_data(self, map_data):
        self._data = map_data
        self._updating = True
        self._list.clear()
        for layer in map_data.get("layers", []):
            status = "[x]" if layer.get("visible", True) else "[ ]"
            self._list.addItem(f"{status} {layer.get('name', 'layer')}")
        if self._list.count():
            self._list.setCurrentRow(0)
        self._updating = False

    def set_active_layer(self, index):
        if 0 <= index < self._list.count():
            self._updating = True
            self._list.setCurrentRow(index)
            self._updating = False

    def _refresh(self):
        if self._data is not None:
            current = self._list.currentRow()
            self.set_data(self._data)
            if 0 <= current < self._list.count():
                self.set_active_layer(current)

    def _on_current_row_changed(self, row):
        if self._updating or row < 0:
            return
        self.active_layer_changed.emit(row)

    def _add_layer(self):
        if not self._data:
            return
        width = self._data.get("width", 1)
        height = self._data.get("height", 1)
        layers = self._data.setdefault("layers", [])
        layers.append({
            "name": f"layer_{len(layers)}",
            "visible": True,
            "tiles": [[0 for _ in range(width)] for _ in range(height)],
        })
        self._refresh()
        self.set_active_layer(len(layers) - 1)
        self.layers_changed.emit()

    def _delete_layer(self):
        if not self._data:
            return
        layers = self._data.setdefault("layers", [])
        row = self._list.currentRow()
        if len(layers) <= 1 or row < 0:
            return
        del layers[row]
        self._refresh()
        self.set_active_layer(max(0, min(row, len(layers) - 1)))
        self.layers_changed.emit()

    def _toggle_visible(self):
        if not self._data:
            return
        row = self._list.currentRow()
        layers = self._data.setdefault("layers", [])
        if not (0 <= row < len(layers)):
            return
        layers[row]["visible"] = not layers[row].get("visible", True)
        self._refresh()
        self.set_active_layer(row)
        self.layers_changed.emit()


class MapSidePanel(QWidget):
    """TilesetPalette と MapPropertyPanel のコンテナ。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("Tileset Palette"))
        self._palette = TilesetPalette()
        layout.addWidget(self._palette, 1)
        layout.addWidget(QLabel("Layers"))
        self._layers = LayerPanel()
        layout.addWidget(self._layers)
        layout.addWidget(QLabel("Map Properties"))
        self._properties = MapPropertyPanel()
        layout.addWidget(self._properties)


class CharacterEditor(QScrollArea):
    """Characters 編集フォーム。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._updating = False
        self._sprite_files = self._list_sprite_files()
        self._graphic_widgets = {}
        self._base_stat_spins = {}
        self._growth_stat_spins = {}
        self._physical_skill_spins = {}
        self._magic_skill_spins = {}

        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        basic_group = QGroupBox("Basic")
        basic_form = QFormLayout(basic_group)
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._on_changed)
        basic_form.addRow("Name:", self._name_edit)
        self._job_spin = QSpinBox()
        self._job_spin.setRange(0, 9999)
        self._job_spin.valueChanged.connect(self._on_changed)
        basic_form.addRow("Initial Job ID:", self._job_spin)
        self._personality_spin = QSpinBox()
        self._personality_spin.setRange(0, 9999)
        self._personality_spin.valueChanged.connect(self._on_changed)
        basic_form.addRow("Personality ID:", self._personality_spin)
        layout.addWidget(basic_group)

        graphic_group = QGroupBox("Graphics")
        graphic_layout = QVBoxLayout(graphic_group)
        for graphic_type, label in (("face", "Face"), ("walk", "Walk"), ("battle", "Battle")):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(QLabel(label + ":"))
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(self._sprite_files)
            combo.currentTextChanged.connect(self._on_changed)
            row_layout.addWidget(combo, 1)
            spin = QSpinBox()
            spin.setRange(0, 9999)
            spin.valueChanged.connect(self._on_changed)
            row_layout.addWidget(QLabel("Selection ID:"))
            row_layout.addWidget(spin)
            preview = QLabel("No Image")
            preview.setFixedSize(48, 48)
            preview.setAlignment(Qt.AlignCenter)
            preview.setStyleSheet("border: 1px solid #666; background: #222;")
            row_layout.addWidget(preview)
            graphic_layout.addWidget(row)
            self._graphic_widgets[graphic_type] = {
                "combo": combo,
                "spin": spin,
                "preview": preview,
            }
        layout.addWidget(graphic_group)

        base_group = QGroupBox("Base Stats")
        base_form = QFormLayout(base_group)
        for key in STAT_KEYS:
            spin = QSpinBox()
            spin.setRange(0, 999999)
            spin.valueChanged.connect(self._on_changed)
            base_form.addRow(STAT_LABELS[key] + ":", spin)
            self._base_stat_spins[key] = spin
        layout.addWidget(base_group)

        growth_stat_group = QGroupBox("Growth Rates - Stats")
        growth_stat_form = QFormLayout(growth_stat_group)
        for key in STAT_KEYS:
            spin = QSpinBox()
            spin.setRange(0, 999999)
            spin.valueChanged.connect(self._on_changed)
            growth_stat_form.addRow(STAT_LABELS[key] + ":", spin)
            self._growth_stat_spins[key] = spin
        layout.addWidget(growth_stat_group)

        physical_group = QGroupBox("Growth Rates - Physical Skills")
        physical_form = QFormLayout(physical_group)
        for key in PHYSICAL_SKILL_KEYS:
            spin = QSpinBox()
            spin.setRange(0, 999999)
            spin.valueChanged.connect(self._on_changed)
            physical_form.addRow(PHYSICAL_SKILL_LABELS[key] + ":", spin)
            self._physical_skill_spins[key] = spin
        layout.addWidget(physical_group)

        magic_group = QGroupBox("Growth Rates - Magic Skills")
        magic_form = QFormLayout(magic_group)
        for key in MAGIC_SKILL_KEYS:
            spin = QSpinBox()
            spin.setRange(0, 999999)
            spin.valueChanged.connect(self._on_changed)
            magic_form.addRow(MAGIC_SKILL_LABELS[key] + ":", spin)
            self._magic_skill_spins[key] = spin
        layout.addWidget(magic_group)
        layout.addStretch()

    def _list_sprite_files(self):
        if not os.path.isdir(SPRITE_DIR):
            return []
        return sorted(
            fname for fname in os.listdir(SPRITE_DIR)
            if os.path.isfile(os.path.join(SPRITE_DIR, fname))
            and fname.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        )

    def set_data(self, char_data):
        self._data = char_data
        self._updating = True

        self._name_edit.setText(char_data.get("name", ""))
        self._job_spin.setValue(int(char_data.get("initial_job", 0)))
        self._personality_spin.setValue(int(char_data.get("personality", 0)))

        graphics = char_data.get("graphics", {})
        for graphic_type, widgets in self._graphic_widgets.items():
            gdata = graphics.get(graphic_type, {})
            combo = widgets["combo"]
            image_name = gdata.get("image", "")
            if image_name and combo.findText(image_name) < 0:
                combo.addItem(image_name)
            combo.setCurrentText(image_name)
            widgets["spin"].setValue(int(gdata.get("selection_id", 0)))
            self._update_graphic_preview(graphic_type)

        base_stats = char_data.get("base_stats", {})
        for key, spin in self._base_stat_spins.items():
            spin.setValue(int(base_stats.get(key, 0)))

        growth = char_data.get("growth_rates", {})
        growth_stats = growth.get("stats", {})
        for key, spin in self._growth_stat_spins.items():
            spin.setValue(int(growth_stats.get(key, 0)))

        physical = growth.get("physical_skills", {})
        for key, spin in self._physical_skill_spins.items():
            spin.setValue(int(physical.get(key, 0)))

        magic = growth.get("magic_skills", {})
        for key, spin in self._magic_skill_spins.items():
            spin.setValue(int(magic.get(key, 0)))

        self._updating = False

    def _update_graphic_preview(self, graphic_type):
        widgets = self._graphic_widgets[graphic_type]
        image_name = widgets["combo"].currentText().strip()
        preview = widgets["preview"]
        if not image_name:
            preview.setText("No Image")
            preview.setPixmap(QPixmap())
            return

        image_path = os.path.join(SPRITE_DIR, image_name)
        image = QImage(image_path)
        if image.isNull():
            preview.setText("Load Error")
            preview.setPixmap(QPixmap())
            return

        selection_id = widgets["spin"].value()
        cols = max(1, image.width() // GRAPHIC_CUT_SIZE)
        x = (selection_id % cols) * GRAPHIC_CUT_SIZE
        y = (selection_id // cols) * GRAPHIC_CUT_SIZE
        if x + GRAPHIC_CUT_SIZE > image.width() or y + GRAPHIC_CUT_SIZE > image.height():
            x = 0
            y = 0
        cropped = image.copy(x, y, GRAPHIC_CUT_SIZE, GRAPHIC_CUT_SIZE)
        pixmap = QPixmap.fromImage(cropped).scaled(
            preview.width(),
            preview.height(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        )
        preview.setText("")
        preview.setPixmap(pixmap)

    def _on_changed(self):
        if self._updating or not self._data:
            return

        self._data["name"] = self._name_edit.text()
        self._data["initial_job"] = self._job_spin.value()
        self._data["personality"] = self._personality_spin.value()

        graphics = self._data.setdefault("graphics", {})
        for graphic_type, widgets in self._graphic_widgets.items():
            graphics[graphic_type] = {
                "image": widgets["combo"].currentText().strip(),
                "selection_id": widgets["spin"].value(),
            }
            self._update_graphic_preview(graphic_type)

        base_stats = self._data.setdefault("base_stats", {})
        for key, spin in self._base_stat_spins.items():
            base_stats[key] = spin.value()

        growth = self._data.setdefault("growth_rates", {})
        stats = growth.setdefault("stats", {})
        for key, spin in self._growth_stat_spins.items():
            stats[key] = spin.value()

        physical = growth.setdefault("physical_skills", {})
        for key, spin in self._physical_skill_spins.items():
            physical[key] = spin.value()

        magic = growth.setdefault("magic_skills", {})
        for key, spin in self._magic_skill_spins.items():
            magic[key] = spin.value()

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
        self._mode = "text"  # "text" | "map" | "character"
        self._map_file_data = {}
        self._current_map_path = None
        self._map_snapshot = None
        self._char_file_data = {}
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
        self._splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self._splitter)
        self.setCentralWidget(main_widget)

        # 左: ファイルツリー
        self._tree = FileTreePanel()
        self._tree.currentItemChanged.connect(self._on_tree_selected)
        self._tree.rename_requested.connect(self._on_rename_requested)
        self._tree.setMinimumWidth(180)
        self._splitter.addWidget(self._tree)

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

        # Events 編集
        self._event_editor = EventEditor()
        self._stack.addWidget(self._event_editor)

        # Characters 編集
        self._char_editor = CharacterEditor()
        self._stack.addWidget(self._char_editor)

        center_layout.addWidget(self._stack)
        self._splitter.addWidget(center)

        # 右: プレビューパネル
        self._preview = PreviewPanel()
        self._splitter.addWidget(self._preview)

        self._map_canvas = MapCanvas()
        self._map_canvas.hide()
        self._splitter.addWidget(self._map_canvas)

        self._map_side_panel = MapSidePanel()
        self._map_side_panel.hide()
        self._map_side_panel._palette.tile_selected.connect(self._map_canvas.set_selected_tile)
        self._map_side_panel._layers.active_layer_changed.connect(self._map_canvas.set_active_layer)
        self._map_side_panel._layers.layers_changed.connect(self._on_map_layers_changed)
        self._map_side_panel._properties.changed.connect(self._on_map_property_changed)
        self._map_side_panel._properties.tileset_changed.connect(self._on_map_tileset_changed)
        self._map_side_panel._properties.tool_changed.connect(self._map_canvas.set_tool)
        self._map_side_panel._properties.erase_mode_changed.connect(self._map_canvas.set_erase_mode)
        self._splitter.addWidget(self._map_side_panel)

        self._splitter.setSizes([200, 500, 400, 0, 0])

        # ステータスバー
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File メニュー
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._save_current)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        self._new_char_file_action = QAction("New Character File...", self)
        self._new_char_file_action.triggered.connect(self._new_char_file)
        file_menu.addAction(self._new_char_file_action)

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

        mode_menu = menubar.addMenu("Mode")
        self._mode_group = QActionGroup(self)
        self._mode_group.setExclusive(True)

        self._text_mode_action = QAction("Text Editor", self, checkable=True)
        self._text_mode_action.setChecked(True)
        self._text_mode_action.triggered.connect(
            lambda checked: checked and self._switch_mode("text")
        )
        self._mode_group.addAction(self._text_mode_action)
        mode_menu.addAction(self._text_mode_action)

        self._map_mode_action = QAction("Map Editor", self, checkable=True)
        self._map_mode_action.triggered.connect(
            lambda checked: checked and self._switch_mode("map")
        )
        self._mode_group.addAction(self._map_mode_action)
        mode_menu.addAction(self._map_mode_action)

        self._character_mode_action = QAction("Character Editor", self, checkable=True)
        self._character_mode_action.triggered.connect(
            lambda checked: checked and self._switch_mode("character")
        )
        self._mode_group.addAction(self._character_mode_action)
        mode_menu.addAction(self._character_mode_action)

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

        self._new_map_action = QAction("New Map...", self)
        self._new_map_action.triggered.connect(self._new_map)
        edit_menu.addAction(self._new_map_action)

        rename_id_action = QAction("Rename ID... (F2)", self)
        rename_id_action.setShortcut(QKeySequence("F2"))
        rename_id_action.triggered.connect(self._rename_id)
        edit_menu.addAction(rename_id_action)

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
        if self._mode == "map":
            self._load_map_files()
        elif self._mode == "character":
            self._load_char_files()
        else:
            self._load_all_files()
        self._undo_stack.clear()
        self._snapshot = None
        self._map_snapshot = None
        self._current_entry = None
        self._stack.setCurrentWidget(self._empty_page)
        self._id_label.setText("Select an item from the tree")

    def _on_tree_selected(self, current, previous):
        if self._mode == "map":
            self._on_map_tree_selected(current, previous)
            return
        if self._mode == "character":
            self._on_char_tree_selected(current, previous)
            return
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
        elif cat == "events":
            self._event_editor.set_data(entry_data)
            self._stack.setCurrentWidget(self._event_editor)

        self._update_preview()

    def _flush_undo(self):
        """現在のエントリへの変更が未コミットなら UndoStack に push する。"""
        if self._mode == "map":
            if not self._current_map_path or self._map_snapshot is None:
                return
            if self._current_map_path not in self._map_file_data:
                return
            current_copy = copy.deepcopy(self._map_file_data[self._current_map_path])
            if current_copy != self._map_snapshot:
                cmd = MapEditCommand(
                    self._map_file_data,
                    self._current_map_path,
                    self._map_snapshot,
                    current_copy,
                    f"Edit map {os.path.basename(self._current_map_path)}",
                )
                self._pushing_undo = True
                self._undo_stack.push(cmd)
                self._pushing_undo = False
                self._map_snapshot = copy.deepcopy(current_copy)
            return
        if not self._current_entry or self._snapshot is None:
            return
        filepath, cat, entry_id = self._current_entry
        store = self._get_store(cat)
        if filepath not in store:
            return
        current_data = store[filepath][cat].get(entry_id)
        if current_data is None:
            return
        current_copy = copy.deepcopy(current_data)
        if current_copy != self._snapshot:
            cmd = EditCommand(
                store, filepath, cat, entry_id,
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
        if self._mode == "text":
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
        mode_title = {
            "text": "Text Editor",
            "map": "Map Editor",
            "character": "Character Editor",
        }.get(self._mode, "Editor")
        self.setWindowTitle(f"{mode_title}{marker}")

    def _get_store(self, category=None):
        if category == "characters" or self._mode == "character":
            return self._char_file_data
        return self._file_data

    def _save_current(self):
        """現在のモードに応じた保存処理。"""
        if self._mode == "text":
            self._save_all()
        elif self._mode == "map":
            self._save_map()
        elif self._mode == "character":
            self._save_char_files()

    def _save_map(self):
        """現在のマップを保存する。"""
        if not self._current_map_path or self._current_map_path not in self._map_file_data:
            self._statusbar.showMessage("No map selected", 3000)
            return
        self._flush_undo()
        try:
            with open(self._current_map_path, "w", encoding="utf-8") as f:
                json.dump(self._map_file_data[self._current_map_path], f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._statusbar.showMessage(f"Save error: {e}", 5000)
            return
        self._dirty = False
        self._update_title()
        self._undo_stack.setClean()
        self._statusbar.showMessage(f"Saved map: {os.path.basename(self._current_map_path)}", 3000)

    def _save_char_files(self):
        """キャラクターファイルを保存する。"""
        self._flush_undo()
        os.makedirs(CHAR_DIR, exist_ok=True)

        for filepath, data in self._char_file_data.items():
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
            f"Saved {len(self._char_file_data)} character file(s)", 3000)

    def _switch_mode(self, mode):
        """編集モードを切り替える。"""
        if mode == self._mode:
            return

        if mode == "text":
            self._mode = "text"
            self._tree.setHeaderLabel("Text Files")
            self._load_all_files()
            self._stack.setCurrentWidget(self._empty_page)
            self._map_canvas.hide()
            self._map_side_panel.hide()
            self._preview.show()
            self._preview.clear_preview()
            self._current_entry = None
            self._snapshot = None
            self._map_snapshot = None
            self._text_mode_action.setChecked(True)
            self._update_title()
            self._splitter.setSizes([200, 500, 400, 0, 0])
            self._statusbar.showMessage("Switched to Text Editor", 2000)
            return

        if mode == "character":
            self._mode = "character"
            self._character_mode_action.setChecked(True)
            self._load_char_files()
            self._stack.setCurrentWidget(self._empty_page)
            self._map_canvas.hide()
            self._map_side_panel.hide()
            self._preview.clear_preview()
            self._preview.hide()
            self._current_entry = None
            self._snapshot = None
            self._map_snapshot = None
            self._update_title()
            self._splitter.setSizes([220, 700, 0, 0, 0])
            self._statusbar.showMessage("Switched to Character Editor", 2000)
            return

        if mode == "map":
            self._mode = "map"
            self._map_mode_action.setChecked(True)
            self._load_map_files()
            self._stack.setCurrentWidget(self._empty_page)
            self._preview.clear_preview()
            self._preview.hide()
            self._map_canvas.show()
            self._map_side_panel.show()
            self._current_entry = None
            self._snapshot = None
            self._map_snapshot = None
            self._update_title()
            self._splitter.setSizes([220, 0, 0, 700, 280])
            self._statusbar.showMessage("Switched to Map Editor", 2000)
            return

        target_name = "Map Editor" if mode == "map" else "Character Editor"
        QMessageBox.information(
            self,
            "Not Implemented",
            f"{target_name} is not implemented yet.",
        )
        self._mode = "text"
        self._tree.setHeaderLabel("Text Files")
        self._load_all_files()
        self._stack.setCurrentWidget(self._empty_page)
        self._preview.show()
        self._preview.clear_preview()
        self._current_entry = None
        self._snapshot = None
        self._map_snapshot = None
        self._text_mode_action.setChecked(True)
        self._update_title()

    def _load_char_files(self):
        """data/characters/ 内の全JSONを読み込む。"""
        self._char_file_data.clear()
        os.makedirs(CHAR_DIR, exist_ok=True)

        for fname in sorted(os.listdir(CHAR_DIR)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(CHAR_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "characters" not in data:
                    data["characters"] = {}
                self._char_file_data[fpath] = data
            except Exception as e:
                self._statusbar.showMessage(f"Load error: {fname}: {e}", 5000)

        self._build_char_tree()
        self._statusbar.showMessage(
            f"Loaded {len(self._char_file_data)} character file(s)", 3000)

    def _load_map_files(self):
        """data/maps/ 内の全JSONを読み込む。"""
        self._map_file_data.clear()
        os.makedirs(MAP_DIR, exist_ok=True)
        for fname in sorted(os.listdir(MAP_DIR)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(MAP_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    self._map_file_data[fpath] = json.load(f)
            except Exception as e:
                self._statusbar.showMessage(f"Load error: {fname}: {e}", 5000)
        self._build_map_tree()
        self._statusbar.showMessage(f"Loaded {len(self._map_file_data)} map file(s)", 3000)

    def _build_map_tree(self):
        self._tree.clear()
        self._tree.setHeaderLabel("Map Files")
        for filepath, data in sorted(self._map_file_data.items()):
            label = data.get("name") or os.path.basename(filepath)
            item = QTreeWidgetItem(self._tree, [label])
            item.setData(0, Qt.UserRole, {
                "type": "map_entry",
                "path": filepath,
            })

    def _on_map_tree_selected(self, current, previous):
        if not current:
            return
        info = current.data(0, Qt.UserRole)
        if not info or info.get("type") != "map_entry":
            self._current_map_path = None
            self._map_snapshot = None
            self._id_label.setText("Select a map to edit")
            self._map_canvas.set_map_data(None)
            return
        filepath = info["path"]
        self._flush_undo()
        self._current_map_path = filepath
        map_data = self._map_file_data[filepath]
        self._map_snapshot = copy.deepcopy(map_data)
        self._id_label.setText(f"Map > {map_data.get('name', os.path.basename(filepath))}")
        self._map_canvas.set_map_data(map_data)
        self._map_canvas.set_active_layer(0)
        self._map_side_panel._layers.set_data(map_data)
        self._map_side_panel._layers.set_active_layer(0)
        self._map_side_panel._properties.set_data(map_data)
        self._map_side_panel._palette.load_tileset(map_data.get("tileset", ""), map_data.get("tile_size", 16))

    def _on_map_property_changed(self):
        if self._mode != "map" or not self._current_map_path:
            return
        map_data = self._map_file_data[self._current_map_path]
        width = map_data.get("width", 1)
        height = map_data.get("height", 1)
        for layer in map_data.get("layers", []):
            old_tiles = layer.get("tiles", [])
            resized = []
            for row in range(height):
                src_row = old_tiles[row] if row < len(old_tiles) else []
                resized.append((src_row + [0] * width)[:width])
            layer["tiles"] = resized
        self._map_canvas.set_map_data(map_data)
        self._map_side_panel._layers.set_data(map_data)
        self.mark_dirty()

    def _on_map_tileset_changed(self, tileset_name):
        if self._mode != "map" or not self._current_map_path:
            return
        map_data = self._map_file_data[self._current_map_path]
        map_data["tileset"] = tileset_name
        self._map_canvas.set_map_data(map_data)
        self._map_side_panel._palette.load_tileset(tileset_name, map_data.get("tile_size", 16))
        self.mark_dirty()

    def _on_map_layers_changed(self):
        if self._mode != "map" or not self._current_map_path:
            return
        map_data = self._map_file_data[self._current_map_path]
        active = self._map_side_panel._layers._list.currentRow()
        self._map_canvas.set_map_data(map_data)
        self._map_canvas.set_active_layer(max(0, active))
        self.mark_dirty()

    def _new_map(self):
        if self._mode != "map":
            self._statusbar.showMessage("Switch to Map Editor first", 3000)
            return
        map_name, ok = QInputDialog.getText(self, "New Map", "Map name:")
        if not ok or not map_name.strip():
            return
        map_name = map_name.strip()
        safe_name = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in map_name)
        filepath = os.path.join(MAP_DIR, f"{safe_name or 'new_map'}.json")
        if filepath in self._map_file_data or os.path.exists(filepath):
            QMessageBox.warning(self, "Error", f"Map '{os.path.basename(filepath)}' already exists")
            return
        self._map_file_data[filepath] = _create_default_map(map_name)
        self._build_map_tree()
        self.mark_dirty()
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            info = item.data(0, Qt.UserRole)
            if info and info.get("path") == filepath:
                self._tree.setCurrentItem(item)
                self._on_map_tree_selected(item, None)
                break

    def _build_char_tree(self):
        self._tree.clear()
        self._tree.setHeaderLabel("Character Files")
        for filepath, data in sorted(self._char_file_data.items()):
            filename = os.path.basename(filepath)
            file_item = QTreeWidgetItem(self._tree, [filename])
            file_item.setData(0, Qt.UserRole, {"type": "file", "path": filepath})
            file_item.setExpanded(True)

            cat_item = QTreeWidgetItem(file_item, ["Characters"])
            cat_item.setData(0, Qt.UserRole, {
                "type": "category", "category": "characters", "path": filepath,
            })
            cat_item.setExpanded(True)

            for entry_id in data.get("characters", {}):
                entry_item = QTreeWidgetItem(cat_item, [entry_id])
                entry_item.setData(0, Qt.UserRole, {
                    "type": "entry", "category": "characters",
                    "entry_id": entry_id, "path": filepath,
                })

    def _on_char_tree_selected(self, current, previous):
        if not current:
            return
        info = current.data(0, Qt.UserRole)
        if not info or info["type"] != "entry":
            self._stack.setCurrentWidget(self._empty_page)
            self._id_label.setText("Select a character entry to edit")
            self._current_entry = None
            return

        filepath = info["path"]
        entry_id = info["entry_id"]
        self._flush_undo()

        entry_data = self._char_file_data[filepath]["characters"][entry_id]
        self._current_entry = (filepath, "characters", entry_id)
        self._snapshot = copy.deepcopy(entry_data)
        self._id_label.setText(f"{os.path.basename(filepath)} > Characters > {entry_id}")
        self._char_editor.set_data(entry_data)
        self._stack.setCurrentWidget(self._char_editor)

    def _new_char_file(self):
        if self._mode != "character":
            self._statusbar.showMessage("Switch to Character Editor first", 3000)
            return
        file_id, ok = QInputDialog.getText(self, "New Character File", "File ID:")
        if not ok or not file_id.strip():
            return
        file_id = file_id.strip()
        filepath = os.path.join(CHAR_DIR, f"{file_id}.json")
        if filepath in self._char_file_data or os.path.exists(filepath):
            QMessageBox.warning(self, "Error", f"File '{file_id}.json' already exists")
            return
        self._char_file_data[filepath] = {
            "version": 1,
            "file_id": file_id,
            "characters": {},
        }
        self.mark_dirty()
        self._build_char_tree()
        self._statusbar.showMessage(f"Created: {file_id}.json", 3000)

    def _add_char_id(self):
        item = self._tree.currentItem()
        if not item:
            return
        info = item.data(0, Qt.UserRole)
        if not info:
            return
        if info["type"] == "category":
            filepath = info["path"]
        elif info["type"] == "entry":
            filepath = info["path"]
        else:
            self._statusbar.showMessage("Select a character category or entry first", 3000)
            return
        new_id, ok = QInputDialog.getText(self, "Add Character", "New character ID:")
        if not ok or not new_id.strip():
            return
        new_id = new_id.strip()
        chars = self._char_file_data[filepath]["characters"]
        if new_id in chars:
            QMessageBox.warning(self, "Error", f"ID '{new_id}' already exists")
            return
        chars[new_id] = copy.deepcopy(DEFAULT_CHARACTER)
        self.mark_dirty()
        self._build_char_tree()
        self._select_tree_entry(filepath, "characters", new_id)
        self._statusbar.showMessage(f"Added: characters.{new_id}", 3000)

    def _delete_char_id(self):
        if not self._current_entry:
            return
        filepath, cat, entry_id = self._current_entry
        reply = QMessageBox.question(
            self, "Delete", f"Delete {cat}.{entry_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        del self._char_file_data[filepath]["characters"][entry_id]
        self._current_entry = None
        self._snapshot = None
        self.mark_dirty()
        self._build_char_tree()
        self._stack.setCurrentWidget(self._empty_page)
        self._id_label.setText("Select a character entry to edit")
        self._statusbar.showMessage(f"Deleted: {cat}.{entry_id}", 3000)

    def _rename_char_id(self):
        if not self._current_entry:
            self._statusbar.showMessage("Select an entry to rename", 3000)
            return
        filepath, cat, old_id = self._current_entry
        new_id, ok = QInputDialog.getText(
            self, "Rename ID", f"New name for '{old_id}':", text=old_id)
        if not ok or not new_id.strip():
            return
        new_id = new_id.strip()
        if new_id == old_id:
            return
        chars = self._char_file_data[filepath]["characters"]
        if new_id in chars:
            QMessageBox.warning(self, "Error", f"ID '{new_id}' already exists")
            return
        self._flush_undo()
        cmd = RenameCommand(
            self._char_file_data, filepath, "characters", old_id, new_id,
            f"Rename characters.{old_id} -> {new_id}",
        )
        self._pushing_undo = True
        self._undo_stack.push(cmd)
        self._pushing_undo = False
        self._current_entry = (filepath, "characters", new_id)
        self._snapshot = copy.deepcopy(chars[new_id])
        self._dirty = True
        self._update_title()
        self._build_char_tree()
        self._select_tree_entry(filepath, "characters", new_id)
        self._statusbar.showMessage(f"Renamed: {old_id} -> {new_id}", 3000)

    def _on_undo_clean_changed(self, clean):
        """UndoStack の clean 状態変化時。"""
        if not clean:
            self._dirty = True
            self._update_title()

    def _on_undo_or_redo(self):
        """Undo/Redo 実行後にエディタUIを再読み込みする。"""
        if self._pushing_undo or self._closing:
            return
        if self._mode == "map":
            if not self._current_map_path or self._current_map_path not in self._map_file_data:
                return
            map_data = self._map_file_data[self._current_map_path]
            self._map_snapshot = copy.deepcopy(map_data)
            self._map_canvas.set_map_data(map_data)
            self._map_side_panel._properties.set_data(map_data)
            self._map_side_panel._palette.load_tileset(
                map_data.get("tileset", ""),
                map_data.get("tile_size", 16),
            )
            self._dirty = True
            self._update_title()
            return
        if not self._current_entry:
            return
        filepath, cat, entry_id = self._current_entry
        store = self._get_store(cat)
        if filepath not in store:
            return
        data = store[filepath]

        # リネーム Undo/Redo でIDが変わった場合: ツリー再構築してリセット
        if entry_id not in data.get(cat, {}):
            if cat == "characters":
                self._build_char_tree()
            else:
                self._tree.load_files(self._file_data)
            self._current_entry = None
            self._snapshot = None
            self._stack.setCurrentWidget(self._empty_page)
            self._id_label.setText(
                "Select a character entry to edit" if cat == "characters"
                else "Select an item from the tree"
            )
            self._preview.clear_preview()
            self._dirty = True
            self._update_title()
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
        elif cat == "events":
            self._event_editor.set_data(entry_data)
        elif cat == "characters":
            self._char_editor.set_data(entry_data)

        self._dirty = True
        self._update_title()
        if cat != "characters":
            self._update_preview()

    def _update_preview(self):
        """現在の編集内容でプレビューを更新する。"""
        if self._mode != "text" or not self._current_entry:
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
            self._save_current()

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
        if self._mode == "character":
            self._add_char_id()
            return
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
        elif cat == "events":
            data[cat][new_id] = [{"cmd": "wait", "duration": 60}]

        self.mark_dirty()
        self._tree.load_files(self._file_data)
        self._statusbar.showMessage(f"Added: {cat}.{new_id}", 3000)

    def _delete_id(self):
        """選択中のIDを削除する。"""
        if self._mode == "character":
            self._delete_char_id()
            return
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

    # --- リネーム機能 ---

    def _on_rename_requested(self, item):
        """右クリックメニューからのリネーム要求。"""
        info = item.data(0, Qt.UserRole)
        if not info or info["type"] != "entry":
            return
        self._tree.setCurrentItem(item)
        self._rename_id()

    def _rename_id(self):
        """選択中のIDをリネームする。"""
        if self._mode == "character":
            self._rename_char_id()
            return
        if not self._current_entry:
            self._statusbar.showMessage("Select an entry to rename", 3000)
            return
        filepath, cat, old_id = self._current_entry

        new_id, ok = QInputDialog.getText(
            self, "Rename ID", f"New name for '{old_id}':", text=old_id)
        if not ok or not new_id.strip():
            return
        new_id = new_id.strip()

        if new_id == old_id:
            return

        data = self._file_data[filepath]
        if new_id in data[cat]:
            QMessageBox.warning(self, "Error", f"ID '{new_id}' already exists")
            return

        # 未確定の編集変更を flush
        self._flush_undo()

        # Undo 対応のリネームコマンドを push
        cmd = RenameCommand(
            self._file_data, filepath, cat, old_id, new_id,
            f"Rename {cat}.{old_id} -> {new_id}",
        )
        self._pushing_undo = True
        self._undo_stack.push(cmd)
        self._pushing_undo = False

        # 現在のエントリ参照を更新
        self._current_entry = (filepath, cat, new_id)
        self._snapshot = copy.deepcopy(data[cat][new_id])

        self._dirty = True
        self._update_title()
        self._tree.load_files(self._file_data)

        # リネーム後のアイテムを再選択
        self._select_tree_entry(filepath, cat, new_id)
        self._statusbar.showMessage(f"Renamed: {old_id} -> {new_id}", 3000)

    def _select_tree_entry(self, filepath, cat, entry_id):
        """ツリー上の指定エントリを選択する。"""
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
        if self._mode != "text":
            self._search_results.clear()
            self._search_index = -1
            self._search_count_label.setText("")
            return
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
        elif cat == "events":
            for cmd in entry_data:
                if query in cmd.get("cmd", "").lower():
                    return True
                for value in cmd.values():
                    if isinstance(value, str) and query in value.lower():
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
                self._save_current()
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
