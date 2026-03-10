import pyxel
from src.constants import SCENE_TITLE, LEVELS

class ClearScene:
    """クリア画面の管理クラス"""
    def __init__(self, app):
        self.app = app
        self.played_clear_sound = False # クリア音を鳴らしたかフラグ
        self.all_clear = False          # 全ステージクリアしたかフラグ

    def on_enter(self):
        """シーン切り替え時に呼ばれる初期化処理"""
        self.played_clear_sound = False
        # 現在のレベルが最後のレベルかどうかを確認
        self.all_clear = (self.app.current_level >= len(LEVELS) - 1)

    def update(self):
        """クリア画面の更新処理"""
        # まだ鳴らしていなければクリア音を1回だけ再生
        if not self.played_clear_sound:
            pyxel.play(0, 2)
            self.played_clear_sound = True
            
        # Enterキーが押されたら次へ
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.all_clear:
                # 全てクリアしていたらタイトルへ戻る（レベルを0にリセット）
                self.app.current_level = 0
                self.app.scene = SCENE_TITLE
            else:
                # まだ次があるなら、次のレベルへ進む
                self.app.next_level()

    def draw(self):
        """クリア画面の描画処理"""
        # ※Appクラス側で背面に現在のプレイ画面を描画した上で、その上に重ねて描画します。
        
        # 背景のメッセージボックス（黒塗りつぶし＋枠線）
        pyxel.rect(20, 35, 120, 30, 0)
        pyxel.rectb(20, 35, 120, 30, 10)
        
        if self.all_clear:
            # 全ステージクリアのメッセージ
            pyxel.text(40, 40, "ALL STAGES CLEAR!", 10)
            if pyxel.frame_count % 30 < 15:
                pyxel.text(45, 55, "PRESS ENTER TO END", 7)
        else:
            # 個別ステージクリアのメッセージ
            pyxel.text(50, 40, "STAGE CLEAR!", 10)
            if pyxel.frame_count % 30 < 15:
                pyxel.text(45, 55, "PRESS ENTER FOR NEXT", 7)
