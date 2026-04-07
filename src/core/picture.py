"""ピクチャ管理クラス。

EventInterpreter から利用される、番号付きスロットで管理される画像オブジェクト。
RPGツクールの「ピクチャ」と同じ概念で、背景・スプライトを統一的に扱う。
"""

from core.graphics import Image


class Picture:
    """ピクチャ番号で管理される画像。

    Attributes:
        no: ピクチャ番号（描画順序: 小→大 = 奥→手前）
        x: 表示X座標
        y: 表示Y座標
        opacity: 不透明度（0〜100）
        colkey: 透過色（None=透過なし）
    """

    def __init__(self, no, image, x=0, y=0, opacity=100, colkey=None):
        self.no = no
        self.image = image
        self.x = float(x)
        self.y = float(y)
        self.opacity = float(opacity)
        self.colkey = colkey

        # アニメーション
        self._anim_start_x = 0.0
        self._anim_start_y = 0.0
        self._anim_start_opacity = 0.0
        self._anim_target_x = None
        self._anim_target_y = None
        self._anim_target_opacity = None
        self._anim_duration = 0
        self._anim_elapsed = 0

    @classmethod
    def from_file(cls, no, filename, x=0, y=0, opacity=100, colkey=None):
        """外部PNGファイルからPictureを生成する。"""
        image = Image.from_file(filename, x=x, y=y, colkey=colkey)
        return cls(no, image, x=x, y=y, opacity=opacity, colkey=colkey)

    def move_to(self, x=None, y=None, opacity=None, duration=30):
        """指定した値へアニメーション移動を開始する。

        Args:
            x: 移動先X座標（None=変更しない）
            y: 移動先Y座標（None=変更しない）
            opacity: 変更後の不透明度（None=変更しない）
            duration: アニメーション時間（フレーム数、1以上）
        """
        self._anim_start_x = self.x
        self._anim_start_y = self.y
        self._anim_start_opacity = self.opacity
        self._anim_target_x = float(x) if x is not None else None
        self._anim_target_y = float(y) if y is not None else None
        self._anim_target_opacity = float(opacity) if opacity is not None else None
        self._anim_duration = max(1, duration)
        self._anim_elapsed = 0

    @property
    def is_animating(self):
        """アニメーション中か。"""
        return self._anim_duration > 0 and self._anim_elapsed < self._anim_duration

    def update(self):
        """アニメーションを1フレーム進める。"""
        if not self.is_animating:
            return

        self._anim_elapsed += 1
        t = min(1.0, self._anim_elapsed / self._anim_duration)

        if self._anim_target_x is not None:
            self.x = self._anim_start_x + (self._anim_target_x - self._anim_start_x) * t
        if self._anim_target_y is not None:
            self.y = self._anim_start_y + (self._anim_target_y - self._anim_start_y) * t
        if self._anim_target_opacity is not None:
            self.opacity = self._anim_start_opacity + (self._anim_target_opacity - self._anim_start_opacity) * t

    def draw(self):
        """描画する。"""
        if self.opacity <= 0:
            return
        self.image.x = self.x
        self.image.y = self.y
        self.image.colkey = self.colkey
        self.image.set_fade(self.opacity / 100.0)
        self.image.draw()
