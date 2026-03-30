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

# --- データディレクトリ ---
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
COMPILED_DIR = os.path.join(DATA_DIR, "compiled")

# フォントオブジェクト（pyxel.init() 後に init_font() で初期化する）
FONT = None

# アセットマネージャー（init_assets() で初期化する）
ASSETS = None

# テキストマネージャー（init_text_manager() で初期化する）
TEXT_MANAGER = None


def init_font():
    """pyxel.init() の後に呼び出してフォントを読み込む。"""
    global FONT
    FONT = pyxel.Font(FONT_PATH, FONT_SIZE)


def init_assets():
    """pyxel.init() の後に呼び出してアセットマネージャーを初期化する。"""
    global ASSETS
    from core.asset_manager import AssetManager
    ASSETS = AssetManager()


def init_text_manager():
    """コンパイル済みテキストデータを読み込む。"""
    global TEXT_MANAGER
    from data.text_manager import TextManager
    TEXT_MANAGER = TextManager()
    TEXT_MANAGER.load(os.path.join(COMPILED_DIR, "text_all.bin"))
