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

# メニューの表示上限
DEMO_MENU_MAX_VISIBLE = 8


class GameScene(Scene):
    """ゲーム画面。メッセージウィンドウ・選択肢ウィンドウの各種テストを個別に実行できる。"""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.msg_window = MessageWindow()

        # デモメニュー（画面左側に配置、ESCで戻る）
        menu = config.TEXT_MANAGER.get_selection("demo_menu")
        self._demo_menu_items = menu["items"]
        self._demo_menu = SelectWindow(
            x=16, y=36,
            items=self._demo_menu_items,
            cancel_index=menu["cancel_index"],
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
        if index == len(self._demo_menu_items) - 1:
            self.scene_manager.change_scene("title")
            return

        # メッセージ系デモ (0-2)
        if index <= 2:
            self._state = STATE_MSG_DEMO
            self.msg_window.set_text_speed(TEXT_SPEED_FAST)
            msg_ids = ["msg_basic", "msg_charcount", "msg_mixed"]
            messages = config.TEXT_MANAGER.get_messages(msg_ids[index])
            self.msg_window.show(messages)
            self._activate_window(self.msg_window)
            return

        # 選択肢系デモ (3-7)
        if index <= 7:
            self._state = STATE_SELECT_DEMO
            sel_ids = ["select_yesno", "select_3", "select_long",
                       "select_many", "select_semi"]
            sel = config.TEXT_MANAGER.get_selection(sel_ids[index - 3])
            layout = self._get_select_layouts()[index - 3]
            self._select_window = SelectWindow(
                x=layout["x"], y=layout["y"],
                items=sel["items"],
                cancel_index=sel.get("cancel_index", -1),
                semi_transparent=sel.get("semi_transparent", False),
            )
            self._select_window.open()
            self._activate_window(self._select_window)
            # 説明メッセージを同時表示（非アクティブで表示のみ）
            if "desc" in sel:
                self.msg_window.set_text_speed(TEXT_SPEED_FAST)
                self.msg_window.show([sel["desc"]])
            return

        # アクティブ/非アクティブデモ (8)
        if index == 8:
            self._start_active_demo()
            return

        # テロップデモ (9-10)
        if index == 9:
            self._start_telop("telop_story")
            return
        if index == 10:
            self._start_telop("telop_credits")
            return

    def _start_active_demo(self):
        """アクティブ/非アクティブ切り替えデモを開始する。"""
        self._state = STATE_ACTIVE_DEMO

        # 選択肢ウィンドウ（初期アクティブ）
        sel = config.TEXT_MANAGER.get_selection("select_active_demo")
        self._select_window = SelectWindow(
            x=200, y=60,
            items=sel["items"],
            cancel_index=sel["cancel_index"],
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

    def _start_telop(self, telop_id):
        """テロップデモを開始する。"""
        self._state = STATE_TELOP_DEMO
        telop = config.TEXT_MANAGER.get_telop(telop_id)
        self._telop = TelopWindow(
            scroll_speed=telop.get("scroll_speed", 1.0),
            text_color=7,
        )
        self._telop.show(telop["lines"])

    # =================================================================
    # 選択肢レイアウト（座標はコード側に残す）
    # =================================================================

    def _get_select_layouts(self):
        """選択肢ウィンドウの座標レイアウトを返す。"""
        return [
            {"x": 200, "y": 60},   # select_yesno
            {"x": 180, "y": 50},   # select_3
            {"x": 80,  "y": 50},   # select_long
            {"x": 160, "y": 20},   # select_many
            {"x": 160, "y": 60},   # select_semi
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
