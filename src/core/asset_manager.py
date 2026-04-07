import os

import pyxel

import config

# アセットディレクトリ
IMAGES_DIR = os.path.join(config._PROJECT_ROOT, "assets", "images")
BGM_DIR = os.path.join(config._PROJECT_ROOT, "assets", "audio", "bgm")
SE_DIR = os.path.join(config._PROJECT_ROOT, "assets", "audio", "se")

# 外部ファイル用サウンドスロットの開始番号 (0-31は.pyxres用に予約)
_EXT_SOUND_SLOT_START = 32


class AssetManager:
    """外部アセット（PNG画像・音声ファイル）の読み込みとキャッシュを管理する。

    pyxel.init() の後に生成すること。
    """

    def __init__(self):
        self._images: dict[str, pyxel.Image] = {}
        self._sounds: dict[str, int] = {}
        self._next_sound_slot = _EXT_SOUND_SLOT_START

    def load_image(self, filename, subdir="images"):
        """PNGファイルを読み込み、pyxel.Image としてキャッシュする。

        Args:
            filename: assets/{subdir}/ 内のファイル名 (例: "title_bg.png")
            subdir: assets/ 配下のサブディレクトリ (デフォルト "images")
        Returns:
            pyxel.Image オブジェクト
        """
        if filename in self._images:
            return self._images[filename]

        path = os.path.join(config._PROJECT_ROOT, "assets", subdir, filename)
        img = pyxel.Image.from_image(path)
        self._images[filename] = img
        return img

    def load_sound(self, filename, subdir="se"):
        """WAV/MP3/OGGファイルをサウンドスロットに読み込み、スロット番号を返す。

        Args:
            filename: assets/{subdir}/ 内のファイル名 (例: "click.wav")
            subdir: assets/ 配下のサブディレクトリ (デフォルト "se")
        Returns:
            サウンドスロット番号 (pyxel.play() で使用)
        """
        if filename in self._sounds:
            return self._sounds[filename]

        slot = self._next_sound_slot
        if slot > 63:
            raise RuntimeError("Sound slot overflow: 外部ファイル用スロット(32-63)を使い切りました")

        path = os.path.join(config._PROJECT_ROOT, "assets", subdir, filename)
        pyxel.sounds[slot].pcm(path)
        self._sounds[filename] = slot
        self._next_sound_slot += 1
        return slot

    def get_image(self, filename):
        """読み込み済みの画像を取得する。未読み込みの場合 KeyError。"""
        return self._images[filename]

    def get_sound_slot(self, filename):
        """読み込み済みの音声のスロット番号を取得する。未読み込みの場合 KeyError。"""
        return self._sounds[filename]
