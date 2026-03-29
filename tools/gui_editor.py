"""PySide6 テキストエディタ。

テキストデータの閲覧・編集・コンパイルを行うGUIアプリ。

使い方:
    .venv/Scripts/python tools/gui_editor.py
"""

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
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QFont

# カテゴリ表示名
CATEGORY_LABELS = {
    "messages": "Messages",
    "selections": "Selections",
    "telops": "Telops",
}
CATEGORIES = ["messages", "selections", "telops"]


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

    def _next_page(self):
        if self._data and self._page < len(self._data) - 1:
            self._page += 1
            self._show_page()

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
        self.resize(1000, 650)

        self._file_data = {}  # { filepath: data }
        self._dirty = False
        self._current_entry = None  # (filepath, category, entry_id)

        self._setup_ui()
        self._setup_menu()
        self._load_all_files()

    def _setup_ui(self):
        # メインスプリッター
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # 左: ファイルツリー
        self._tree = FileTreePanel()
        self._tree.currentItemChanged.connect(self._on_tree_selected)
        self._tree.setMinimumWidth(180)
        splitter.addWidget(self._tree)

        # 右: 編集エリア（スタックウィジェット）
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._id_label = QLabel("Select an item from the tree")
        self._id_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        right_layout.addWidget(self._id_label)

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

        right_layout.addWidget(self._stack)
        splitter.addWidget(right)

        splitter.setSizes([220, 780])

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

        # Edit メニュー
        edit_menu = menubar.addMenu("Edit")

        add_id_action = QAction("Add ID...", self)
        add_id_action.triggered.connect(self._add_id)
        edit_menu.addAction(add_id_action)

        del_id_action = QAction("Delete ID", self)
        del_id_action.setShortcut(QKeySequence("Delete"))
        del_id_action.triggered.connect(self._delete_id)
        edit_menu.addAction(del_id_action)

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
            return

        cat = info["category"]
        entry_id = info["entry_id"]
        filepath = info["path"]
        data = self._file_data[filepath]
        entry_data = data[cat][entry_id]

        self._current_entry = (filepath, cat, entry_id)
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

    def mark_dirty(self):
        self._dirty = True
        self._update_title()

    def _update_title(self):
        marker = " *" if self._dirty else ""
        self.setWindowTitle(f"Text Editor{marker}")

    def _save_all(self):
        """変更を全ファイルに保存する。"""
        for filepath, data in self._file_data.items():
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self._statusbar.showMessage(f"Save error: {e}", 5000)
                return

        self._dirty = False
        self._update_title()
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

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                self._save_all()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = EditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
