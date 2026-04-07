"""イベントインタプリタ。

JSONで定義されたイベントコマンドリストを逐次実行するエンジン。
RPGツクールのイベントコマンド実行エンジンに相当する。

使い方:
    interpreter = EventInterpreter(scene_manager)
    interpreter.start(config.TEXT_MANAGER.get_event("ev_opening"))
    # 毎フレーム:
    interpreter.update()
    interpreter.draw()
"""

import pyxel

import config
from core.audio import Audio
from core.picture import Picture
from ui.message_window import MessageWindow, TEXT_SPEED_FAST
from ui.select_window import SelectWindow
from ui.telop_window import TelopWindow


# ウェイト種別
_WAIT_NONE = ""
_WAIT_FADE = "fade"
_WAIT_MESSAGE = "message"
_WAIT_SELECTION = "selection"
_WAIT_TELOP = "telop"
_WAIT_MOVE_PICTURE = "move_picture"
_WAIT_FRAMES = "wait"


class EventInterpreter:
    """イベントコマンドを逐次実行するインタプリタ。"""

    def __init__(self, scene_manager):
        self._scene_manager = scene_manager

        # コマンド実行状態
        self._commands = []
        self._index = 0
        self._running = False
        self._waiting = False
        self._wait_type = _WAIT_NONE

        # ピクチャ管理（番号 → Picture）
        self._pictures = {}

        # 画面フェード
        self._fade_alpha = 0.0      # 現在値 (0.0〜1.0)
        self._fade_target = 0.0
        self._fade_speed = 0.0
        self._fade_color = 0
        self._screen_faded_out = False  # フェードアウト状態か

        # UIウィンドウ
        self._msg_window = MessageWindow()
        self._select_window = None
        self._telop_window = None

        # ラベル
        self._labels = {}

        # ウェイト用
        self._wait_counter = 0
        self._wait_picture_no = -1

        # 選択肢の分岐情報
        self._selection_branches = None

        # フェード用オーバーレイ画像
        self._fade_overlay_img = None

    @property
    def is_running(self):
        """イベント実行中か。"""
        return self._running

    def start(self, commands):
        """イベントの実行を開始する。

        Args:
            commands: コマンドリスト [{"cmd": "...", ...}, ...]
        """
        self._commands = commands
        self._index = 0
        self._running = True
        self._waiting = False
        self._wait_type = _WAIT_NONE

        # ラベルをプリスキャン
        self._labels = {}
        for i, cmd in enumerate(commands):
            if cmd.get("cmd") == "label":
                self._labels[cmd["name"]] = i

    def stop(self):
        """イベントを強制停止する。"""
        self._running = False
        Audio.stop_all()

    # =========================================================
    # メインループ
    # =========================================================

    def update(self):
        """毎フレームの更新処理。"""
        if not self._running:
            return

        # ピクチャのアニメーション更新（ウェイト中でも常に更新）
        for pic in self._pictures.values():
            pic.update()

        # ウェイト中
        if self._waiting:
            self._update_wait()
            return

        # コマンドを実行（ウェイトなしは同一フレームで連続実行）
        while self._index < len(self._commands):
            cmd = self._commands[self._index]
            self._index += 1
            result = self._execute(cmd)

            if result == "wait":
                self._waiting = True
                return
            if result == "stop":
                return

        # 全コマンド完了
        self._running = False

    def draw(self):
        """イベントが管理するオブジェクトを描画する。"""
        # ピクチャを番号順（小→大 = 奥→手前）に描画
        for no in sorted(self._pictures.keys()):
            self._pictures[no].draw()

        # テロップ
        if self._telop_window and self._telop_window.is_open:
            self._telop_window.draw()

        # メッセージ（最前面）
        self._msg_window.draw()

        # 選択肢
        if self._select_window and self._select_window.is_open:
            self._select_window.draw()

        # 画面フェード（最最前面）
        if self._fade_alpha > 0.0:
            self._draw_fade_overlay()

    # =========================================================
    # コマンド実行ディスパッチ
    # =========================================================

    def _execute(self, cmd):
        """1コマンドを実行する。"wait"/"stop"/None を返す。"""
        cmd_type = cmd["cmd"]
        handler = self._HANDLERS.get(cmd_type)
        if handler is None:
            print(f"[EventInterpreter] 未知のコマンド: {cmd_type}")
            return None
        return handler(self, cmd)

    # --- グラフィック系 ---

    def _exec_show_picture(self, cmd):
        no = cmd["no"]
        filename = cmd["file"]
        x = cmd.get("x", 0)
        y = cmd.get("y", 0)
        opacity = cmd.get("opacity", 100)
        colkey = cmd.get("colkey")
        pic = Picture.from_file(no, filename, x=x, y=y,
                                opacity=opacity, colkey=colkey)
        self._pictures[no] = pic
        return None

    def _exec_move_picture(self, cmd):
        no = cmd["no"]
        pic = self._pictures.get(no)
        if pic is None:
            print(f"[EventInterpreter] move_picture: No.{no} が存在しません")
            return None
        duration = cmd.get("duration", 30)
        pic.move_to(
            x=cmd.get("x"),
            y=cmd.get("y"),
            opacity=cmd.get("opacity"),
            duration=duration,
        )
        self._wait_type = _WAIT_MOVE_PICTURE
        self._wait_picture_no = no
        return "wait"

    def _exec_erase_picture(self, cmd):
        no = cmd["no"]
        self._pictures.pop(no, None)
        return None

    # --- 画面効果系 ---

    def _exec_fadeout(self, cmd):
        duration = cmd.get("duration", 30)
        self._fade_color = cmd.get("color", 0)
        self._fade_target = 1.0
        self._fade_speed = 1.0 / max(1, duration)
        self._wait_type = _WAIT_FADE
        self._screen_faded_out = True
        return "wait"

    def _exec_fadein(self, cmd):
        duration = cmd.get("duration", 30)
        # fadein は現在のフェードを解除する
        if not self._screen_faded_out:
            self._fade_alpha = 0.0
            return None
        self._fade_target = 0.0
        self._fade_speed = 1.0 / max(1, duration)
        self._wait_type = _WAIT_FADE
        self._screen_faded_out = False
        return "wait"

    def _exec_wait(self, cmd):
        self._wait_counter = cmd.get("duration", 60)
        self._wait_type = _WAIT_FRAMES
        return "wait"

    # --- 音声系 ---

    def _exec_play_bgm(self, cmd):
        Audio.play_bgm_file(cmd["file"])
        return None

    def _exec_stop_bgm(self, cmd):
        Audio.stop_all()
        return None

    def _exec_play_se(self, cmd):
        if "file" in cmd:
            Audio.play_se_file(cmd["file"])
        elif "sound_no" in cmd:
            pyxel.play(cmd.get("ch", 3), cmd["sound_no"])
        return None

    def _exec_play_me(self, cmd):
        Audio.play_me_file(cmd["file"])
        return None

    # --- テキスト系 ---

    def _exec_message(self, cmd):
        if "id" in cmd:
            messages = config.TEXT_MANAGER.get_messages(cmd["id"])
        else:
            # インライン定義
            msg = {"text": cmd.get("text", ""), "name": cmd.get("name")}
            messages = [msg]
        self._msg_window.set_text_speed(TEXT_SPEED_FAST)
        self._msg_window.show(messages)
        self._msg_window.activate()
        self._wait_type = _WAIT_MESSAGE
        return "wait"

    def _exec_selection(self, cmd):
        sel_data = config.TEXT_MANAGER.get_selection(cmd["id"])
        self._select_window = SelectWindow(
            x=cmd.get("x", 200), y=cmd.get("y", 60),
            items=sel_data["items"],
            cancel_index=sel_data.get("cancel_index", -1),
        )
        self._select_window.open()
        self._select_window.activate()
        self._selection_branches = cmd.get("branches")
        self._wait_type = _WAIT_SELECTION
        return "wait"

    def _exec_telop(self, cmd):
        if "id" in cmd:
            telop_data = config.TEXT_MANAGER.get_telop(cmd["id"])
        else:
            telop_data = {"lines": cmd.get("lines", []),
                          "scroll_speed": cmd.get("scroll_speed", 1.0)}
        self._telop_window = TelopWindow(
            scroll_speed=telop_data.get("scroll_speed", 1.0),
            text_color=7,
        )
        self._telop_window.show(telop_data["lines"])
        self._wait_type = _WAIT_TELOP
        return "wait"

    # --- フロー制御系 ---

    def _exec_label(self, cmd):
        # ラベルは何もしない（プリスキャン済み）
        return None

    def _exec_jump(self, cmd):
        target = cmd["to"]
        if target in self._labels:
            self._index = self._labels[target]
        else:
            print(f"[EventInterpreter] jump: ラベル '{target}' が見つかりません")
        return None

    def _exec_end(self, cmd):
        self._running = False
        return "stop"

    def _exec_change_scene(self, cmd):
        self._running = False
        Audio.stop_all()
        self._scene_manager.change_scene(cmd["scene"])
        return "stop"

    # コマンドハンドラテーブル
    _HANDLERS = {
        "show_picture": _exec_show_picture,
        "move_picture": _exec_move_picture,
        "erase_picture": _exec_erase_picture,
        "fadeout": _exec_fadeout,
        "fadein": _exec_fadein,
        "wait": _exec_wait,
        "play_bgm": _exec_play_bgm,
        "stop_bgm": _exec_stop_bgm,
        "play_se": _exec_play_se,
        "play_me": _exec_play_me,
        "message": _exec_message,
        "selection": _exec_selection,
        "telop": _exec_telop,
        "label": _exec_label,
        "jump": _exec_jump,
        "end": _exec_end,
        "change_scene": _exec_change_scene,
    }

    # =========================================================
    # ウェイト更新
    # =========================================================

    def _update_wait(self):
        """ウェイト中の状態を更新し、完了したらウェイト解除する。"""
        if self._wait_type == _WAIT_FADE:
            self._update_fade()
            if self._fade_alpha == self._fade_target:
                self._waiting = False
                self._wait_type = _WAIT_NONE

        elif self._wait_type == _WAIT_MESSAGE:
            self._msg_window.update()
            if not self._msg_window.is_busy:
                self._waiting = False
                self._wait_type = _WAIT_NONE

        elif self._wait_type == _WAIT_SELECTION:
            result = self._select_window.update()
            if result is not None:
                self._waiting = False
                self._wait_type = _WAIT_NONE
                # 分岐処理
                if self._selection_branches:
                    label = self._selection_branches.get(str(result))
                    if label and label in self._labels:
                        self._index = self._labels[label]
                self._selection_branches = None

        elif self._wait_type == _WAIT_TELOP:
            self._telop_window.update()
            # Enter/Spaceでスキップ
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
                self._telop_window.skip()
            if self._telop_window.is_complete:
                self._waiting = False
                self._wait_type = _WAIT_NONE

        elif self._wait_type == _WAIT_MOVE_PICTURE:
            pic = self._pictures.get(self._wait_picture_no)
            if pic is None or not pic.is_animating:
                self._waiting = False
                self._wait_type = _WAIT_NONE

        elif self._wait_type == _WAIT_FRAMES:
            self._wait_counter -= 1
            if self._wait_counter <= 0:
                self._waiting = False
                self._wait_type = _WAIT_NONE

    # =========================================================
    # フェード処理
    # =========================================================

    def _update_fade(self):
        """フェードの alpha を target に向けて更新する。"""
        if self._fade_alpha < self._fade_target:
            self._fade_alpha = min(self._fade_target,
                                   self._fade_alpha + self._fade_speed)
        elif self._fade_alpha > self._fade_target:
            self._fade_alpha = max(self._fade_target,
                                   self._fade_alpha - self._fade_speed)

    def _draw_fade_overlay(self):
        """画面全体にフェードオーバーレイを描画する。"""
        if self._fade_overlay_img is None:
            self._fade_overlay_img = pyxel.Image(
                config.SCREEN_WIDTH, config.SCREEN_HEIGHT
            )
            self._fade_overlay_img.rect(
                0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT,
                self._fade_color
            )
        # 色が変わった場合は再生成
        self._fade_overlay_img.rect(
            0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT,
            self._fade_color
        )
        pyxel.dither(self._fade_alpha)
        pyxel.blt(0, 0, self._fade_overlay_img,
                  0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        pyxel.dither(1.0)
