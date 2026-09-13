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


def draw_paw(canvas: tk.Canvas, x: int, y: int, color: str, scale: float = 1) -> None:
    pad = 9 * scale
    canvas.create_oval(x - pad, y - pad / 2, x + pad, y + pad, fill=color, outline="")
    for dx, dy in ((-10, -10), (-3, -15), (5, -15), (12, -9)):
        radius = 4 * scale
        canvas.create_oval(
            x + dx * scale - radius,
            y + dy * scale - radius,
            x + dx * scale + radius,
            y + dy * scale + radius,
            fill=color,
            outline="",
        )


class SoftButton(tk.Canvas):
    def __init__(self, parent, text: str, command, theme: Theme, width: int = 250):
        super().__init__(
            parent,
            width=width,
            height=58,
            bg=parent.cget("bg"),
            highlightthickness=0,
            cursor="hand2",
        )
        self.command = command
        self.theme = theme
        self.width = width
        self.text = text
        self.draw(False)
        self.bind("<Enter>", lambda _: self.draw(True))
        self.bind("<Leave>", lambda _: self.draw(False))
        self.bind("<Button-1>", lambda _: self.draw(True, pressed=True))
        self.bind("<ButtonRelease-1>", self.activate)

    def rounded_box(self, x1, y1, x2, y2, radius, **options) -> None:
        points = (
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y1 + radius,
            x1,
            y1,
        )
        self.create_polygon(points, smooth=True, splinesteps=24, **options)

    def draw(self, hovered: bool, pressed: bool = False) -> None:
        self.delete("all")
        offset = 5 if not pressed else 2
        self.rounded_box(
            7,
            7 + offset,
            self.width - 3,
            51 + offset,
            15,
            fill=self.theme.shadow_color,
        )
        color = self.theme.secondary_color if hovered else self.theme.accent_color
        self.rounded_box(3, 3, self.width - 7, 47, 15, fill=color)
        self.create_text(
            self.width / 2 - 5,
            25,
            text=self.text,
            fill="white",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        draw_paw(self, self.width - 27, 28, "#fff7f2", 0.45)

    def activate(self, event) -> None:
        self.draw(True)
        if 0 <= event.x <= self.width and 0 <= event.y <= 58:
            self.command()


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
        mascot = tk.Canvas(
            frame,
            width=420,
            height=118,
            bg=self.theme.background_color,
            highlightthickness=0,
        )
        mascot.pack(pady=(62, 0))
        mascot.create_polygon(108, 46, 128, 14, 145, 51, fill=self.theme.panel_color, outline=self.theme.accent_color, width=3)
        mascot.create_polygon(275, 51, 292, 14, 312, 46, fill=self.theme.panel_color, outline=self.theme.accent_color, width=3)
        mascot.create_text(210, 64, text=title, font=("Microsoft YaHei UI", 30, "bold"), fill=self.theme.text_color)
        draw_paw(mascot, 74, 68, self.theme.accent_color, 0.7)
        draw_paw(mascot, 346, 68, self.theme.secondary_color, 0.7)
        tk.Label(
            frame,
            text=subtitle,
            font=("Microsoft YaHei UI", 12),
            fg=self.theme.text_color,
            bg=self.theme.background_color,
        ).pack(pady=(0, 28))
        return frame

    def menu_button(self, parent: tk.Widget, text: str, command) -> SoftButton:
        button = SoftButton(parent, text, command, self.theme)
        button.pack(pady=7)
        return button

    def show_main_menu(self) -> None:
        frame = self.menu_frame("六子棋", "和朋友或电脑来一局吧")
        self.menu_button(frame, "开始游玩", self.show_play_menu)
        self.menu_button(frame, "退出游戏", self.root.destroy)
        self.show(frame)

    def show_play_menu(self) -> None:
        frame = self.menu_frame("选择伙伴", "黑白阵营会在开局时随机决定")
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
            text=f"🐾  {title}",
            font=("Microsoft YaHei UI", 19, "bold"),
            fg=self.theme.text_color,
            bg=self.theme.panel_color,
        ).pack(pady=(24, 14))

        self.black_card = self.player_card(panel, self.black_var, "#2f2a2c")
        self.black_card.pack(fill="x", padx=16, pady=5)
        self.status_label = tk.Label(
            panel,
            textvariable=self.status_var,
            font=("Microsoft YaHei UI", 10, "bold"),
            fg="white",
            bg=self.theme.secondary_color,
            wraplength=190,
            justify="center",
            padx=12,
            pady=9,
        )
        self.status_label.pack(fill="x", padx=20, pady=7)
        self.white_card = self.player_card(panel, self.white_var, "#eee9e5")
        self.white_card.pack(fill="x", padx=16, pady=5)
        tk.Label(
            panel,
            textvariable=self.last_var,
            font=("Microsoft YaHei UI", 9),
            fg=self.theme.muted_text_color,
            bg=self.theme.panel_color,
            wraplength=205,
            justify="center",
        ).pack(fill="x", padx=18, pady=(8, 4))

        self.confirm_button = tk.Button(
            panel,
            text="确认本回合",
            command=self.submit_human,
            state="disabled",
            width=18,
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=self.theme.accent_color,
            fg="white",
            activebackground=self.theme.secondary_color,
            activeforeground="white",
            relief="flat",
            bd=0,
            pady=7,
        )
        self.confirm_button.pack(pady=(9, 5))
        self.panel_button(panel, "清除选择", self.clear_selection)
        self.panel_button(panel, "暂停 / 继续", self.toggle)
        self.panel_button(panel, "保存棋谱", self.save)
        self.panel_button(panel, "返回主菜单", self.leave)

    def player_card(self, parent, variable: tk.StringVar, stone_color: str) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=self.theme.background_color,
            highlightthickness=2,
            highlightbackground=self.theme.shadow_color,
            padx=10,
            pady=8,
        )
        stone = tk.Canvas(
            card,
            width=34,
            height=34,
            bg=self.theme.background_color,
            highlightthickness=0,
        )
        stone.pack(side="left", padx=(0, 8))
        stone.create_oval(3, 3, 31, 31, fill=stone_color, outline=self.theme.shadow_color)
        tk.Label(
            card,
            textvariable=variable,
            font=("Microsoft YaHei UI", 9, "bold"),
            fg=self.theme.text_color,
            bg=self.theme.background_color,
            justify="left",
        ).pack(side="left")
        return card

    def panel_button(self, parent, text: str, command) -> None:
        tk.Button(
            parent,
            text=text,
            command=command,
            width=18,
            font=("Microsoft YaHei UI", 9),
            bg=self.theme.background_color,
            fg=self.theme.text_color,
            activebackground=self.theme.shadow_color,
            relief="flat",
            bd=0,
            pady=4,
        ).pack(pady=3)

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
        else:
            self.draw_grass_tiles()

        self.draw_board_decorations()

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

    def draw_grass_tiles(self) -> None:
        for row in range(BOARD_SIZE - 1):
            for col in range(BOARD_SIZE - 1):
                x1, y1 = self.point(row, col)
                x2, y2 = self.point(row + 1, col + 1)
                color = (
                    self.theme.board_color
                    if (row + col) % 2 == 0
                    else self.theme.board_alt_color
                )
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                direction = -1 if (row * 3 + col) % 2 else 1
                self.canvas.create_line(
                    center_x - 3,
                    center_y + 5,
                    center_x,
                    center_y - 3,
                    center_x + direction * 3,
                    center_y + 2,
                    fill=self.theme.grass_highlight_color,
                    width=2,
                    smooth=True,
                )

    def draw_board_decorations(self) -> None:
        board_end = self.MARGIN + self.CELL * (BOARD_SIZE - 1)
        decoration_color = "#85b66c"
        draw_paw(self.canvas, 16, 17, decoration_color, 0.45)
        draw_paw(self.canvas, board_end + 18, 17, decoration_color, 0.45)
        draw_paw(self.canvas, 16, board_end + 18, decoration_color, 0.45)
        draw_paw(
            self.canvas,
            board_end + 18,
            board_end + 18,
            decoration_color,
            0.45,
        )

    def draw_selected_stone(self, row: int, col: int) -> None:
        x, y = self.point(row, col)
        image_name = "black" if self.game.current_color == BLACK else "white"
        if image_name in self.images:
            self.canvas.create_oval(
                x - 17,
                y - 17,
                x + 17,
                y + 17,
                fill="#dff4ff",
                outline="#65aef2",
                width=3,
            )
            self.canvas.create_image(x, y, image=self.images[image_name])
            return
        self.draw_animal_stone(row, col, self.game.current_color, selected=True)

    def draw_stone(self, row: int, col: int, color: int, last: bool) -> None:
        x, y = self.point(row, col)
        image_name = "black" if color == BLACK else "white"
        if image_name in self.images:
            self.canvas.create_image(x, y, image=self.images[image_name])
        else:
            self.draw_animal_stone(row, col, color)
        if last:
            self.canvas.create_oval(
                x + 6,
                y + 6,
                x + 12,
                y + 12,
                fill=self.theme.accent_color,
                outline="white",
            )

    def draw_animal_stone(
        self, row: int, col: int, color: int, selected: bool = False
    ) -> None:
        if color == BLACK:
            self.draw_cat_head(row, col, selected)
        else:
            self.draw_dog_head(row, col, selected)

    def draw_cat_head(self, row: int, col: int, selected: bool) -> None:
        x, y = self.point(row, col)
        outline = self.theme.success_color if selected else "#40383b"
        outline_width = 3 if selected else 2
        self.canvas.create_oval(
            x - 14,
            y - 14,
            x + 14,
            y + 14,
            fill="#2b2729",
            outline=outline,
            width=outline_width,
        )
        self.canvas.create_polygon(
            x - 11,
            y - 7,
            x - 10,
            y - 14,
            x - 5,
            y - 11,
            x,
            y - 12,
            x + 5,
            y - 11,
            x + 10,
            y - 14,
            x + 11,
            y - 7,
            fill=self.theme.black_color,
            outline="",
            smooth=True,
            splinesteps=24,
        )
        self.canvas.create_oval(
            x - 12,
            y - 11,
            x + 12,
            y + 12,
            fill=self.theme.black_color,
            outline="",
        )
        eye_color = "#f7d778"
        self.canvas.create_oval(x - 7, y - 5, x - 3, y - 1, fill=eye_color, outline="")
        self.canvas.create_oval(x + 3, y - 5, x + 7, y - 1, fill=eye_color, outline="")
        self.canvas.create_oval(x - 3, y, x + 3, y + 5, fill="#ead8cd", outline="")
        self.canvas.create_oval(x - 1.5, y + 1, x + 1.5, y + 3.5, fill="#e99aa8", outline="")
        self.canvas.create_arc(x - 5, y + 2, x, y + 8, start=210, extent=100, style="arc", outline="#ead8cd", width=1)
        self.canvas.create_arc(x, y + 2, x + 5, y + 8, start=230, extent=100, style="arc", outline="#ead8cd", width=1)

    def draw_dog_head(self, row: int, col: int, selected: bool) -> None:
        x, y = self.point(row, col)
        outline = self.theme.success_color if selected else "#bdaea4"
        outline_width = 3 if selected else 2
        ear_color = "#cfa17c"
        self.canvas.create_oval(
            x - 15, y - 10, x - 5, y + 10, fill=ear_color, outline=outline, width=2
        )
        self.canvas.create_oval(
            x + 5, y - 10, x + 15, y + 10, fill=ear_color, outline=outline, width=2
        )
        self.canvas.create_oval(
            x - 13,
            y - 14,
            x + 13,
            y + 14,
            fill=self.theme.white_color,
            outline=outline,
            width=outline_width,
        )
        self.canvas.create_oval(x - 7, y - 5, x - 3, y - 1, fill="#51464a", outline="")
        self.canvas.create_oval(x + 3, y - 5, x + 7, y - 1, fill="#51464a", outline="")
        self.canvas.create_oval(x - 6, y - 1, x + 6, y + 9, fill="#ead8cd", outline="")
        self.canvas.create_oval(x - 3, y + 1, x + 3, y + 6, fill="#51464a", outline="")
        self.canvas.create_arc(x - 5, y + 4, x, y + 10, start=205, extent=105, style="arc", outline="#8d6f62", width=1)
        self.canvas.create_arc(x, y + 4, x + 5, y + 10, start=230, extent=105, style="arc", outline="#8d6f62", width=1)

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

        def calculate_move() -> None:
            try:
                moves = player.choose_turn(board, stone_count)
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

        active_color = self.theme.accent_color
        inactive_color = self.theme.shadow_color
        self.black_card.configure(
            highlightbackground=(
                active_color if self.game.current_color == BLACK else inactive_color
            )
        )
        self.white_card.configure(
            highlightbackground=(
                active_color if self.game.current_color == WHITE else inactive_color
            )
        )

        if self.game.status == GameStatus.RUNNING:
            self.status_label.configure(bg=self.theme.secondary_color)
            self.status_var.set(
                f"第 {self.game.turn_number} 回合\n"
                f"轮到：{COLOR_NAMES[self.game.current_color]}\n"
                f"本回合：{self.game.expected_stones} 子"
            )
        elif self.game.status == GameStatus.DRAW:
            self.status_label.configure(bg=self.theme.muted_text_color)
            self.status_var.set("对局结束：和棋")
        else:
            self.status_label.configure(bg=self.theme.success_color)
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
