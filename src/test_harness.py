"""スクリーンショット撮影用ハーネス。
UIコンポーネントを直接操作して各状態のスクリーンショットを保存する。
"""

import os
import pyxel
from PIL import Image

import config
from ui.message_window import MessageWindow
from ui.select_window import SelectWindow
from ui.telop_window import TelopWindow

SCREENSHOT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "screenshots"
)

PALETTE = [
    (0, 0, 0), (43, 51, 95), (126, 32, 114), (25, 149, 156),
    (139, 72, 82), (57, 92, 152), (169, 193, 255), (238, 238, 238),
    (212, 24, 108), (211, 132, 65), (233, 195, 91), (112, 198, 169),
    (118, 150, 222), (163, 163, 163), (255, 151, 152), (237, 199, 176),
]


class ScreenshotHarness:
    def __init__(self):
        pyxel.init(config.SCREEN_WIDTH, config.SCREEN_HEIGHT,
                   title="Screenshot Harness", display_scale=2)
        config.init_font()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        self._shots = self._define_shots()
        self._index = 0
        self._phase = 0  # 0=draw, 1=capture
        self._saved_count = 0

        print(f"\nScreenshot Harness: {len(self._shots)} shots")
        print(f"Output: {SCREENSHOT_DIR}\n")

        pyxel.run(self.update, self.draw)

    def _define_shots(self):
        return [
            ("demo_menu", self._draw_demo_menu),
            ("demo_menu_page2", self._draw_demo_menu_page2),
            ("msg_japanese_basic", self._draw_msg_basic),
            ("msg_japanese_name_long", self._draw_msg_name_long),
            ("msg_charcount_28", self._draw_msg_28),
            ("msg_charcount_29_overflow", self._draw_msg_29),
            ("msg_mixed_japanese_english", self._draw_msg_mixed),
            ("msg_no_name", self._draw_msg_no_name),
            ("select_yes_no", self._draw_select_yesno),
            ("select_3choices", self._draw_select_3),
            ("select_long_text_autoresize", self._draw_select_long),
            ("select_many_items", self._draw_select_many),
            ("select_semi_transparent", self._draw_select_semi),
            ("active_select_with_inactive_msg", self._draw_active_select),
            ("active_msg_with_inactive_select", self._draw_active_msg),
            ("telop_story", self._draw_telop_story),
            ("telop_credits", self._draw_telop_credits),
        ]

    def _save_current(self, name):
        """現在の画面バッファをPNGに保存。"""
        w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        scale = 2
        img = Image.new("RGB", (w * scale, h * scale))
        for py in range(h):
            for px in range(w):
                col = pyxel.pget(px, py)
                r, g, b = PALETTE[col % 16]
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((px * scale + dx, py * scale + dy),
                                     (r, g, b))
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        img.save(path)
        print(f"  [{self._saved_count+1}/{len(self._shots)}] {name}.png")
        self._saved_count += 1

    def update(self):
        if self._index >= len(self._shots):
            return
        # phase 1: 前フレームのdraw結果をキャプチャ
        if self._phase == 1:
            name = self._shots[self._index][0]
            self._save_current(name)
            self._index += 1
            self._phase = 0
            if self._index >= len(self._shots):
                print(f"\nDone! {self._saved_count} screenshots saved.")
                pyxel.quit()

    def draw(self):
        if self._index >= len(self._shots):
            return
        if self._phase == 0:
            # 描画実行
            _, draw_func = self._shots[self._index]
            draw_func()
            self._phase = 1  # 次のupdateでキャプチャ

    # =====================================================
    # 描画関数
    # =====================================================

    def _header(self):
        font = config.FONT
        pyxel.text(180, 10, "DEMO SCENE", 7, font)
        pyxel.text(340, 254, "ESC: 戻る", 5, font)

    def _make_msg(self, messages, active=True):
        """MessageWindowを構築してテキスト全表示状態にする。"""
        mw = MessageWindow()
        mw.show(messages)
        mw._char_index = mw._total_chars
        mw._display_complete = True
        if active:
            mw.activate()
        return mw

    # --- デモメニュー ---
    def _demo_menu_items(self):
        return [
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

    def _draw_demo_menu(self):
        pyxel.cls(0)
        self._header()
        sw = SelectWindow(
            x=16, y=36,
            items=self._demo_menu_items(),
            cancel_index=11,
            page_size=8,
        )
        sw.open()
        sw.activate()
        sw.draw()

    def _draw_demo_menu_page2(self):
        """デモメニューの2ページ目。"""
        pyxel.cls(0)
        self._header()
        sw = SelectWindow(
            x=16, y=36,
            items=self._demo_menu_items(),
            cancel_index=11,
            page_size=8,
        )
        # カーソルを9番目（タイトルに戻る）にしてページ2を表示
        sw.open(initial_cursor=9)
        sw.activate()
        sw.draw()

    # --- メッセージ系 ---
    def _draw_msg_basic(self):
        pyxel.cls(0)
        self._header()
        mw = self._make_msg([{
            "text": "こんにちは！\nメッセージウィンドウの\nテストを始めます。",
            "name": "アリス",
        }])
        mw.draw()

    def _draw_msg_name_long(self):
        pyxel.cls(0)
        self._header()
        mw = self._make_msg([{
            "text": "長い名前が正しく\n表示されるかテスト。",
            "name": "名前が長いキャラクター",
        }])
        mw.draw()

    def _draw_msg_28(self):
        pyxel.cls(0)
        self._header()
        mw = self._make_msg([{
            "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふ\n↑全角28文字ぴったり",
            "name": "全角28文字",
        }])
        mw.draw()

    def _draw_msg_29(self):
        pyxel.cls(0)
        self._header()
        mw = self._make_msg([{
            "text": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへ\n↑全角29文字（はみ出す？）",
            "name": "全角29文字",
        }])
        mw.draw()

    def _draw_msg_mixed(self):
        pyxel.cls(0)
        self._header()
        mw = self._make_msg([{
            "text": "HPが100回復した！\nLv.5にアップ！ATK+3\nスキル「炎の剣」を習得！",
            "name": "システム",
        }])
        mw.draw()

    def _draw_msg_no_name(self):
        pyxel.cls(0)
        self._header()
        mw = self._make_msg(["名前ウィンドウなしの\n日本語メッセージです。"])
        mw.draw()

    # --- 選択肢系 ---
    def _draw_select_yesno(self):
        pyxel.cls(0)
        self._header()
        sw = SelectWindow(x=200, y=60, items=["はい", "いいえ"], cancel_index=1)
        sw.open()
        sw.activate()
        sw.draw()

    def _draw_select_3(self):
        pyxel.cls(0)
        self._header()
        sw = SelectWindow(x=180, y=50, items=["攻撃", "魔法", "逃げる"], cancel_index=2)
        sw.open()
        sw.activate()
        sw.draw()

    def _draw_select_long(self):
        pyxel.cls(0)
        self._header()
        sw = SelectWindow(
            x=80, y=50,
            items=["ポーションを使う", "エリクサーを使う", "ハイポーションを使う", "やめる"],
            cancel_index=3,
        )
        sw.open()
        sw.activate()
        sw.draw()

    def _draw_select_many(self):
        pyxel.cls(0)
        self._header()
        sw = SelectWindow(
            x=160, y=20,
            items=["アイテム1", "アイテム2", "アイテム3", "アイテム4",
                   "アイテム5", "アイテム6", "アイテム7", "キャンセル"],
            cancel_index=7,
        )
        sw.open()
        sw.activate()
        sw.draw()

    def _draw_select_semi(self):
        pyxel.cls(0)
        self._header()
        font = config.FONT
        for i in range(8):
            pyxel.text(20, 40 + i * 20, f"背景テキスト行{i+1} - 半透明確認用", 5, font)
        sw = SelectWindow(
            x=160, y=60,
            items=["セーブする", "ロードする", "戻る"],
            cancel_index=2,
            semi_transparent=True,
        )
        sw.open()
        sw.activate()
        sw.draw()

    # --- アクティブ/非アクティブ同時表示 ---
    def _draw_active_select(self):
        """選択肢ウィンドウがアクティブ、メッセージウィンドウが非アクティブ。"""
        pyxel.cls(0)
        self._header()
        font = config.FONT
        pyxel.text(16, 30, "選択肢=アクティブ(白枠)", 7, font)
        pyxel.text(16, 50, "メッセージ=非アクティブ(灰枠)", 13, font)
        # 選択肢: アクティブ
        sw = SelectWindow(x=200, y=60, items=["はい", "いいえ"], cancel_index=1)
        sw.open()
        sw.activate()
        sw.draw()
        # メッセージ: 非アクティブ（表示のみ）
        mw = self._make_msg([{
            "text": "説明テキスト。\nこのウィンドウは\n操作できません。",
            "name": "説明",
        }])
        # is_active=False のまま
        mw.draw()

    def _draw_active_msg(self):
        """メッセージウィンドウがアクティブ、選択肢ウィンドウが非アクティブ。"""
        pyxel.cls(0)
        self._header()
        font = config.FONT
        pyxel.text(16, 30, "メッセージ=アクティブ(白枠)", 7, font)
        pyxel.text(16, 50, "選択肢=非アクティブ(灰枠)", 13, font)
        # 選択肢: 非アクティブ
        sw = SelectWindow(x=200, y=60, items=["はい", "いいえ"], cancel_index=1)
        sw.open()
        # is_active=False のまま
        sw.draw()
        # メッセージ: アクティブ
        mw = self._make_msg([{
            "text": "こちらがアクティブ。\n決定キーで進めます。",
            "name": "アクティブ",
        }])
        mw.activate()
        mw.draw()


    # --- テロップ系 ---
    def _draw_telop_story(self):
        """ストーリー風テロップ（途中表示状態）。"""
        pyxel.cls(0)
        telop = TelopWindow(scroll_speed=1.0, text_color=7)
        lines = [
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
        ]
        telop.show(lines)
        # テロップを途中位置にセット（画面中央あたりに表示）
        telop._scroll_y = -(len(lines) * 24 // 2 - config.SCREEN_HEIGHT // 2)
        telop.y = int(telop._scroll_y)
        telop.draw()

    def _draw_telop_credits(self):
        """スタッフロール風テロップ（途中表示状態）。"""
        pyxel.cls(0)
        telop = TelopWindow(scroll_speed=1.0, text_color=7)
        lines = [
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
        ]
        telop.show(lines)
        # テロップを途中位置にセット
        telop._scroll_y = -(len(lines) * 24 // 2 - config.SCREEN_HEIGHT // 2)
        telop.y = int(telop._scroll_y)
        telop.draw()


if __name__ == "__main__":
    ScreenshotHarness()
