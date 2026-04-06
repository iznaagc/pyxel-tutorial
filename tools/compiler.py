"""データコンパイラ。

data/text/*.json および data/characters/*.json を読み込み、
全ファイルをマージ・バリデーションした上で gzip 圧縮して
data/compiled/ に出力する。

使い方:
    .venv/Scripts/python tools/compiler.py
"""

import gzip
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEXT_DIR = os.path.join(PROJECT_ROOT, "data", "text")
CHAR_DIR = os.path.join(PROJECT_ROOT, "data", "characters")
COMPILED_DIR = os.path.join(PROJECT_ROOT, "data", "compiled")
OUTPUT_PATH = os.path.join(COMPILED_DIR, "text_all.bin")
CHAR_OUTPUT_PATH = os.path.join(COMPILED_DIR, "characters_all.bin")

REQUIRED_KEYS = {"version", "file_id", "messages", "selections", "telops"}
MERGE_CATEGORIES = ["messages", "selections", "telops", "events"]

CHAR_STAT_KEYS = {"hp", "mp", "str", "vit", "int", "mnd", "luk"}
CHAR_PHYS_KEYS = {"dagger", "sword", "katana", "axe", "spear", "staff", "claw", "bow"}
CHAR_MAGIC_KEYS = {"healing", "elemental", "buff", "debuff"}


def validate(data, filepath):
    """JSON データのバリデーション。"""
    if "version" not in data:
        raise ValueError(f"{filepath}: 'version' キーがありません")
    if data["version"] != 1:
        raise ValueError(f"{filepath}: 未対応の version: {data['version']}")

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"{filepath}: 必須キーが不足: {missing}")

    for msg_id, msgs in data["messages"].items():
        if not isinstance(msgs, list):
            raise ValueError(f"{filepath}: messages.{msg_id} は配列でなければなりません")

    for sel_id, sel in data["selections"].items():
        if "items" not in sel:
            raise ValueError(f"{filepath}: selections.{sel_id} に 'items' がありません")

    for telop_id, telop in data["telops"].items():
        if "lines" not in telop:
            raise ValueError(f"{filepath}: telops.{telop_id} に 'lines' がありません")

    if "events" in data:
        for ev_id, ev_cmds in data["events"].items():
            if not isinstance(ev_cmds, list):
                raise ValueError(f"{filepath}: events.{ev_id} は配列でなければなりません")
            for i, cmd in enumerate(ev_cmds):
                if not isinstance(cmd, dict) or "cmd" not in cmd:
                    raise ValueError(
                        f"{filepath}: events.{ev_id}[{i}] に 'cmd' キーがありません"
                    )


