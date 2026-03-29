"""エディタのスクリーンショット撮影用ハーネス。"""

import json
import os
import sys

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TOOLS_DIR, ".."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src"))
sys.path.insert(0, _TOOLS_DIR)

import pyxel
from PIL import Image

import config
from panels.text_panel import TextPanel
from panels.preview_panel import PreviewPanel
from editor_config import (
    SCREEN_W, SCREEN_H, DISPLAY_SCALE,
    HEADER_H, STATUS_H, TEXT_PANEL_W,
    PREVIEW_X, PREVIEW_W, PANEL_Y, PANEL_H, STATUS_Y,
)

SCREENSHOT_DIR = os.path.join(_PROJECT_ROOT, "screenshots")
JSON_PATH = os.path.join(_PROJECT_ROOT, "data", "text", "demo.json")

PALETTE = [
    (0, 0, 0), (43, 51, 95), (126, 32, 114), (25, 149, 156),
    (139, 72, 82), (57, 92, 152), (169, 193, 255), (238, 238, 238),
    (212, 24, 108), (211, 132, 65), (233, 195, 91), (112, 198, 169),
    (118, 150, 222), (163, 163, 163), (255, 151, 152), (237, 199, 176),
]


class EditorHarness:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Editor Harness",
                   display_scale=DISPLAY_SCALE)
        config.init_font()
        self._font = config.FONT
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self._shots = self._define_shots()
        self._index = 0
        self._phase = 0
        self._saved = 0

        print(f"\nEditor Harness: {len(self._shots)} shots")
        pyxel.run(self.update, self.draw)

    def _define_shots(self):
        return [
            ("editor_messages_preview", "messages", "msg_basic"),
            ("editor_selections_preview", "selections", "select_yesno"),
            ("editor_telop_preview", "telops", "telop_story"),
        ]

    def _make_panels(self, category, entry_id):
        """指定アイテムを選択した状態のパネルを構築する。"""
        tp = TextPanel(0, PANEL_Y, TEXT_PANEL_W, PANEL_H, self._font)
        pp = PreviewPanel(PREVIEW_X, PANEL_Y, PREVIEW_W, PANEL_H, self._font)
        tp.set_data(self._data)
        pp.set_data(self._data)
        tp.on_activate()

        # カーソルを目的のアイテムに移動
        for i, (cat, eid, _) in enumerate(tp._items):
            if cat == category and eid == entry_id:
                tp._cursor = i
                tp._ensure_visible()
                break

        pp.show_preview(category, entry_id)
        return tp, pp

    def _draw_editor(self, category, entry_id):
        """エディタ画面を描画する。"""
        pyxel.cls(0)
        font = self._font

        # ヘッダー
        pyxel.rect(0, 0, SCREEN_W, HEADER_H, 1)
        pyxel.text(4, 2, "Text Editor v1", 7, font)
        help_text = "F5:Compile  F9:Reload  ESC:Quit"
        help_w = font.text_width(help_text) if font else len(help_text) * 4
        pyxel.text(SCREEN_W - help_w - 4, 2, help_text, 5, font)

        # パネル
        tp, pp = self._make_panels(category, entry_id)
        tp.draw()
        pp.draw()

        # ステータスバー
        pyxel.rect(0, STATUS_Y, SCREEN_W, STATUS_H, 1)
        pyxel.text(4, STATUS_Y + 1, "JSON loaded", 11, font)

    def _save(self, name):
        w, h = SCREEN_W, SCREEN_H
        scale = 2
        img = Image.new("RGB", (w * scale, h * scale))
        for py in range(h):
            for px in range(w):
                col = pyxel.pget(px, py)
                r, g, b = PALETTE[col % 16]
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((px * scale + dx, py * scale + dy),
                                     (r, g, b))
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        img.save(path)
        self._saved += 1
        print(f"  [{self._saved}/{len(self._shots)}] {name}.png")

    def update(self):
        if self._index >= len(self._shots):
            return
        if self._phase == 1:
            name = self._shots[self._index][0]
            self._save(name)
            self._index += 1
            self._phase = 0
            if self._index >= len(self._shots):
                print(f"\nDone! {self._saved} screenshots saved.")
                pyxel.quit()

    def draw(self):
        if self._index >= len(self._shots):
            return
        if self._phase == 0:
            name, cat, eid = self._shots[self._index]
            self._draw_editor(cat, eid)
            self._phase = 1


if __name__ == "__main__":
    EditorHarness()
