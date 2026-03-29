"""テキストエディタ v1。

テキストデータの閲覧・プレビュー・コンパイルを行うPyxelアプリ。

使い方:
    .venv/Scripts/python tools/editor_app.py

操作:
    Up/Down : テキストID選択
    F5      : コンパイル実行（JSON → bin）
    F9      : JSONリロード
    ESC     : 終了
"""

import json
import os
import subprocess
import sys

# src/ を import パスに追加
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TOOLS_DIR, ".."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src"))
sys.path.insert(0, _TOOLS_DIR)

import pyxel

import config
from panels.text_panel import TextPanel
from panels.preview_panel import PreviewPanel
from editor_config import (
    SCREEN_W, SCREEN_H, DISPLAY_SCALE,
    HEADER_H, STATUS_H, TEXT_PANEL_W,
    PREVIEW_X, PREVIEW_W, PANEL_Y, PANEL_H, STATUS_Y,
)

# パス
TEXT_DIR = os.path.join(_PROJECT_ROOT, "data", "text")
JSON_PATH = os.path.join(TEXT_DIR, "demo_text.json")
COMPILER_PATH = os.path.join(_TOOLS_DIR, "compiler.py")

# ステータスバー
STATUS_DISPLAY_FRAMES = 180  # 3秒（60fps）


class EditorApp:
    """テキストエディタ本体。"""

    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Text Editor v1",
                   display_scale=DISPLAY_SCALE)
        config.init_font()

        self._font = config.FONT
        self._data = None
        self._status_msg = ""
        self._status_timer = 0
        self._status_color = 7

        # パネル生成
        self._text_panel = TextPanel(
            0, PANEL_Y, TEXT_PANEL_W, PANEL_H, self._font)
        self._preview_panel = PreviewPanel(
            PREVIEW_X, PANEL_Y, PREVIEW_W, PANEL_H, self._font)

        # テキスト一覧の選択変更 → プレビュー更新
        self._text_panel.set_on_select(self._on_text_selected)

        # テキスト一覧をアクティブに
        self._text_panel.on_activate()

        # JSONデータ読み込み
        self._load_json()

        pyxel.run(self.update, self.draw)

    def _load_json(self):
        """JSONファイルを読み込む。"""
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            self._text_panel.set_data(self._data)
            self._preview_panel.set_data(self._data)
            self._set_status("JSON loaded", 11)
        except Exception as e:
            self._set_status(f"Load error: {e}", 8)

    def _compile(self):
        """コンパイラを実行する。"""
        self._set_status("Compiling...", 10)
        try:
            python = sys.executable
            result = subprocess.run(
                [python, COMPILER_PATH],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                self._set_status("Compile OK!", 11)
            else:
                err = result.stderr.strip().split("\n")[-1] if result.stderr else "Unknown error"
                self._set_status(f"Compile error: {err}", 8)
        except Exception as e:
            self._set_status(f"Compile error: {e}", 8)

    def _set_status(self, msg, color=7):
        """ステータスバーにメッセージを表示する。"""
        self._status_msg = msg
        self._status_color = color
        self._status_timer = STATUS_DISPLAY_FRAMES

    def _on_text_selected(self, category, entry_id):
        """テキスト一覧で選択が変わった時のコールバック。"""
        self._preview_panel.show_preview(category, entry_id)

    def update(self):
        # ESC: 終了
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
            return

        # F5: コンパイル
        if pyxel.btnp(pyxel.KEY_F5):
            self._compile()
            return

        # F9: リロード
        if pyxel.btnp(pyxel.KEY_F9):
            self._load_json()
            return

        # パネル更新
        self._text_panel.update()

        # ステータスタイマー
        if self._status_timer > 0:
            self._status_timer -= 1

    def draw(self):
        pyxel.cls(0)
        font = self._font

        # ヘッダー
        pyxel.rect(0, 0, SCREEN_W, HEADER_H, 1)
        pyxel.text(4, 2, "Text Editor v1", 7, font)
        help_text = "F5:Compile  F9:Reload  ESC:Quit"
        help_w = font.text_width(help_text) if font else len(help_text) * 4
        pyxel.text(SCREEN_W - help_w - 4, 2, help_text, 5, font)

        # パネル描画
        self._text_panel.draw()
        self._preview_panel.draw()

        # ステータスバー
        pyxel.rect(0, STATUS_Y, SCREEN_W, STATUS_H, 1)
        if self._status_timer > 0:
            pyxel.text(4, STATUS_Y + 1, self._status_msg,
                       self._status_color, font)


if __name__ == "__main__":
    EditorApp()
