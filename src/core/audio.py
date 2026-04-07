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

    # --- 外部ファイルベースの再生 ---

    @staticmethod
    def play_bgm_file(filename: str, ch: int = 0):
        """外部音声ファイルをBGMとしてループ再生する。

        Args:
            filename: assets/bgm/ 内のファイル名 (例: "field.ogg")
            ch: 再生チャンネル (デフォルト 0)
        """
        import config
        slot = config.ASSETS.load_sound(filename, subdir="audio/bgm")
        pyxel.play(ch, slot, loop=True)

    @staticmethod
    def play_se_file(filename: str, ch: int = 3):
        """外部音声ファイルをSE（効果音）として再生する。

        Args:
            filename: assets/audio/se/ 内のファイル名 (例: "click.wav")
            ch: 再生チャンネル (デフォルト 3)
        """
        import config
        slot = config.ASSETS.load_sound(filename, subdir="audio/se")
        pyxel.play(ch, slot)

    @staticmethod
    def play_me_file(filename: str, ch: int = 0):
        """外部音声ファイルをME（短い音楽）として一度だけ再生する。

        注意: BGMと同じチャンネルを使用するため、BGMは停止します。
        ME終了後、必要に応じて利用側で再度BGMを再生してください。

        Args:
            filename: assets/audio/bgm/ 内のファイル名
            ch: 再生チャンネル (デフォルト 0)
        """
        import config
        slot = config.ASSETS.load_sound(filename, subdir="audio/bgm")
        pyxel.play(ch, slot, loop=False)
