"""テキストデータマネージャー。

コンパイル済みバイナリ（gzip圧縮JSON）を読み込み、
ゲームコードにテキストデータを提供する。
"""

import gzip
import json


class TextManager:
    """テキストデータの読み込みと提供を行う。"""

    def __init__(self):
        self._data = None

    def load(self, bin_path):
        """コンパイル済みバイナリを読み込む。"""
        with gzip.open(bin_path, "rb") as f:
            raw = f.read()
        self._data = json.loads(raw.decode("utf-8"))

    def get_messages(self, msg_id):
        """メッセージリストを返す。MessageWindow.show() にそのまま渡せる形式。"""
        messages = self._data["messages"]
        if msg_id not in messages:
            raise KeyError(f"メッセージID '{msg_id}' が見つかりません。"
                           f"利用可能: {list(messages.keys())}")
        return messages[msg_id]

    def get_selection(self, sel_id):
        """選択肢データを返す。{"items": [...], "cancel_index": N, ...}"""
        selections = self._data["selections"]
        if sel_id not in selections:
            raise KeyError(f"選択肢ID '{sel_id}' が見つかりません。"
                           f"利用可能: {list(selections.keys())}")
        return selections[sel_id]

    def get_telop(self, telop_id):
        """テロップデータを返す。{"lines": [...], "scroll_speed": float}"""
        telops = self._data["telops"]
        if telop_id not in telops:
            raise KeyError(f"テロップID '{telop_id}' が見つかりません。"
                           f"利用可能: {list(telops.keys())}")
        return telops[telop_id]

    def get_event(self, event_id):
        """イベントコマンドリストを返す。[{"cmd": "...", ...}, ...]"""
        events = self._data.get("events", {})
        if event_id not in events:
            raise KeyError(f"イベントID '{event_id}' が見つかりません。"
                           f"利用可能: {list(events.keys())}")
        return events[event_id]
