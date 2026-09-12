from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .board import Position, format_position
from .constants import BLACK, BOARD_SIZE, COLOR_NAMES, EMPTY, WHITE
from .game import Game, GameStatus
from .logging_utils import save_game
from .players import HeuristicPlayer, HumanPlayer
from .theme import Theme


class SixStonesApp:
    def __init__(self, root: tk.Tk, theme: Theme, theme_dir: Path):
        self.root = root
        self.theme = theme
        self.theme_dir = theme_dir
        self.current: tk.Widget | None = None

        root.title("六子棋")
        root.configure(bg=theme.background_color)
        root.resizable(False, False)
        self.show_main_menu()

    def show(self, widget: tk.Widget) -> None:
        if self.current is not None:
            self.current.destroy()
        self.current = widget
        widget.pack(fill="both", expand=True)

    def menu_frame(self, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(
            self.root, bg=self.theme.background_color, width=900, height=650
        )
        frame.pack_propagate(False)
        tk.Label(
            frame,
            text=title,
            font=("Microsoft YaHei UI", 30, "bold"),
            fg=self.theme.accent_color,
            bg=self.theme.background_color,
        ).pack(pady=(100, 10))
        tk.Label(
            frame,
            text=subtitle,
            font=("Microsoft YaHei UI", 12),
            fg=self.theme.text_color,
            bg=self.theme.background_color,
        ).pack(pady=(0, 38))
        return frame

    def menu_button(self, parent: tk.Widget, text: str, command) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=25,
            height=2,
            font=("Microsoft YaHei UI", 12),
            bg=self.theme.panel_color,
            fg=self.theme.text_color,
            activebackground=self.theme.accent_color,
            bd=0,
        )
        button.pack(pady=9)
        return button

    def show_main_menu(self) -> None:
        frame = self.menu_frame("六子棋", "19×19 六子棋游玩")
        self.menu_button(frame, "开始游玩", self.show_play_menu)
        self.menu_button(frame, "退出游戏", self.root.destroy)
        self.show(frame)

    def show_play_menu(self) -> None:
        frame = self.menu_frame("游玩模式", "选择本地对战方式")
        self.menu_button(
            frame,
            "真人 vs 真人",
            lambda: self.start_game(
                HumanPlayer("玩家 A"), HumanPlayer("玩家 B"), "真人对战"
            ),
        )
        self.menu_button(
            frame,
            "真人 vs 程序",
            lambda: self.start_game(
                HumanPlayer("玩家"), HeuristicPlayer("电脑程序"), "人机对战"
            ),
        )
        self.menu_button(frame, "返回主菜单", self.show_main_menu)
        self.show(frame)

    def start_game(self, player_a, player_b, title: str) -> None:
        game = Game(player_a, player_b, total_time=600)
        view = GameView(
            self.root,
            game,
            self.theme,
            self.theme_dir,
            title,
            self.show_main_menu,
        )
        self.show(view)


