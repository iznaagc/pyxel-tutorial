"""テキストデータコンパイラ。

data/text/*.json を読み込み、全ファイルをマージ・バリデーションした上で
gzip 圧縮して data/compiled/text_all.bin に出力する。

使い方:
    .venv/Scripts/python tools/compiler.py
"""

import gzip
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEXT_DIR = os.path.join(PROJECT_ROOT, "data", "text")
COMPILED_DIR = os.path.join(PROJECT_ROOT, "data", "compiled")
OUTPUT_PATH = os.path.join(COMPILED_DIR, "text_all.bin")

REQUIRED_KEYS = {"version", "file_id", "messages", "selections", "telops"}
MERGE_CATEGORIES = ["messages", "selections", "telops"]


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


def load_and_validate(json_path):
    """JSONファイルを読み込みバリデーションして返す。"""
    print(f"  読み込み: {os.path.basename(json_path)}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validate(data, os.path.basename(json_path))
    return data


def merge_all(file_data_list):
    """複数ファイルのデータをマージする。ID重複時はエラー。"""
    merged = {"version": 1, "messages": {}, "selections": {}, "telops": {}}

    # ID → ファイル名の逆引き（重複検出用）
    id_source = {}  # { "messages.msg_basic": "demo.json", ... }

    for filepath, data in file_data_list:
        filename = os.path.basename(filepath)
        for category in MERGE_CATEGORIES:
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


def main():
    os.makedirs(COMPILED_DIR, exist_ok=True)

    json_files = sorted(
        os.path.join(TEXT_DIR, f)
        for f in os.listdir(TEXT_DIR)
        if f.endswith(".json")
    )

    if not json_files:
        print(f"警告: {TEXT_DIR} に JSON ファイルが見つかりません")
        sys.exit(1)

    print(f"テキストファイル: {len(json_files)} 件")

    # 全ファイル読み込み + バリデーション
    file_data_list = []
    for json_path in json_files:
        data = load_and_validate(json_path)
        file_data_list.append((json_path, data))

    # マージ（ID重複チェック込み）
    merged = merge_all(file_data_list)

    total_ids = sum(len(merged[cat]) for cat in MERGE_CATEGORIES)
    print(f"  マージ完了: {total_ids} ID")

    # gzip 圧縮して書き出し
    json_bytes = json.dumps(merged, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.open(OUTPUT_PATH, "wb") as f:
        f.write(json_bytes)

    original_size = len(json_bytes)
    compressed_size = os.path.getsize(OUTPUT_PATH)
    ratio = compressed_size / original_size * 100
    print(f"出力: {OUTPUT_PATH}")
    print(f"  {original_size} -> {compressed_size} bytes ({ratio:.1f}%)")
    print("コンパイル完了!")


if __name__ == "__main__":
    main()
