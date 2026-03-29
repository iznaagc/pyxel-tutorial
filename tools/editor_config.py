"""エディタ設定。

画面サイズやレイアウトを変更したい場合はここを編集する。
"""

# --- 画面設定 ---
SCREEN_W = 640           # エディタの横幅（px）
SCREEN_H = 400           # エディタの縦幅（px）
DISPLAY_SCALE = 2        # ウィンドウの表示倍率

# --- レイアウト ---
HEADER_H = 16            # ヘッダーの高さ（px）
STATUS_H = 14            # ステータスバーの高さ（px）
TEXT_PANEL_W = 200       # テキスト一覧パネルの幅（px）

# --- 以下は自動算出（通常は変更不要） ---
PREVIEW_X = TEXT_PANEL_W
PREVIEW_W = SCREEN_W - TEXT_PANEL_W
PANEL_Y = HEADER_H
PANEL_H = SCREEN_H - HEADER_H - STATUS_H
STATUS_Y = SCREEN_H - STATUS_H
