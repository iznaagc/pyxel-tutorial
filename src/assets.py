import pyxel

def setup_assets():
    # 0: Floor (Navy dotted)
    pyxel.images[0].set(0, 0, [
        "11111111", "10111111", "11111101", "11101111",
        "11111111", "11110111", "10111111", "11111111"
    ])
    # 1: Wall (Brown bricks)
    pyxel.images[0].set(8, 0, [
        "44444444", "40444044", "44444444", "44044404",
        "44444444", "40444044", "44444444", "44044404"
    ])
    # 2: Goal (Red target on floor)
    pyxel.images[0].set(16, 0, [
        "11111111", "11888811", "18111181", "18188181",
        "18188181", "18111181", "11888811", "11111111"
    ])
    # 3: Box (Orange with yellow highlights)
    pyxel.images[0].set(24, 0, [
        "99999999", "9aaaaaa9", "9a9999a9", "9a9999a9",
        "9a9999a9", "9a9999a9", "9aaaaaa9", "99999999"
    ])
    # 4: Player (White body, peach face)
    pyxel.images[0].set(32, 0, [
        "00000000", "00777700", "07eeee70", "07fefef0",
        "07eeee70", "00888800", "00800800", "00000000"
    ])
    
    # Audio
    # Sound 0: Move
    pyxel.sounds[0].set("a2", "p", "6", "vffnn", 10)
    # Sound 1: Push Box
    pyxel.sounds[1].set("c2", "n", "4", "vffnn", 10)
    # Sound 2: Clear
    pyxel.sounds[2].set("c3e3g3c4", "s", "4", "vffn", 30)
