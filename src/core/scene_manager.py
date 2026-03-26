class SceneManager:
    """シーンの登録・切り替え・実行を管理するクラス。"""

    def __init__(self):
        # シーン名 → シーンクラス の対応辞書
        self._scenes = {}
        # 現在アクティブなシーンのインスタンス
        self._current_scene = None

    def register(self, name, scene_class):
        """シーンを名前付きで登録する。

        Args:
            name: シーンを識別する文字列キー（例: "title", "game"）
            scene_class: Scene を継承したクラス（インスタンスではなくクラスそのもの）
        """
        self._scenes[name] = scene_class

    def change_scene(self, name):
        """アクティブシーンを切り替える。

        登録済みのクラスから新しいインスタンスを生成して差し替える。
        毎回新規生成するので、シーンに入るたびに状態がリセットされる。

        Args:
            name: 切り替え先のシーン名
        """
        if name not in self._scenes:
            raise KeyError(f"Scene '{name}' is not registered.")
        scene_class = self._scenes[name]
        self._current_scene = scene_class(self)

    def update(self):
        """アクティブシーンの update() を呼ぶ。"""
        if self._current_scene:
            self._current_scene.update()

    def draw(self):
        """アクティブシーンの draw() を呼ぶ。"""
        if self._current_scene:
            self._current_scene.draw()