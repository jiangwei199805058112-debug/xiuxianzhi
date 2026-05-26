"""简单 JSON 存档读档。"""

from __future__ import annotations

import json
from pathlib import Path

from player import Player

SAVE_FILE = Path("save.json")


def save_game(player: Player, path: Path = SAVE_FILE) -> Path:
    player.clamp()
    with path.open("w", encoding="utf-8") as file:
        json.dump(player.to_dict(), file, ensure_ascii=False, indent=2)
    return path


def load_game(path: Path = SAVE_FILE) -> Player:
    if not path.exists():
        raise FileNotFoundError(f"未找到存档文件：{path}")
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("存档格式错误：根节点必须是对象。")
    return Player.from_dict(data)
