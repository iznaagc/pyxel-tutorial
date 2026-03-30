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


class FadeOverlay(Image):
    """画面のフェードイン・フェードアウトを行うオーバーレイ。
    Imageを継承し、指定色の矩形として画面全体を覆う。
    
    Attributes:
        color (int): 0(黒) または 7(白)などフェードに使用する色
        speed (float): 1フレームあたりの透明度変化量
        fade_state (int): 0: 待機, 1: フェードイン(暗→明), 2: フェードアウト(明→暗)
    """
    
    FADE_IN = 1
    FADE_OUT = 2
    
    def __init__(self, color=0, speed=0.02):
        import config
        sw = getattr(config, "SCREEN_WIDTH", 480)
        sh = getattr(config, "SCREEN_HEIGHT", 270)
        # 背景画像等に隠して待機できるよう、1x1サイズで初期化 (描画負荷低減)
        super().__init__(0, 0, 0, 0, 0, 1, 1, None)
        self.color = color
        self.speed = speed
        self.fade_state = 0
        self.alpha = 0.0
        self._target_w = sw
        self._target_h = sh

    def fade_in(self, speed=None):
        """フェードイン（暗/白→透明）を開始する"""
        if speed is not None:
            self.speed = speed
        self.w = self._target_w
        self.h = self._target_h
        self.alpha = 1.0
        self.fade_state = self.FADE_IN

    def fade_out(self, speed=None, color=None):
        """フェードアウト（透明→暗/白）を開始する"""
        if speed is not None:
            self.speed = speed
        if color is not None:
            self.color = color
        self.w = self._target_w
        self.h = self._target_h
        self.alpha = 0.0
        self.fade_state = self.FADE_OUT

    def update(self):
        super().update()
        if self.fade_state == self.FADE_IN:
            self.alpha -= self.speed
            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.fade_state = 0
                self.w = 1  # 負荷軽減のため1x1に戻す
                self.h = 1
        elif self.fade_state == self.FADE_OUT:
            self.alpha += self.speed
            if self.alpha >= 1.0:
                self.alpha = 1.0
                self.fade_state = 0

    def is_fading(self):
        """フェード中かどうかを返す"""
        return self.fade_state != 0

    def is_fade_out_completed(self):
        """フェードアウトが完全に終了して画面が隠れているか"""
        return self.fade_state == 0 and self.alpha >= 1.0

    def _blt(self):
        """オーバーライド: bltの代わりにrect(矩形塗りつぶし)で画面を覆う"""
        pyxel.rect(self.x, self.y, self.w, self.h, self.color)
