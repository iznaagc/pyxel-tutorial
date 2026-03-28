import pyxel

import config
from scenes.base import Scene
from ui.message_window import MessageWindow, TEXT_SPEED_FAST
from ui.select_window import SelectWindow
from ui.telop_window import TelopWindow


# デモの進行状態
STATE_MENU = 0           # デモメニュー表示中
STATE_MSG_DEMO = 1       # メッセージウィンドウデモ中
STATE_SELECT_DEMO = 2    # 選択肢ウィンドウデモ中
STATE_ACTIVE_DEMO = 3    # アクティブ/非アクティブデモ中
STATE_TELOP_DEMO = 4     # テロップデモ中

# デモメニューの選択肢
DEMO_MENU_ITEMS = [
    "メッセージ：基本（日本語会話）",
    "メッセージ：文字数テスト",
    "メッセージ：日英混在/名前/自動送り",
    "選択肢：はい/いいえ",
    "選択肢：3択メニュー",
    "選択肢：長いテキスト（自動リサイズ）",
    "選択肢：多数選択肢（長押しリピート）",
    "選択肢：半透明ウィンドウ",
    "ウィンドウ：アクティブ/非アクティブ",
    "テロップ：ストーリー風",
    "テロップ：スタッフロール風",
    "タイトルに戻る",
]

# メニューの表示上限
DEMO_MENU_MAX_VISIBLE = 8


