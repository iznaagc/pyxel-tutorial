class Scene:
    """全シーンの基底クラス。
    各シーンはこのクラスを継承し、update() と draw() をオーバーライドする。
    """

    def __init__(self, scene_manager):
        # シーンマネージャーへの参照を保持する。
        # シーン内から self.scene_manager.change_scene("name") で遷移できる。
        self.scene_manager = scene_manager

    def update(self):
        """毎フレーム呼ばれる。入力処理・ゲームロジックを書く。"""
        pass

    def draw(self):
        """毎フレーム呼ばれる。描画処理を書く。"""
        pass