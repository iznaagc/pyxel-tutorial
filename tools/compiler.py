"""テキストデータコンパイラ。

data/text/*.json を読み込み、バリデーションした上で
gzip 圧縮して data/compiled/*.bin に出力する。

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

REQUIRED_KEYS = {"version", "messages", "selections", "telops"}


def validate(data, filepath):
    """JSON データのバリデーション。"""
    # version チェック
    if "version" not in data:
        raise ValueError(f"{filepath}: 'version' キーがありません")
    if data["version"] != 1:
        raise ValueError(f"{filepath}: 未対応の version: {data['version']}")

    # 必須キー確認
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"{filepath}: 必須キーが不足: {missing}")

    # messages の各エントリが list であること
    for msg_id, msgs in data["messages"].items():
        if not isinstance(msgs, list):
            raise ValueError(f"{filepath}: messages.{msg_id} は配列でなければなりません")

    # selections の各エントリに items があること
    for sel_id, sel in data["selections"].items():
        if "items" not in sel:
            raise ValueError(f"{filepath}: selections.{sel_id} に 'items' がありません")

    # telops の各エントリに lines があること
    for telop_id, telop in data["telops"].items():
        if "lines" not in telop:
            raise ValueError(f"{filepath}: telops.{telop_id} に 'lines' がありません")


def compile_file(json_path):
    """JSON ファイルを読み込み、バリデーション後に gzip 圧縮して .bin に出力する。"""
    print(f"読み込み: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validate(data, json_path)

    # 出力先
    basename = os.path.splitext(os.path.basename(json_path))[0]
    bin_path = os.path.join(COMPILED_DIR, f"{basename}.bin")

    # gzip 圧縮して書き出し
    json_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.open(bin_path, "wb") as f:
        f.write(json_bytes)

    original_size = len(json_bytes)
    compressed_size = os.path.getsize(bin_path)
    ratio = compressed_size / original_size * 100
    print(f"出力: {bin_path} ({original_size} -> {compressed_size} bytes, {ratio:.1f}%)")


def main():
    os.makedirs(COMPILED_DIR, exist_ok=True)

    json_files = [
        os.path.join(TEXT_DIR, f)
        for f in os.listdir(TEXT_DIR)
        if f.endswith(".json")
    ]

    if not json_files:
        print(f"警告: {TEXT_DIR} に JSON ファイルが見つかりません")
        sys.exit(1)

    for json_path in sorted(json_files):
        compile_file(json_path)

    print("コンパイル完了!")


if __name__ == "__main__":
    main()