def load_and_validate(json_path):
    """JSONファイルを読み込みバリデーションして返す。"""
    print(f"  読み込み: {os.path.basename(json_path)}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validate(data, os.path.basename(json_path))
    return data


def merge_all(file_data_list):
    """複数ファイルのデータをマージする。ID重複時はエラー。"""
    merged = {"version": 1, "messages": {}, "selections": {}, "telops": {}, "events": {}}
    id_source = {}

    for filepath, data in file_data_list:
        filename = os.path.basename(filepath)
        for category in MERGE_CATEGORIES:
            if category not in data:
                continue
            for entry_id, entry_data in data[category].items():
                full_key = f"{category}.{entry_id}"
                if full_key in id_source:
                    raise ValueError(
                        f"ID重複: {full_key} が {id_source[full_key]} と "
                        f"{filename} の両方に存在します"
                    )
                id_source[full_key] = filename
                merged[category][entry_id] = entry_data

    return merged


def _require_int_dict(section, required_keys, label):
    """整数キー辞書の必須項目を検証する。"""
    if not isinstance(section, dict):
        raise ValueError(f"{label} が辞書ではありません")

    missing = required_keys - set(section.keys())
    if missing:
        missing_keys = ", ".join(sorted(missing))
        raise ValueError(f"{label} に必須キーが不足: {missing_keys}")

    for key in required_keys:
        if not isinstance(section.get(key), int):
            raise ValueError(f"{label}.{key} は整数でなければなりません")


def validate_character(char_id, char_data, filepath):
    """キャラクターデータのバリデーション。"""
    fname = os.path.basename(filepath)

    if not isinstance(char_data.get("name"), str):
        raise ValueError(f"{fname}: characters.{char_id}.name は文字列でなければなりません")
    if not isinstance(char_data.get("initial_job"), int):
        raise ValueError(f"{fname}: characters.{char_id}.initial_job は整数でなければなりません")
    if not isinstance(char_data.get("personality"), int):
        raise ValueError(f"{fname}: characters.{char_id}.personality は整数でなければなりません")

    graphics = char_data.get("graphics")
    if not isinstance(graphics, dict):
        raise ValueError(f"{fname}: characters.{char_id}.graphics が辞書ではありません")
    for graphic_type in ("face", "walk", "battle"):
        graphic = graphics.get(graphic_type)
        if not isinstance(graphic, dict):
            raise ValueError(
                f"{fname}: characters.{char_id}.graphics.{graphic_type} が辞書ではありません"
            )
        if not isinstance(graphic.get("image"), str):
            raise ValueError(
                f"{fname}: characters.{char_id}.graphics.{graphic_type}.image は文字列でなければなりません"
            )
        if not isinstance(graphic.get("selection_id"), int):
            raise ValueError(
                f"{fname}: characters.{char_id}.graphics.{graphic_type}.selection_id は整数でなければなりません"
            )

    _require_int_dict(
        char_data.get("base_stats"),
        CHAR_STAT_KEYS,
        f"{fname}: characters.{char_id}.base_stats",
    )

    growth_rates = char_data.get("growth_rates")
    if not isinstance(growth_rates, dict):
        raise ValueError(f"{fname}: characters.{char_id}.growth_rates が辞書ではありません")

    _require_int_dict(
        growth_rates.get("stats"),
        CHAR_STAT_KEYS,
        f"{fname}: characters.{char_id}.growth_rates.stats",
    )
    _require_int_dict(
        growth_rates.get("physical_skills"),
        CHAR_PHYS_KEYS,
        f"{fname}: characters.{char_id}.growth_rates.physical_skills",
    )
    _require_int_dict(
        growth_rates.get("magic_skills"),
        CHAR_MAGIC_KEYS,
        f"{fname}: characters.{char_id}.growth_rates.magic_skills",
    )


def load_and_validate_characters(json_path):
    """キャラクター JSON を読み込みバリデーションして返す。"""
    print(f"  読み込み: {os.path.basename(json_path)}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fname = os.path.basename(json_path)
    if data.get("version") != 1:
        raise ValueError(f"{fname}: 未対応の version: {data.get('version')}")
    if "characters" not in data:
        raise ValueError(f"{fname}: 'characters' キーがありません")
    if not isinstance(data["characters"], dict):
        raise ValueError(f"{fname}: 'characters' は辞書でなければなりません")

    for char_id, char_data in data["characters"].items():
        validate_character(char_id, char_data, json_path)

    return data


def merge_characters(file_data_list):
    """複数キャラクターファイルのデータをマージする。"""
    merged = {"version": 1, "characters": {}}
    id_source = {}

    for filepath, data in file_data_list:
        filename = os.path.basename(filepath)
        for char_id, char_data in data.get("characters", {}).items():
            if char_id in id_source:
                raise ValueError(
                    f"キャラクターID重複: {char_id} が {id_source[char_id]} と "
                    f"{filename} の両方に存在します"
                )
            id_source[char_id] = filename
            merged["characters"][char_id] = char_data

    return merged


def compile_text():
    """テキストデータのコンパイル。"""
    json_files = sorted(
        os.path.join(TEXT_DIR, f)
        for f in os.listdir(TEXT_DIR)
        if f.endswith(".json")
    )

    if not json_files:
        print(f"警告: {TEXT_DIR} に JSON ファイルが見つかりません")
        return False

    print(f"テキストファイル: {len(json_files)} 件")

    file_data_list = []
    for json_path in json_files:
        data = load_and_validate(json_path)
        file_data_list.append((json_path, data))

    merged = merge_all(file_data_list)

    total_ids = sum(len(merged[cat]) for cat in MERGE_CATEGORIES)
    print(f"  マージ完了: {total_ids} ID")

    json_bytes = json.dumps(merged, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.open(OUTPUT_PATH, "wb") as f:
        f.write(json_bytes)

    original_size = len(json_bytes)
    compressed_size = os.path.getsize(OUTPUT_PATH)
    ratio = compressed_size / original_size * 100
    print(f"出力: {OUTPUT_PATH}")
    print(f"  {original_size} -> {compressed_size} bytes ({ratio:.1f}%)")
    return True


def compile_characters():
    """キャラクターデータのコンパイル。"""
    if not os.path.isdir(CHAR_DIR):
        print(f"情報: {CHAR_DIR} が存在しないためスキップ")
        return True

    json_files = sorted(
        os.path.join(CHAR_DIR, f)
        for f in os.listdir(CHAR_DIR)
        if f.endswith(".json")
    )

    if not json_files:
        print("情報: キャラクターファイルなし、スキップ")
        return True

    print(f"キャラクターファイル: {len(json_files)} 件")

    file_data_list = []
    for json_path in json_files:
        data = load_and_validate_characters(json_path)
        file_data_list.append((json_path, data))

    merged = merge_characters(file_data_list)
    total = len(merged["characters"])
    print(f"  マージ完了: {total} キャラクター")

    json_bytes = json.dumps(merged, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.open(CHAR_OUTPUT_PATH, "wb") as f:
        f.write(json_bytes)

    original_size = len(json_bytes)
    compressed_size = os.path.getsize(CHAR_OUTPUT_PATH)
    ratio = compressed_size / original_size * 100
    print(f"出力: {CHAR_OUTPUT_PATH}")
    print(f"  {original_size} -> {compressed_size} bytes ({ratio:.1f}%)")
    return True


def main():
    os.makedirs(COMPILED_DIR, exist_ok=True)

    ok = compile_text()
    ok2 = compile_characters()

    if ok and ok2:
        print("コンパイル完了!")
    else:
        if not ok:
            print("テキストコンパイルに失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
