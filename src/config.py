"""ゲーム全体の共通設定。
解像度・フォントなどプロジェクト共通の定数をここで管理する。
"""

import os
import pyxel

# --- パス解決 ---
# src/ から一つ上のプロジェクトルートを基準にする
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# --- 画面設定 ---
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 270

# --- フォント設定 ---
FONT_SIZE = 16
FONT_PATH = os.path.join(_PROJECT_ROOT, "assets", "fonts", "madoufmg.ttf")

# フォントオブジェクト（pyxel.init() 後に init_font() で初期化する）
FONT = None


def init_font():
    """pyxel.init() の後に呼び出してフォントを読み込む。"""
    global FONT
    FONT = pyxel.Font(FONT_PATH, FONT_SIZE)
