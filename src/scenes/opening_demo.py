"""オープニングデモシーン（イベント駆動版）。

EventInterpreter を使って、JSONで定義されたイベントコマンドを実行する。
data/text/demo.json の "ev_opening_demo" イベントを再生する。
"""

import pyxel

import config
from scenes.base import Scene
from core.event_interpreter import EventInterpreter
from core.audio import Audio


class OpeningDemoScene(Scene):
    """イベント駆動のオープニングデモシーン。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self._event = EventInterpreter(scene_manager)

        event_data = config.TEXT_MANAGER.get_event("ev_opening_demo")
        self._event.start(event_data)

    def update(self):
        # Qキー: いつでもタイトルに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            Audio.stop_all()
            self.scene_manager.change_scene("title")
            return

        self._event.update()

        # イベント完了時（change_scene で終了しなかった場合のフォールバック）
        if not self._event.is_running:
            self.scene_manager.change_scene("title")

    def draw(self):
        pyxel.cls(0)
        self._event.draw()

        # デバッグ情報
        font = config.FONT
        pyxel.text(8, 254, "Q: タイトルへ", 5, font)
