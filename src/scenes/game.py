import pyxel

import config
from scenes.base import Scene
from ui.message_window import MessageWindow, TEXT_SPEED_FAST


class GameScene(Scene):
    """ゲーム画面。メッセージウィンドウの各種テスト表示を行う。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.msg_window = MessageWindow()

        self._demo_started = False

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            if self.msg_window.is_open:
                return
            self.scene_manager.change_scene("title")
            return

        # メッセージウィンドウが開いている場合はそちらの入力を優先
        if self.msg_window.is_open:
            self.msg_window.update()
            return

        # デモ開始
        if pyxel.btnp(pyxel.KEY_RETURN) and not self._demo_started:
            self._demo_started = True
            self.msg_window.set_text_speed(TEXT_SPEED_FAST)
            self.msg_window.show(self._build_test_messages())

    def _build_test_messages(self):
        """各種テストパターンのメッセージリストを構築する。"""
        # テキスト領域幅: 464 - 8*2 = 448px
        # 全角(16px): 1行28文字 / 半角(8px): 1行56文字

        return [
            # --- 1. 基本: 日本語会話 ---
            {
                "text": "こんにちは！\nメッセージウィンドウの\nテストを始めます。",
                "name": "アリス",
            },
            {
                "text": "日本語のテキストが\n正しく表示されるか\n確認しましょう。",
                "name": "ボブ",
            },

            # --- 2. 全角28文字ぴったり（1行の限界） ---
            {
                "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふ\n↑全角28文字ぴったり",
                "name": "テスト2",
            },

            # --- 3. 全角29文字（1文字はみ出し） ---
            {
                "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへ\n↑全角29文字（はみ出す？）",
                "name": "テスト3",
            },

            # --- 4. 全角30文字（2文字はみ出し） ---
            {
                "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ\n↑全角30文字",
                "name": "テスト4",
            },

            # --- 5. 半角56文字ぴったり ---
            {
                "text": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv\n↑半角56文字ぴったり",
                "name": "Test5",
            },

            # --- 6. 半角60文字（はみ出し） ---
            {
                "text": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz\n↑半角60文字（はみ出す？）",
                "name": "Test6",
            },

            # --- 7. 全角日本語3行びっしり ---
            {
                "text": "１行目：全角で長めのテキストを書く\n２行目：このぐらいの文章量が\n３行目：実際のゲームで使われる",
                "name": "テスト7",
            },

            # --- 8. 日英混在テスト ---
            {
                "text": "HPが100回復した！\nLv.5にアップ！ATK+3\nスキル「炎の剣」を習得！",
                "name": "システム",
            },

            # --- 9. 1行だけ ---
            {
                "text": "1行だけのメッセージ。",
                "name": "テスト9",
            },

            # --- 10. 名前なし日本語 ---
            "名前ウィンドウなしの\n日本語メッセージです。",

            # --- 11. 長い名前テスト ---
            {
                "text": "長い名前が正しく\n表示されるかテスト。",
                "name": "名前が長いキャラクター",
            },

            # --- 12. 自動送りテスト ---
            {
                "text": "このメッセージは\n自動で送られます。",
                "name": "自動送り",
                "auto": True,
            },

            # --- 13. 完了メッセージ ---
            "テスト完了！\nESCでタイトルに戻ります。",
        ]

    def draw(self):
        pyxel.cls(0)
        font = config.FONT

        pyxel.text(180, 40, "DEMO SCENE", 7, font)

        if not self._demo_started:
            pyxel.text(120, 80, "ENTERキーでデモ開始", 5, font)
            # テスト内容の説明
            pyxel.text(40, 110, "テスト項目:", 10, font)
            pyxel.text(40, 130, "- 日本語会話 / 日英混在", 13, font)
            pyxel.text(40, 150, "- 全角28,29,30文字(はみ出し確認)", 13, font)
            pyxel.text(40, 170, "- 半角56,60文字(はみ出し確認)", 13, font)
            pyxel.text(40, 190, "- 名前ウィンドウ / 自動送り", 13, font)
        elif not self.msg_window.is_open:
            pyxel.text(150, 100, "デモ完了！", 11, font)

        pyxel.text(130, 240, "ESC: タイトルに戻る", 5, font)

        # メッセージウィンドウは最前面に描画
        self.msg_window.draw()
