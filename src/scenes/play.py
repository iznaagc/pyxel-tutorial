import pyxel
from src.constants import SCENE_PLAY, SCENE_CLEAR, SCENE_TITLE, TILE_SIZE, LEVELS, WINDOW_WIDTH, WINDOW_HEIGHT

class PlayScene:
    """ゲーム本編（プレイ画面）の管理クラス"""
    def __init__(self, app):
        self.app = app
        self.walls = []   # 壁の座標リスト
        self.goals = []   # ゴールの座標リスト
        self.boxes = []   # 箱の座標リスト
        self.player_x = 0 # プレイヤーのX座標（タイル単位）
        self.player_y = 0 # プレイヤーのY座標（タイル単位）
        self.offset_x = 0 # マップを中央に寄せるための表示オフセット
        self.offset_y = 0
        self.history = [] # アクション履歴（Undo用）

    def init_game(self):
        """現在のレベルのマップデータを読み込み、初期化する"""
        self.walls = []
        self.goals = []
        self.boxes = []
        self.history = []
        
        # 現在のレベルの文字列マップを取得
        current_map = LEVELS[self.app.current_level]
        map_width = 0
        map_height = len(current_map)
        
        # 文字列を解析して各要素の座標を保存
        for y, row in enumerate(current_map):
            map_width = max(map_width, len(row))
            for x, char in enumerate(row):
                if char == '#': # 壁
                    self.walls.append((x, y))
                elif char == '.': # ゴール
                    self.goals.append((x, y))
                elif char == '$': # 箱
                    self.boxes.append((x, y))
                elif char == '@': # プレイヤー
                    self.player_x = x
                    self.player_y = y
                    
        # マップが画面中央に来るようにオフセットを計算
        self.offset_x = (WINDOW_WIDTH - (map_width * TILE_SIZE)) // 2
        self.offset_y = (WINDOW_HEIGHT - (map_height * TILE_SIZE)) // 2

    def save_state(self):
        """現在の状態（プレイヤーと箱の座標）を履歴に保存する（シャローコピー）"""
        self.history.append({
            'px': self.player_x,
            'py': self.player_y,
            'boxes': list(self.boxes) # 箱のリストを新しく作って保存
        })

    def undo_state(self):
        """1手前の状態に戻す（Undo機能）"""
        if len(self.history) > 0:
            last_state = self.history.pop()
            self.player_x = last_state['px']
            self.player_y = last_state['py']
            self.boxes = list(last_state['boxes'])
            pyxel.play(0, 0) # 戻った合図に移動音を鳴らす

    def update(self):
        """プレイ画面の更新（移動・判定・入力）"""
        dx = 0
        dy = 0
        
        # キー入力の受け取り
        if pyxel.btnp(pyxel.KEY_UP): dy = -1
        elif pyxel.btnp(pyxel.KEY_DOWN): dy = 1
        elif pyxel.btnp(pyxel.KEY_LEFT): dx = -1
        elif pyxel.btnp(pyxel.KEY_RIGHT): dx = 1
        elif pyxel.btnp(pyxel.KEY_Z): self.undo_state() # Undo実行
            
        if dx != 0 or dy != 0:
            # 移動先の座標を計算
            nx = self.player_x + dx
            ny = self.player_y + dy
            
            # --- 当たり判定ロジック ---
            if (nx, ny) in self.walls:
                pass # 壁なら動けない
            elif (nx, ny) in self.boxes:
                # 移動先に箱がある場合、その奥（箱の移動先）を計算
                bx = nx + dx
                by = ny + dy
                
                # 箱が動けるか（奥が壁でも箱でもないか）チェック
                if (bx, by) not in self.walls and (bx, by) not in self.boxes:
                    # 移動を確定させる前に現在の状態を保存
                    self.save_state()
                    # 箱を移動
                    self.boxes.remove((nx, ny))
                    self.boxes.append((bx, by))
                    # プレイヤーを移動
                    self.player_x = nx
                    self.player_y = ny
                    pyxel.play(0, 1) # 箱を押す音
            else:
                # 障害物がない場合、そのまま移動
                self.save_state()
                self.player_x = nx
                self.player_y = ny
                pyxel.play(0, 0) # 移動音

        # --- クリア判定 ---
        if len(self.boxes) > 0 and len(self.goals) > 0:
            won = True
            for box in self.boxes:
                if box not in self.goals:
                    # ゴールに乗っていない箱が1つでもあればクリアではない
                    won = False
                    break
            if won:
                # 全ての箱がゴールに乗った！クリア画面へ遷移
                self.app.scene = SCENE_CLEAR
                self.app.scenes[SCENE_CLEAR].on_enter()

        # デバッグ用・緊急用ボタン
        if pyxel.btnp(pyxel.KEY_C): # 強制クリア
            self.app.scene = SCENE_CLEAR
            self.app.scenes[SCENE_CLEAR].on_enter()
        if pyxel.btnp(pyxel.KEY_R): # リトライ（レベルを最初から）
            self.init_game()

    def draw(self):
        """プレイ画面の描画処理"""
        # 操作説明
        pyxel.text(5, 5, "Z:Undo R:Retry C:Clear(Debug)", 13)
        
        # 画面座標計算用ヘルパー
        def scr_x(gx): return self.offset_x + gx * TILE_SIZE
        def scr_y(gy): return self.offset_y + gy * TILE_SIZE
        
        # 1. 床を敷き詰める（マップの範囲内のみ）
        current_map = LEVELS[self.app.current_level]
        map_width = len(current_map[0])
        map_height = len(current_map)
        for y in range(map_height):
            for x in range(map_width):
                pyxel.blt(scr_x(x), scr_y(y), 0, 0, 0, 8, 8)
        
        # 2. ゴールを描画
        for gx, gy in self.goals:
            pyxel.blt(scr_x(gx), scr_y(gy), 0, 16, 0, 8, 8, 0)
            
        # 3. 壁を描画
        for wx, wy in self.walls:
            pyxel.blt(scr_x(wx), scr_y(wy), 0, 8, 0, 8, 8, 0)
            
        # 4. 箱を描画
        for bx, by in self.boxes:
            pyxel.blt(scr_x(bx), scr_y(by), 0, 24, 0, 8, 8, 0)
            
        # 5. プレイヤーを描画
        pyxel.blt(scr_x(self.player_x), scr_y(self.player_y), 0, 32, 0, 8, 8, 0)
