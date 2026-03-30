import pyxel

_ext_blt_supported = True

class Image:
    """背景など動かさない画像の描画用クラス（フェードイン・フェードアウト対応）。
    
    Attributes:
        x (float): 描画X座標
        y (float): 描画Y座標
        img (int): 画像バンク番号 (0-2) または pyxel.Image
        u (float): 画像切り出し元X座標
        v (float): 画像切り出し元Y座標
        w (float): 画像切り出し幅
        h (float): 画像切り出し高さ
        colkey (int|None): 透過色
        alpha (float): 透明度 (0.0=完全透明 ～ 1.0=完全不透明)。 dither()を用いて疑似的に表現する
    """

    def __init__(self, x=0, y=0, img=0, u=0, v=0, w=0, h=0, colkey=None):
        self.x = x
        self.y = y
        self.img = img
        self.u = u
        self.v = v
        self.w = w
        self.h = h
        self.colkey = colkey
        self.alpha = 1.0

    @classmethod
    def from_file(cls, filename, x=0, y=0, colkey=None):
        """外部PNGファイルからImageを生成する。

        Args:
            filename: assets/images/ 内のファイル名 (例: "title_bg.png")
            x: 描画X座標
            y: 描画Y座標
            colkey: 透過色 (None=透過なし)
        Returns:
            Image instance
        """
        import config
        pyxel_img = config.ASSETS.load_image(filename)
        return cls(x=x, y=y, img=pyxel_img,
                   u=0, v=0, w=pyxel_img.width, h=pyxel_img.height,
                   colkey=colkey)

    def set_fade(self, alpha):
        """透明度を設定し、フェード効果を反映させる。

        Args:
            alpha (float): 0.0 (透明) ～ 1.0 (不透明) の値
        """
        self.alpha = max(0.0, min(1.0, float(alpha)))

    def update(self):
        """状態の更新処理。必要に応じて継承先で実装する。"""
        pass

    def draw(self):
        """画像を画面へ描画する。"""
        if self.alpha <= 0.0:
            return  # 完全に透明なら描画しない

        # pyxel.dither が存在する場合のみ半透明(ディザリング)描画を有効にする (Pyxel 2.x対応用)
        has_dither = hasattr(pyxel, "dither")
        if self.alpha < 1.0 and has_dither:
            pyxel.dither(self.alpha)
        
        try:
            self._blt()
        finally:
            if self.alpha < 1.0 and has_dither:
                pyxel.dither(1.0)
                
    def _blt(self):
        """実際の blt 描画処理"""
        pyxel.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)


class Sprite(Image):
    """移動・拡大縮小・回転などの処理を追加した画像（スプライト）表示用クラス。
    
    Attributes:
        vx (float): X方向の速度
        vy (float): Y方向の速度
        scale (float): 拡大縮小率 (1.0 = 等倍)
        rotate (float): 回転角度 (度数法)
    """

    def __init__(self, x=0, y=0, img=0, u=0, v=0, w=0, h=0, colkey=None):
        super().__init__(x, y, img, u, v, w, h, colkey)
        self.vx = 0.0
        self.vy = 0.0
        self.scale = 1.0
        self.rotate = 0.0
        
    def move(self, dx, dy):
        """現在位置から指定距離分移動する。
        
        Args:
            dx (float): X方向の移動量
            dy (float): Y方向の移動量
        """
        self.x += dx
        self.y += dy

    def update(self):
        """毎フレームの座標更新処理など。"""
        super().update()
        self.x += self.vx
        self.y += self.vy

    def _blt(self):
        """スプライトを描画する。
        （Pyxelが拡大縮小や回転に対応している場合は反映し、非対応なら通常描画する）
        """
        global _ext_blt_supported
        if _ext_blt_supported:
            try:
                pyxel.blt(
                    self.x, self.y, self.img, 
                    self.u, self.v, self.w, self.h, 
                    self.colkey, self.rotate, self.scale
                )
            except (TypeError, ValueError):
                _ext_blt_supported = False
                pyxel.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
        else:
            pyxel.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
