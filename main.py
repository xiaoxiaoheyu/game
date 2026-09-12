from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path

from six_stones.game import Game
from six_stones.players import HeuristicPlayer
from six_stones.theme import Theme
from six_stones.ui import GameUI


def main() -> None:
    parser = argparse.ArgumentParser(description="19x19 六子棋程序对战")
    parser.add_argument("--time", type=float, default=300, help="每方总用时（秒）")
    parser.add_argument("--theme", default="themes/default/theme.json", help="皮肤配置文件")
    parser.add_argument("--delay", type=int, default=350, help="自动落子展示间隔（毫秒）")
    args = parser.parse_args()

    theme_path = Path(args.theme).resolve()
    theme = Theme.load(theme_path)
    player_a = HeuristicPlayer("我方程序 A")
    player_b = HeuristicPlayer("测试程序 B")
    game = Game(player_a, player_b, total_time=args.time)
    root = tk.Tk()
    GameUI.THINK_DELAY_MS = max(10, args.delay)
    GameUI(root, game, theme, theme_path.parent)
    root.mainloop()


if __name__ == "__main__":
    main()

