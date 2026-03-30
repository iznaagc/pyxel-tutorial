import pyxel

class Audio:
    """音声（BGM、SE、ME）の再生を管理するクラス。"""

    @staticmethod
    def play_bgm(music_no: int, loop: bool = True):
        """BGMを再生する。
        
        Args:
            music_no: 再生する音楽（ミュージック）番号
            loop: ループ再生するかどうか
        """
        pyxel.playm(music_no, loop=loop)

    @staticmethod
    def stop_all():
        """すべての音声（BGM、SE、ME）の再生を停止する。"""
        pyxel.stop()

    @staticmethod
    def play_se(ch: int, snd_no: int):
        """SE（効果音）を再生する。
        
        Args:
            ch: 再生するチャンネル（0〜3）
            snd_no: 再生するサウンド番号
        """
        pyxel.play(ch, snd_no)

    @staticmethod
    def play_me(music_no: int):
        """ME（ファンファーレなどの短い音楽）を再生する。
        一度だけ再生し、ループしない。
        
        注意 (Note): 
        MEはBGMと同じミュージック機構を使うため、再生開始時に現在のBGMが停止します。
        MEが終了したあと、必要に応じて利用側で再度BGMを再生（復帰）させる必要があります。
        
        Args:
            music_no: 再生する音楽（ミュージック）番号
        """
        pyxel.playm(music_no, loop=False)

    @staticmethod
    def stop_ch(ch: int):
        """指定したチャンネルの音声を停止する。
        
        Args:
            ch: 停止するチャンネル（0〜3）
        """
        pyxel.stop(ch)
