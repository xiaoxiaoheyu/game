from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path

from six_stones.theme import Theme
from six_stones.ui import SixStonesApp


def main() -> None:
    parser = argparse.ArgumentParser(description="19×19 六子棋")
    parser.add_argument("--theme", default="themes/default/theme.json", help="皮肤配置文件")
    args = parser.parse_args()
    theme_path = Path(args.theme).resolve()
    root = tk.Tk()
    SixStonesApp(root, Theme.load(theme_path), theme_path.parent)
    root.mainloop()


if __name__ == "__main__":
    main()