class GameScene(Scene):
    """ゲーム画面。メッセージウィンドウ・選択肢ウィンドウの各種テストを個別に実行できる。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.msg_window = MessageWindow()

        # デモメニュー（画面左側に配置、ESCで戻る）
        self._demo_menu = SelectWindow(
            x=16, y=36,
            items=DEMO_MENU_ITEMS,
            cancel_index=len(DEMO_MENU_ITEMS) - 1,
            page_size=DEMO_MENU_MAX_VISIBLE,
        )

        self._state = STATE_MENU
        self._select_window = None    # テスト用の選択肢ウィンドウ
        self._select_result_text = "" # 選択結果の表示テキスト
        self._telop = None            # テロップウィンドウ

        # デモメニューを開いた状態で開始
        self._demo_menu.open()
        self._demo_menu.activate()

    def _open_demo_menu(self):
        """デモメニューを開いてメニュー状態に戻る。"""
        self._state = STATE_MENU
        self._select_window = None
        self._select_result_text = ""
        self._telop = None
        self._demo_menu.open(initial_cursor=self._demo_menu.cursor)
        self._demo_menu.activate()

    def _activate_window(self, window):
        """指定ウィンドウをアクティブにし、他を非アクティブにする。"""
        self._demo_menu.deactivate()
        self.msg_window.deactivate()
        if self._select_window:
            self._select_window.deactivate()
        window.activate()

    def update(self):
        # Qキー: いつでもタイトルに戻る
        if pyxel.btnp(pyxel.KEY_Q):
            self.scene_manager.change_scene("title")
            return

        # BSキー: デモ中ならメニューに戻る
        if self._state != STATE_MENU and pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.msg_window.close()
            if self._select_window:
                self._select_window.close()
            if self._telop:
                self._telop.skip()
            self._open_demo_menu()
            return

        # --- メニュー表示中 ---
        if self._state == STATE_MENU:
            result = self._demo_menu.update()
            if result is not None:
                self._on_menu_selected(result)
            return

        # --- メッセージデモ中 ---
        if self._state == STATE_MSG_DEMO:
            if self.msg_window.is_open:
                self.msg_window.update()
            else:
                self._open_demo_menu()
            return

        # --- 選択肢デモ中 ---
        if self._state == STATE_SELECT_DEMO:
            if self._select_window and self._select_window.is_open:
                result = self._select_window.update()
                if result is not None:
                    items = self._select_window._items
                    self._select_result_text = (
                        f"選択結果: {items[result]}({result})"
                    )
                    # 結果をメッセージで表示してからメニューへ
                    self.msg_window.set_text_speed(TEXT_SPEED_FAST)
                    self.msg_window.show([self._select_result_text])
                    self._activate_window(self.msg_window)
            elif self.msg_window.is_open:
                self.msg_window.update()
            else:
                self._open_demo_menu()
            return

        # --- アクティブ/非アクティブデモ中 ---
        if self._state == STATE_ACTIVE_DEMO:
            # TABキーでアクティブウィンドウを切り替え
            if pyxel.btnp(pyxel.KEY_TAB):
                if self._select_window and self.msg_window.is_open:
                    if self._select_window.is_active:
                        self._activate_window(self.msg_window)
                    else:
                        self._activate_window(self._select_window)

            # アクティブなウィンドウのみ更新
            if self._select_window and self._select_window.is_active:
                result = self._select_window.update()
                if result is not None:
                    items = self._select_window._items
                    self.msg_window.set_text_speed(TEXT_SPEED_FAST)
                    self.msg_window.show([f"選択結果: {items[result]}({result})"])
                    self._activate_window(self.msg_window)
            elif self.msg_window.is_active and self.msg_window.is_open:
                self.msg_window.update()
                if not self.msg_window.is_open:
                    self._open_demo_menu()
            return

        # --- テロップデモ中 ---
        if self._state == STATE_TELOP_DEMO:
            if self._telop and self._telop.is_open:
                # Enter/Spaceでスキップ
                if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
                    self._telop.skip()
                    self._open_demo_menu()
                    return
                self._telop.update()
                if self._telop.is_complete:
                    self._open_demo_menu()
            else:
                self._open_demo_menu()
            return

    def _on_menu_selected(self, index):
        """デモメニューの選択に応じてデモを開始する。"""
        # 最後の項目 = タイトルに戻る
        if index == len(DEMO_MENU_ITEMS) - 1:
            self.scene_manager.change_scene("title")
            return

        # メッセージ系デモ (0-2)
        if index <= 2:
            self._state = STATE_MSG_DEMO
            self.msg_window.set_text_speed(TEXT_SPEED_FAST)
            messages = [
                self._msg_basic,
                self._msg_charcount,
                self._msg_mixed,
            ][index]()
            self.msg_window.show(messages)
            self._activate_window(self.msg_window)
            return

        # 選択肢系デモ (3-7)
        if index <= 7:
            self._state = STATE_SELECT_DEMO
            pattern = self._get_select_patterns()[index - 3]
            self._select_window = SelectWindow(
                x=pattern["x"], y=pattern["y"],
                items=pattern["items"],
                cancel_index=pattern.get("cancel_index", -1),
                semi_transparent=pattern.get("semi_transparent", False),
            )
            self._select_window.open()
            self._activate_window(self._select_window)
            # 説明メッセージを同時表示（非アクティブで表示のみ）
            if "desc" in pattern:
                self.msg_window.set_text_speed(TEXT_SPEED_FAST)
                self.msg_window.show([pattern["desc"]])
            return

        # アクティブ/非アクティブデモ (8)
        if index == 8:
            self._start_active_demo()
            return

        # テロップデモ (9-10)
        if index == 9:
            self._start_telop_story()
            return
        if index == 10:
            self._start_telop_credits()
            return

    def _start_active_demo(self):
        """アクティブ/非アクティブ切り替えデモを開始する。"""
        self._state = STATE_ACTIVE_DEMO

        # 選択肢ウィンドウ（初期アクティブ）
        self._select_window = SelectWindow(
            x=200, y=60,
            items=["はい", "いいえ"],
            cancel_index=1,
        )
        self._select_window.open()

        # メッセージウィンドウ（非アクティブで表示のみ）
        self.msg_window.set_text_speed(TEXT_SPEED_FAST)
        self.msg_window.show([{
            "text": "TABキーでアクティブを\n切り替えられます。\n白枠=アクティブ 灰枠=非アクティブ",
            "name": "説明",
        }])
        # メッセージを即時全表示
        self.msg_window._char_index = self.msg_window._total_chars
        self.msg_window._display_complete = True

        self._activate_window(self._select_window)

    def _start_telop_story(self):
        """ストーリー風テロップデモを開始する。"""
        self._state = STATE_TELOP_DEMO
        self._telop = TelopWindow(scroll_speed=0.8, text_color=7)
        self._telop.show([
            "",
            "遥かなる時の彼方──",
            "",
            "世界は光と闇の狭間で",
            "均衡を保っていた。",
            "",
            "しかしある日、",
            "封印されし古の魔王が",
            "目覚めの時を迎える。",
            "",
            "大地は裂け、空は紅に染まり",
            "人々は絶望の淵に立たされた。",
            "",
            "残された希望は、",
            "伝説の勇者の末裔──",
            "たった一人の少年だけだった。",
            "",
            "",
            "第一章「旅立ちの朝」",
            "",
        ])

    def _start_telop_credits(self):
        """スタッフロール風テロップデモを開始する。"""
        self._state = STATE_TELOP_DEMO
        self._telop = TelopWindow(scroll_speed=1.0, text_color=7)
        self._telop.show([
            "",
            "- STAFF -",
            "",
            "",
            "Director",
            "テスト太郎",
            "",
            "",
            "Programming",
            "テストプログラマーA",
            "テストプログラマーB",
            "",
            "",
            "Graphics",
            "テストアーティストA",
            "",
            "",
            "Music & Sound",
            "テストコンポーザー",
            "",
            "",
            "Special Thanks",
            "Pyxel Engine",
            "すべてのプレイヤー",
            "",
            "",
            "",
            "Thank you for playing!",
            "",
            "",
        ])

    # =================================================================
    # メッセージテストパターン
    # =================================================================

    def _msg_basic(self):
        """基本: 日本語会話テスト。"""
        return [
            {
                "text": "こんにちは！\nメッセージウィンドウの\nテストを始めます。",
                "name": "アリス",
            },
            {
                "text": "日本語のテキストが\n正しく表示されるか\n確認しましょう。",
                "name": "ボブ",
            },
            {
                "text": "1行だけのメッセージ。",
                "name": "テスト",
            },
            "名前ウィンドウなしの\n日本語メッセージです。",
            {
                "text": "長い名前が正しく\n表示されるかテスト。",
                "name": "名前が長いキャラクター",
            },
        ]

    def _msg_charcount(self):
        """文字数テスト: はみ出し確認。"""
        return [
            {
                "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふ\n↑全角28文字ぴったり",
                "name": "全角28文字",
            },
            {
                "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへ\n↑全角29文字（はみ出す？）",
                "name": "全角29文字",
            },
            {
                "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ\n↑全角30文字",
                "name": "全角30文字",
            },
            {
                "text": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv\n↑半角56文字ぴったり",
                "name": "半角56文字",
            },
            {
                "text": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz\n↑半角60文字（はみ出す？）",
                "name": "半角60文字",
            },
            {
                "text": "１行目：全角で長めのテキストを書く\n２行目：このぐらいの文章量が\n３行目：実際のゲームで使われる",
                "name": "3行びっしり",
            },
        ]

    def _msg_mixed(self):
        """日英混在・名前・自動送りテスト。"""
        return [
            {
                "text": "HPが100回復した！\nLv.5にアップ！ATK+3\nスキル「炎の剣」を習得！",
                "name": "システム",
            },
            {
                "text": "This is English text.\nWith Japanese: 混在テスト\nHP: 999 / MP: 50",
                "name": "Mixed",
            },
            {
                "text": "このメッセージは\n自動で送られます。",
                "name": "自動送り",
                "auto": True,
            },
            {
                "text": "自動送り2つ目。\n連続で自動送りが\n動作するか確認。",
                "auto": True,
            },
            "テスト完了！",
        ]

    # =================================================================
    # 選択肢テストパターン
    # =================================================================

    def _get_select_patterns(self):
        """選択肢ウィンドウのテストパターンを返す。"""
        return [
            # 0: はい/いいえ
            {
                "x": 200, "y": 60,
                "items": ["はい", "いいえ"],
                "cancel_index": 1,
                "desc": {
                    "text": "基本の「はい/いいえ」選択。\nESCキーで「いいえ」が\n選ばれます。",
                    "name": "はい/いいえ",
                },
            },
            # 1: 3択メニュー
            {
                "x": 180, "y": 50,
                "items": ["攻撃", "魔法", "逃げる"],
                "cancel_index": 2,
                "desc": {
                    "text": "3つの選択肢。\nカーソル上下でループ確認。\nESCで「逃げる」。",
                    "name": "3択メニュー",
                },
            },
            # 2: 長いテキスト
            {
                "x": 80, "y": 50,
                "items": [
                    "ポーションを使う",
                    "エリクサーを使う",
                    "ハイポーションを使う",
                    "やめる",
                ],
                "cancel_index": 3,
                "desc": {
                    "text": "長い日本語テキスト。\n自動リサイズで幅が\n合っているか確認。",
                    "name": "自動リサイズ",
                },
            },
            # 3: 多数の選択肢
            {
                "x": 160, "y": 20,
                "items": [
                    "アイテム1",
                    "アイテム2",
                    "アイテム3",
                    "アイテム4",
                    "アイテム5",
                    "アイテム6",
                    "アイテム7",
                    "キャンセル",
                ],
                "cancel_index": 7,
                "desc": {
                    "text": "8個の選択肢。\n長押しでカーソルが\n加速するか確認。",
                    "name": "長押しリピート",
                },
            },
            # 4: 半透明
            {
                "x": 160, "y": 60,
                "items": ["セーブする", "ロードする", "戻る"],
                "cancel_index": 2,
                "semi_transparent": True,
                "desc": {
                    "text": "半透明ウィンドウの\n選択肢表示テスト。",
                    "name": "半透明",
                },
            },
        ]

    # =================================================================
    # 描画
    # =================================================================

    def draw(self):
        pyxel.cls(0)
        font = config.FONT

        # テロップデモ中は全画面テロップのみ描画
        if self._state == STATE_TELOP_DEMO:
            if self._telop:
                self._telop.draw()
            pyxel.text(120, 254, "Enter: スキップ  BS: メニューへ  Q: タイトルへ", 5, font)
            return

        pyxel.text(180, 10, "DEMO SCENE", 7, font)

        # 状態に応じたヒント表示
        if self._state == STATE_MENU:
            pyxel.text(300, 254, "Q: タイトルへ", 5, font)
        elif self._state == STATE_ACTIVE_DEMO:
            pyxel.text(120, 254, "TAB: 切替  BS: メニューへ  Q: タイトルへ", 5, font)
        else:
            pyxel.text(200, 254, "BS: メニューへ  Q: タイトルへ", 5, font)

        # デモメニュー
        if self._state == STATE_MENU:
            self._demo_menu.draw()

        # テスト用選択肢ウィンドウ
        if self._select_window:
            self._select_window.draw()

        # メッセージウィンドウは最前面
        self.msg_window.draw()
