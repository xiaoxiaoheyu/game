from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .board import Board, Position, format_position
from .constants import BLACK, BOARD_SIZE, COLOR_NAMES, EMPTY, WHITE
from .game import Game, GameStatus
from .logging_utils import save_game
from .theme import Theme


class GameUI:
    CELL = 32
    MARGIN = 34
    THINK_DELAY_MS = 350

    def __init__(self, root: tk.Tk, game: Game, theme: Theme, theme_dir: Path):
        self.root, self.game, self.theme, self.theme_dir = root, game, theme, theme_dir
        root.title("六子棋程序对战系统")
        root.configure(bg=theme.background_color)
        root.resizable(False, False)
        self.images: dict[str, tk.PhotoImage] = {}
        self.running = True
        self.status_var = tk.StringVar()
        self.black_var = tk.StringVar()
        self.white_var = tk.StringVar()
        self.last_var = tk.StringVar(value="等待开局")
        self._build()
        self._load_images()
        self.draw()
        self.game.start_current_clock()
        self.root.after(100, self.tick)
        self.root.after(self.THINK_DELAY_MS, self.auto_turn)

    def _build(self) -> None:
        width = self.MARGIN * 2 + self.CELL * (BOARD_SIZE - 1)
        self.canvas = tk.Canvas(self.root, width=width, height=width, bg=self.theme.board_color, highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=10, padx=14, pady=14)
        panel = tk.Frame(self.root, bg=self.theme.panel_color, width=250, height=width)
        panel.grid(row=0, column=1, sticky="ns", padx=(0, 14), pady=14)
        panel.grid_propagate(False)
        tk.Label(panel, text="程序对战", font=("Microsoft YaHei UI", 20, "bold"), fg=self.theme.accent_color, bg=self.theme.panel_color).pack(pady=(28, 24))
        for var in (self.status_var, self.black_var, self.white_var, self.last_var):
            tk.Label(panel, textvariable=var, font=("Microsoft YaHei UI", 11), fg=self.theme.text_color, bg=self.theme.panel_color, wraplength=210, justify="left").pack(anchor="w", padx=20, pady=8)
        tk.Button(panel, text="暂停 / 继续", command=self.toggle, width=18).pack(pady=(28, 8))
        tk.Button(panel, text="保存棋谱", command=self.save, width=18).pack(pady=8)
        tk.Button(panel, text="退出", command=self.root.destroy, width=18).pack(pady=8)

    def _load_images(self) -> None:
        for key, filename in (("black", self.theme.black_image), ("white", self.theme.white_image), ("board", self.theme.board_image)):
            if filename:
                path = self.theme_dir / filename
                if path.exists():
                    self.images[key] = tk.PhotoImage(file=str(path))

    def point(self, row: int, col: int) -> tuple[int, int]:
        return self.MARGIN + col * self.CELL, self.MARGIN + row * self.CELL

    def draw(self) -> None:
        self.canvas.delete("all")
        if "board" in self.images:
            self.canvas.create_image(0, 0, image=self.images["board"], anchor="nw")
        for index in range(BOARD_SIZE):
            start = self.MARGIN
            end = self.MARGIN + self.CELL * (BOARD_SIZE - 1)
            pos = self.MARGIN + index * self.CELL
            self.canvas.create_line(start, pos, end, pos, fill=self.theme.line_color)
            self.canvas.create_line(pos, start, pos, end, fill=self.theme.line_color)
            self.canvas.create_text(pos, 14, text=chr(ord('A') + index), fill=self.theme.line_color, font=("Arial", 8))
            self.canvas.create_text(14, pos, text=str(index + 1), fill=self.theme.line_color, font=("Arial", 8))
        for row, col in ((3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15)):
            x, y = self.point(row, col); self.canvas.create_oval(x-3,y-3,x+3,y+3,fill=self.theme.line_color,outline="")
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = self.game.board.get(row, col)
                if color != EMPTY:
                    self.draw_stone(row, col, color, (row, col) in self.game.last_moves)
        self.update_labels()

    def draw_stone(self, row: int, col: int, color: int, last: bool) -> None:
        x, y = self.point(row, col); key = "black" if color == BLACK else "white"
        if key in self.images:
            self.canvas.create_image(x, y, image=self.images[key])
        else:
            fill = self.theme.black_color if color == BLACK else self.theme.white_color
            self.canvas.create_oval(x-13, y-13, x+13, y+13, fill=fill, outline="#555" if color == WHITE else "#000", width=1)
        if last:
            self.canvas.create_oval(x-4, y-4, x+4, y+4, fill="#d33", outline="")

    def update_labels(self) -> None:
        black = self.game.players[BLACK]
        white = self.game.players[WHITE]
        self.black_var.set(f"● 黑方：{black.name}\n剩余 {self.game.clocks[BLACK].remaining():.1f} 秒")
        self.white_var.set(f"○ 白方：{white.name}\n剩余 {self.game.clocks[WHITE].remaining():.1f} 秒")
        if self.game.status == GameStatus.RUNNING:
            self.status_var.set(f"第 {self.game.turn_number} 回合\n轮到：{COLOR_NAMES[self.game.current_color]}\n本回合：{self.game.expected_stones} 子")
        elif self.game.status == GameStatus.DRAW:
            self.status_var.set("比赛结束：和棋")
        else:
            reason = "超时" if self.game.status == GameStatus.TIMEOUT else "六子连线"
            self.status_var.set(f"比赛结束\n{COLOR_NAMES[self.game.winner]}获胜（{reason}）")

    def tick(self) -> None:
        if self.running and self.game.status == GameStatus.RUNNING and self.game.check_timeout():
            self.finish()
        self.update_labels()
        self.root.after(100, self.tick)

    def auto_turn(self) -> None:
        if not self.running or self.game.status != GameStatus.RUNNING:
            return
        player = self.game.players[self.game.current_color]
        try:
            moves = player.choose_turn(self.game.board.copy(), self.game.expected_stones, self.game.clocks[self.game.current_color].remaining())
            self.game.submit_turn(moves)
            self.last_var.set(f"{player.name}：{'、'.join(format_position(p) for p in moves)}")
            self.draw()
        except (ValueError, TimeoutError) as exc:
            self.last_var.set(f"提交失败：{exc}")
        if self.game.status != GameStatus.RUNNING:
            self.finish()
        else:
            self.game.start_current_clock()
            self.root.after(self.THINK_DELAY_MS, self.auto_turn)

    def finish(self) -> None:
        self.running = False
        self.draw()
        path = save_game(self.game)
        messagebox.showinfo("比赛结束", f"{self.status_var.get()}\n棋谱已保存：{path}")

    def toggle(self) -> None:
        if self.game.status != GameStatus.RUNNING:
            return
        if self.running:
            self.game.clocks[self.game.current_color].stop()
            self.running = False
            self.last_var.set("比赛已暂停")
        else:
            self.running = True
            self.game.start_current_clock()
            self.last_var.set("比赛继续")
            self.root.after(self.THINK_DELAY_MS, self.auto_turn)

    def save(self) -> None:
        path = save_game(self.game)
        messagebox.showinfo("保存成功", str(path))