class GameView(tk.Frame):
    CELL = 32
    MARGIN = 34
    THINK_DELAY_MS = 280

    def __init__(
        self,
        root: tk.Tk,
        game: Game,
        theme: Theme,
        theme_dir: Path,
        title: str,
        on_exit,
    ):
        super().__init__(root, bg=theme.background_color)
        self.game = game
        self.theme = theme
        self.theme_dir = theme_dir
        self.on_exit = on_exit
        self.images: dict[str, tk.PhotoImage] = {}
        self.selected: list[Position] = []
        self.running = True
        self.thinking = False
        self.worker_results: queue.Queue = queue.Queue()
        self.status_var = tk.StringVar()
        self.black_var = tk.StringVar()
        self.white_var = tk.StringVar()
        self.last_var = tk.StringVar(value="对局已开始，黑白由系统随机决定")

        self.build_layout(title)
        self.load_images()
        self.draw()
        self.game.start_current_clock()
        self.after(100, self.tick)
        self.after(self.THINK_DELAY_MS, self.advance)

    def build_layout(self, title: str) -> None:
        width = self.MARGIN * 2 + self.CELL * (BOARD_SIZE - 1)
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=width,
            bg=self.theme.board_color,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, padx=14, pady=14)
        self.canvas.bind("<Button-1>", self.on_board_click)

        panel = tk.Frame(self, bg=self.theme.panel_color, width=250, height=width)
        panel.grid(row=0, column=1, sticky="ns", padx=(0, 14), pady=14)
        panel.grid_propagate(False)
        tk.Label(
            panel,
            text=title,
            font=("Microsoft YaHei UI", 19, "bold"),
            fg=self.theme.accent_color,
            bg=self.theme.panel_color,
        ).pack(pady=(26, 18))
        for variable in (
            self.status_var,
            self.black_var,
            self.white_var,
            self.last_var,
        ):
            tk.Label(
                panel,
                textvariable=variable,
                font=("Microsoft YaHei UI", 10),
                fg=self.theme.text_color,
                bg=self.theme.panel_color,
                wraplength=210,
                justify="left",
            ).pack(anchor="w", padx=20, pady=6)

        self.confirm_button = tk.Button(
            panel,
            text="确认本回合",
            command=self.submit_human,
            state="disabled",
            width=18,
        )
        self.confirm_button.pack(pady=(18, 6))
        tk.Button(
            panel, text="清除选择", command=self.clear_selection, width=18
        ).pack(pady=6)
        tk.Button(panel, text="暂停 / 继续", command=self.toggle, width=18).pack(
            pady=6
        )
        tk.Button(panel, text="保存棋谱", command=self.save, width=18).pack(pady=6)
        tk.Button(panel, text="返回主菜单", command=self.leave, width=18).pack(pady=6)

    def load_images(self) -> None:
        image_names = {
            "black": self.theme.black_image,
            "white": self.theme.white_image,
            "board": self.theme.board_image,
        }
        for name, filename in image_names.items():
            if not filename:
                continue
            path = self.theme_dir / filename
            if path.exists():
                self.images[name] = tk.PhotoImage(file=str(path))

    def point(self, row: int, col: int) -> tuple[int, int]:
        return self.MARGIN + col * self.CELL, self.MARGIN + row * self.CELL

    def draw(self) -> None:
        self.canvas.delete("all")
        if "board" in self.images:
            self.canvas.create_image(0, 0, image=self.images["board"], anchor="nw")

        start = self.MARGIN
        end = self.MARGIN + self.CELL * (BOARD_SIZE - 1)
        for index in range(BOARD_SIZE):
            position = self.MARGIN + index * self.CELL
            self.canvas.create_line(
                start, position, end, position, fill=self.theme.line_color
            )
            self.canvas.create_line(
                position, start, position, end, fill=self.theme.line_color
            )
            self.canvas.create_text(
                position,
                14,
                text=chr(65 + index),
                fill=self.theme.line_color,
                font=("Arial", 8),
            )
            self.canvas.create_text(
                14,
                position,
                text=str(index + 1),
                fill=self.theme.line_color,
                font=("Arial", 8),
            )

        star_points = (3, 9, 15)
        for row in star_points:
            for col in star_points:
                x, y = self.point(row, col)
                self.canvas.create_oval(
                    x - 3,
                    y - 3,
                    x + 3,
                    y + 3,
                    fill=self.theme.line_color,
                    outline="",
                )

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = self.game.board.get(row, col)
                if color != EMPTY:
                    self.draw_stone(
                        row, col, color, (row, col) in self.game.last_moves
                    )

        for row, col in self.selected:
            self.draw_selected_stone(row, col)
        self.update_labels()

    def draw_selected_stone(self, row: int, col: int) -> None:
        x, y = self.point(row, col)
        fill = (
            self.theme.black_color
            if self.game.current_color == BLACK
            else self.theme.white_color
        )
        self.canvas.create_oval(
            x - 13,
            y - 13,
            x + 13,
            y + 13,
            fill=fill,
            outline="#32d17d",
            width=3,
            stipple="gray50",
        )

    def draw_stone(self, row: int, col: int, color: int, last: bool) -> None:
        x, y = self.point(row, col)
        image_name = "black" if color == BLACK else "white"
        if image_name in self.images:
            self.canvas.create_image(x, y, image=self.images[image_name])
        else:
            fill = (
                self.theme.black_color if color == BLACK else self.theme.white_color
            )
            outline = "#555" if color == WHITE else "#000"
            self.canvas.create_oval(
                x - 13, y - 13, x + 13, y + 13, fill=fill, outline=outline
            )
        if last:
            self.canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4, fill="#d33", outline=""
            )

    def is_human_turn(self) -> bool:
        return isinstance(self.game.players[self.game.current_color], HumanPlayer)

    def on_board_click(self, event: tk.Event) -> None:
        if (
            not self.running
            or self.game.status != GameStatus.RUNNING
            or not self.is_human_turn()
        ):
            return

        position = (
            round((event.y - self.MARGIN) / self.CELL),
            round((event.x - self.MARGIN) / self.CELL),
        )
        if not self.game.board.is_empty(*position):
            return
        if position in self.selected:
            self.selected.remove(position)
        elif len(self.selected) < self.game.expected_stones:
            self.selected.append(position)

        ready = len(self.selected) == self.game.expected_stones
        self.confirm_button.configure(state="normal" if ready else "disabled")
        self.draw()

    def submit_human(self) -> None:
        if len(self.selected) != self.game.expected_stones:
            return
        player = self.game.players[self.game.current_color]
        moves = self.selected[:]
        self.selected.clear()
        try:
            self.game.submit_turn(moves)
            positions = "、".join(format_position(position) for position in moves)
            self.last_var.set(f"{player.name}：{positions}")
        except (ValueError, TimeoutError) as error:
            self.last_var.set(str(error))

        self.confirm_button.configure(state="disabled")
        self.draw()
        if self.game.status != GameStatus.RUNNING:
            self.finish()
            return
        self.game.start_current_clock()
        self.after(self.THINK_DELAY_MS, self.advance)

    def clear_selection(self) -> None:
        self.selected.clear()
        self.confirm_button.configure(state="disabled")
        self.draw()

    def advance(self) -> None:
        if (
            not self.running
            or self.game.status != GameStatus.RUNNING
            or self.is_human_turn()
            or self.thinking
        ):
            return

        self.thinking = True
        player = self.game.players[self.game.current_color]
        board = self.game.board.copy()
        stone_count = self.game.expected_stones
        time_left = self.game.clocks[self.game.current_color].remaining()

        def calculate_move() -> None:
            try:
                moves = player.choose_turn(board, stone_count, time_left)
                self.worker_results.put(("ok", player, moves))
            except Exception as error:
                # A player implementation is an execution boundary. Its failure
                # ends that player's turn instead of taking down the Tk event loop.
                self.worker_results.put(("error", player, error))

        threading.Thread(target=calculate_move, daemon=True).start()
        self.after(50, self.poll_worker)

    def poll_worker(self) -> None:
        try:
            kind, player, value = self.worker_results.get_nowait()
        except queue.Empty:
            if self.game.check_timeout():
                self.finish()
            elif self.thinking:
                self.after(50, self.poll_worker)
            return

        self.thinking = False
        if kind == "error":
            self.last_var.set(f"程序错误：{value}")
            self.game.clocks[self.game.current_color].remaining_seconds = 0
            self.game.check_timeout()
        else:
            try:
                self.game.submit_turn(value)
                positions = "、".join(format_position(position) for position in value)
                self.last_var.set(f"{player.name}：{positions}")
            except (ValueError, TimeoutError) as error:
                self.last_var.set(f"提交失败：{error}")

        self.draw()
        if self.game.status != GameStatus.RUNNING:
            self.finish()
            return
        self.game.start_current_clock()
        self.after(self.THINK_DELAY_MS, self.advance)

    def tick(self) -> None:
        if (
            self.running
            and self.game.status == GameStatus.RUNNING
            and self.game.check_timeout()
        ):
            self.finish()
        self.update_labels()
        self.after(100, self.tick)

    def update_labels(self) -> None:
        black_time = self.game.clocks[BLACK].remaining()
        white_time = self.game.clocks[WHITE].remaining()
        self.black_var.set(
            f"● 黑方：{self.game.players[BLACK].name}\n剩余 {black_time:.1f} 秒"
        )
        self.white_var.set(
            f"○ 白方：{self.game.players[WHITE].name}\n剩余 {white_time:.1f} 秒"
        )

        if self.game.status == GameStatus.RUNNING:
            self.status_var.set(
                f"第 {self.game.turn_number} 回合\n"
                f"轮到：{COLOR_NAMES[self.game.current_color]}\n"
                f"本回合：{self.game.expected_stones} 子"
            )
        elif self.game.status == GameStatus.DRAW:
            self.status_var.set("对局结束：和棋")
        else:
            reason = (
                "超时" if self.game.status == GameStatus.TIMEOUT else "六子连线"
            )
            self.status_var.set(
                f"对局结束\n{COLOR_NAMES[self.game.winner]}获胜（{reason}）"
            )

    def finish(self) -> None:
        if not self.running:
            return
        self.running = False
        self.draw()
        path = save_game(self.game)
        messagebox.showinfo(
            "对局结束", f"{self.status_var.get()}\n棋谱已保存：{path}"
        )

    def toggle(self) -> None:
        if self.game.status != GameStatus.RUNNING:
            return
        if self.running:
            self.game.clocks[self.game.current_color].stop()
            self.running = False
            self.last_var.set("对局已暂停")
            return
        self.running = True
        self.game.start_current_clock()
        self.last_var.set("对局继续")
        self.after(self.THINK_DELAY_MS, self.advance)

    def save(self) -> None:
        messagebox.showinfo("保存成功", str(save_game(self.game)))

    def leave(self) -> None:
        self.running = False
        self.game.clocks[self.game.current_color].stop()
        self.on_exit()
