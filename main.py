"""文字修仙游戏第一章 MVP 入口。"""

from __future__ import annotations

import sys
from typing import Optional

from data import CHAPTER_NAME, FAMILY_NAME, MONTH_NAMES, TOTAL_ACTIONS, VERSION
from player import Player, create_player
from save_load import load_game, save_game
from systems import action_menu_text, monthly_event, perform_action, risk_summary, tutorial_tip
from tournament import format_tournament_result, run_tournament


def print_header() -> None:
    print("=" * 42)
    print(f"{FAMILY_NAME}  第一章：《{CHAPTER_NAME}》  {VERSION}")
    print("=" * 42)
    print("你是青岭沈家旁支子弟。一年后，家族大比开场。")
    print("目标：在 12 个月、36 次行动后进入家族大比前十。")
    print()


def pause() -> None:
    if sys.stdin.isatty():
        input("\n按回车继续...")


def new_game() -> Player:
    print("\n===== 创建玩家 =====")
    name = input("请输入姓名（默认：沈无名）：").strip() or "沈无名"
    player = create_player(name)
    print("\n灵根已定。")
    print(player.status_text())
    pause()
    return player


def load_game_safe() -> Optional[Player]:
    try:
        player = load_game()
    except FileNotFoundError as error:
        print(error)
        return None
    except (ValueError, OSError) as error:
        print(f"读档失败：{error}")
        return None
    print("读档成功。")
    return player


def show_progress(player: Player) -> None:
    month_name = MONTH_NAMES[player.month - 1]
    print("\n" + "-" * 42)
    print(f"进度：{month_name}｜本月第 {player.action_in_month}/3 次行动｜总行动 {player.total_actions}/{TOTAL_ACTIONS}")
    print("-" * 42)
    print(player.status_text())
    warnings = risk_summary(player)
    if warnings:
        print("风险提示：" + "；".join(warnings))
    tip = tutorial_tip(player)
    if tip:
        print(tip)
    print()


def game_loop(player: Player) -> None:
    while not player.finished:
        show_progress(player)
        print(action_menu_text())
        choice = input("请选择：").strip().upper()

        if choice in {"S", "9"}:
            try:
                path = save_game(player)
            except OSError as error:
                print(f"存档失败：{error}")
            else:
                print(f"已存档：{path}")
            continue

        if choice == "L":
            loaded = load_game_safe()
            if loaded is not None:
                player = loaded
            continue

        if choice in {"Q", "0"}:
            print("你暂时离开青岭。")
            return

        before_action = player.total_actions
        result = perform_action(player, choice)
        print("\n" + result)
        if player.total_actions == before_action:
            continue

        if player.total_actions % 3 == 0 and not player.finished:
            print()
            print(monthly_event(player))

        pause()

    print("\n一年期满，青岭沈家家族大比开场。")
    result = run_tournament(player)
    print(format_tournament_result(result))


def main() -> None:
    print_header()
    while True:
        print("1. 新游戏")
        print("2. 读取存档")
        print("3. 退出")
        choice = input("请选择：").strip()

        if choice == "1":
            game_loop(new_game())
            return
        if choice == "2":
            player = load_game_safe()
            if player is not None:
                game_loop(player)
                return
        if choice == "3":
            print("已退出。")
            return
        print("请输入 1、2 或 3。")


if __name__ == "__main__":
    main()
