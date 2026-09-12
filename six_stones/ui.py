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
from .network import RemotePlayer, listen_once
from .players import HeuristicPlayer, HumanPlayer
from .theme import Theme


class SixStonesApp:
    def __init__(self, root: tk.Tk, theme: Theme, theme_dir: Path):
        self.root, self.theme, self.theme_dir = root, theme, theme_dir
        root.title("六子棋")
        root.configure(bg=theme.background_color)
        root.resizable(False, False)
        self.current = None
        self.network_stop = threading.Event()
        self.network_events: queue.Queue = queue.Queue()
        self.show_main_menu()

    def show(self, widget: tk.Widget) -> None:
        self.network_stop.set()
        if self.current is not None:
            self.current.destroy()
        self.current = widget
        widget.pack(fill="both", expand=True)

    def menu_frame(self, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(self.root, bg=self.theme.background_color, width=900, height=650)
        frame.pack_propagate(False)
        tk.Label(frame, text=title, font=("Microsoft YaHei UI", 30, "bold"), fg=self.theme.accent_color, bg=self.theme.background_color).pack(pady=(100, 10))
        tk.Label(frame, text=subtitle, font=("Microsoft YaHei UI", 12), fg=self.theme.text_color, bg=self.theme.background_color).pack(pady=(0, 38))
        return frame

    def menu_button(self, parent, text, command):
        button = tk.Button(parent, text=text, command=command, width=25, height=2, font=("Microsoft YaHei UI", 12), bg=self.theme.panel_color, fg=self.theme.text_color, activebackground=self.theme.accent_color, bd=0)
        button.pack(pady=9)
        return button

    def show_main_menu(self) -> None:
        frame = self.menu_frame("六子棋", "19×19 程序比赛与本地游玩")
        self.menu_button(frame, "比赛模式", self.show_competition_config)
        self.menu_button(frame, "游玩模式", self.show_play_menu)
        self.menu_button(frame, "退出游戏", self.root.destroy)
        self.show(frame)

    def show_play_menu(self) -> None:
        frame = self.menu_frame("游玩模式", "选择本地对战方式")
        self.menu_button(frame, "真人 vs 真人", lambda: self.start_game(HumanPlayer("玩家 A"), HumanPlayer("玩家 B"), 600, "真人对战"))
        self.menu_button(frame, "真人 vs 程序", lambda: self.start_game(HumanPlayer("玩家"), HeuristicPlayer("电脑程序"), 600, "人机对战"))
        self.menu_button(frame, "返回主菜单", self.show_main_menu)
        self.show(frame)

    def show_competition_config(self) -> None:
        frame = self.menu_frame("比赛配置", "本程序担任裁判和我方棋手，对方程序通过 TCP 接入")
        form = tk.Frame(frame, bg=self.theme.background_color); form.pack()
        entries = {}
        for row, (label, default) in enumerate((("监听地址", "127.0.0.1"), ("端口", "8765"), ("每方棋钟（秒）", "300"))):
            tk.Label(form, text=label, width=18, anchor="e", font=("Microsoft YaHei UI", 11), fg=self.theme.text_color, bg=self.theme.background_color).grid(row=row, column=0, padx=8, pady=8)
            entry = tk.Entry(form, width=24, font=("Consolas", 11)); entry.insert(0, default); entry.grid(row=row, column=1, padx=8, pady=8); entries[label] = entry
        status = tk.StringVar(value="尚未连接")
        tk.Label(frame, textvariable=status, font=("Microsoft YaHei UI", 10), fg=self.theme.accent_color, bg=self.theme.background_color).pack(pady=12)

        def listen() -> None:
            try:
                host, port, seconds = entries["监听地址"].get().strip(), int(entries["端口"].get()), float(entries["每方棋钟（秒）"].get())
                if not (1 <= port <= 65535) or seconds <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("配置错误", "请输入有效端口和正数棋钟"); return
            self.network_stop = threading.Event(); self.network_events = queue.Queue()
            status.set(f"正在监听 {host}:{port}，等待对方程序连接…"); start_button.configure(state="disabled")
            threading.Thread(target=listen_once, args=(host, port, self.network_events, self.network_stop), daemon=True).start()

            def poll() -> None:
                if self.current is not frame: return
                try: event = self.network_events.get_nowait()
                except queue.Empty: frame.after(100, poll); return
                if event[0] == "connected":
                    _, connection, address = event
                    status.set(f"已连接 {address[0]}:{address[1]}，正在准备比赛")
                    frame.after(300, lambda: self.start_game(HeuristicPlayer("我方程序 A"), RemotePlayer("对方程序 B", connection), seconds, "正式比赛"))
                elif event[0] == "error": status.set(f"连接失败：{event[1]}"); start_button.configure(state="normal")
                else: status.set(event[1]); frame.after(100, poll)
            poll()

        start_button = self.menu_button(frame, "开始监听并准备", listen)
        self.menu_button(frame, "返回主菜单", self.show_main_menu)
        self.show(frame)

    def start_game(self, player_a, player_b, seconds, title) -> None:
        self.show(GameView(self.root, Game(player_a, player_b, total_time=seconds), self.theme, self.theme_dir, title, self.show_main_menu))


class GameView(tk.Frame):
    CELL, MARGIN, THINK_DELAY_MS = 32, 34, 280

    def __init__(self, root, game: Game, theme: Theme, theme_dir: Path, title: str, on_exit):
        super().__init__(root, bg=theme.background_color)
        self.game, self.theme, self.theme_dir, self.on_exit = game, theme, theme_dir, on_exit
        self.images, self.selected = {}, []
        self.running, self.thinking = True, False
        self.worker_results: queue.Queue = queue.Queue()
        self.status_var, self.black_var, self.white_var, self.last_var = (tk.StringVar() for _ in range(4))
        self.last_var.set("比赛已开始，黑白由系统随机决定")
        self._build(title); self._load_images(); self.draw(); self.game.start_current_clock()
        self.after(100, self.tick); self.after(self.THINK_DELAY_MS, self.advance)

    def _build(self, title):
        width=self.MARGIN*2+self.CELL*(BOARD_SIZE-1)
        self.canvas=tk.Canvas(self,width=width,height=width,bg=self.theme.board_color,highlightthickness=0);self.canvas.grid(row=0,column=0,padx=14,pady=14);self.canvas.bind("<Button-1>",self.on_board_click)
        panel=tk.Frame(self,bg=self.theme.panel_color,width=250,height=width);panel.grid(row=0,column=1,sticky="ns",padx=(0,14),pady=14);panel.grid_propagate(False)
        tk.Label(panel,text=title,font=("Microsoft YaHei UI",19,"bold"),fg=self.theme.accent_color,bg=self.theme.panel_color).pack(pady=(26,18))
        for var in (self.status_var,self.black_var,self.white_var,self.last_var):tk.Label(panel,textvariable=var,font=("Microsoft YaHei UI",10),fg=self.theme.text_color,bg=self.theme.panel_color,wraplength=210,justify="left").pack(anchor="w",padx=20,pady=6)
        self.confirm_button=tk.Button(panel,text="确认本回合",command=self.submit_human,state="disabled",width=18);self.confirm_button.pack(pady=(18,6))
        tk.Button(panel,text="清除选择",command=self.clear_selection,width=18).pack(pady=6)
        tk.Button(panel,text="暂停 / 继续",command=self.toggle,width=18).pack(pady=6)
        tk.Button(panel,text="保存棋谱",command=self.save,width=18).pack(pady=6)
        tk.Button(panel,text="返回主菜单",command=self.leave,width=18).pack(pady=6)

    def _load_images(self):
        for key,filename in (("black",self.theme.black_image),("white",self.theme.white_image),("board",self.theme.board_image)):
            path=self.theme_dir/filename if filename else None
            if path and path.exists():self.images[key]=tk.PhotoImage(file=str(path))

    def point(self,row,col):return self.MARGIN+col*self.CELL,self.MARGIN+row*self.CELL

    def draw(self):
        self.canvas.delete("all")
        if "board" in self.images:self.canvas.create_image(0,0,image=self.images["board"],anchor="nw")
        start,end=self.MARGIN,self.MARGIN+self.CELL*(BOARD_SIZE-1)
        for i in range(BOARD_SIZE):
            p=self.MARGIN+i*self.CELL;self.canvas.create_line(start,p,end,p,fill=self.theme.line_color);self.canvas.create_line(p,start,p,end,fill=self.theme.line_color)
            self.canvas.create_text(p,14,text=chr(65+i),fill=self.theme.line_color,font=("Arial",8));self.canvas.create_text(14,p,text=str(i+1),fill=self.theme.line_color,font=("Arial",8))
        for r,c in ((3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15)):
            x,y=self.point(r,c);self.canvas.create_oval(x-3,y-3,x+3,y+3,fill=self.theme.line_color,outline="")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color=self.game.board.get(r,c)
                if color!=EMPTY:self.draw_stone(r,c,color,(r,c) in self.game.last_moves)
        for r,c in self.selected:
            x,y=self.point(r,c);fill=self.theme.black_color if self.game.current_color==BLACK else self.theme.white_color
            self.canvas.create_oval(x-13,y-13,x+13,y+13,fill=fill,outline="#32d17d",width=3,stipple="gray50")
        self.update_labels()

    def draw_stone(self,r,c,color,last):
        x,y=self.point(r,c);key="black" if color==BLACK else "white"
        if key in self.images:self.canvas.create_image(x,y,image=self.images[key])
        else:
            fill=self.theme.black_color if color==BLACK else self.theme.white_color;self.canvas.create_oval(x-13,y-13,x+13,y+13,fill=fill,outline="#555" if color==WHITE else "#000")
        if last:self.canvas.create_oval(x-4,y-4,x+4,y+4,fill="#d33",outline="")

    def is_human_turn(self):return isinstance(self.game.players[self.game.current_color],HumanPlayer)

    def on_board_click(self,event):
        if not self.running or self.game.status!=GameStatus.RUNNING or not self.is_human_turn():return
        pos=(round((event.y-self.MARGIN)/self.CELL),round((event.x-self.MARGIN)/self.CELL))
        if not self.game.board.is_empty(*pos):return
        if pos in self.selected:self.selected.remove(pos)
        elif len(self.selected)<self.game.expected_stones:self.selected.append(pos)
        self.confirm_button.configure(state="normal" if len(self.selected)==self.game.expected_stones else "disabled");self.draw()

    def submit_human(self):
        if len(self.selected)!=self.game.expected_stones:return
        player=self.game.players[self.game.current_color];moves=self.selected[:];self.selected.clear()
        try:self.game.submit_turn(moves);self.last_var.set(f"{player.name}：{'、'.join(format_position(p) for p in moves)}")
        except (ValueError,TimeoutError) as exc:self.last_var.set(str(exc))
        self.confirm_button.configure(state="disabled");self.draw()
        if self.game.status!=GameStatus.RUNNING:self.finish()
        else:self.game.start_current_clock();self.after(self.THINK_DELAY_MS,self.advance)

    def clear_selection(self):self.selected.clear();self.confirm_button.configure(state="disabled");self.draw()

    def advance(self):
        if not self.running or self.game.status!=GameStatus.RUNNING or self.is_human_turn() or self.thinking:return
        self.thinking=True;player=self.game.players[self.game.current_color];board=self.game.board.copy();count=self.game.expected_stones;remaining=self.game.clocks[self.game.current_color].remaining()
        def work():
            try:self.worker_results.put(("ok",player,player.choose_turn(board,count,remaining)))
            except Exception as exc:self.worker_results.put(("error",player,exc))
        threading.Thread(target=work,daemon=True).start();self.after(50,self.poll_worker)

    def poll_worker(self):
        try:kind,player,value=self.worker_results.get_nowait()
        except queue.Empty:
            if self.game.check_timeout():self.finish()
            elif self.thinking:self.after(50,self.poll_worker)
            return
        self.thinking=False
        if kind=="error":self.last_var.set(f"程序错误：{value}");self.game.clocks[self.game.current_color].remaining_seconds=0;self.game.check_timeout()
        else:
            try:self.game.submit_turn(value);self.last_var.set(f"{player.name}：{'、'.join(format_position(p) for p in value)}")
            except (ValueError,TimeoutError) as exc:self.last_var.set(f"提交失败：{exc}")
        self.draw()
        if self.game.status!=GameStatus.RUNNING:self.finish()
        else:self.game.start_current_clock();self.after(self.THINK_DELAY_MS,self.advance)

    def tick(self):
        if self.running and self.game.status==GameStatus.RUNNING and self.game.check_timeout():self.finish()
        self.update_labels();self.after(100,self.tick)

    def update_labels(self):
        self.black_var.set(f"● 黑方：{self.game.players[BLACK].name}\n剩余 {self.game.clocks[BLACK].remaining():.1f} 秒")
        self.white_var.set(f"○ 白方：{self.game.players[WHITE].name}\n剩余 {self.game.clocks[WHITE].remaining():.1f} 秒")
        if self.game.status==GameStatus.RUNNING:self.status_var.set(f"第 {self.game.turn_number} 回合\n轮到：{COLOR_NAMES[self.game.current_color]}\n本回合：{self.game.expected_stones} 子")
        elif self.game.status==GameStatus.DRAW:self.status_var.set("比赛结束：和棋")
        else:self.status_var.set(f"比赛结束\n{COLOR_NAMES[self.game.winner]}获胜（{'超时' if self.game.status==GameStatus.TIMEOUT else '六子连线'}）")

    def finish(self):
        if not self.running:return
        self.running=False;self.draw();path=save_game(self.game)
        for player in self.game.players.values():
            if isinstance(player,RemotePlayer):
                try:player.send_result({"type":"GAME_OVER","status":self.game.status.value,"winner":COLOR_NAMES.get(self.game.winner,"DRAW")})
                except Exception:pass
        messagebox.showinfo("比赛结束",f"{self.status_var.get()}\n棋谱已保存：{path}")

    def toggle(self):
        if self.game.status!=GameStatus.RUNNING:return
        if self.running:self.game.clocks[self.game.current_color].stop();self.running=False;self.last_var.set("比赛已暂停")
        else:self.running=True;self.game.start_current_clock();self.last_var.set("比赛继续");self.after(self.THINK_DELAY_MS,self.advance)

    def save(self):messagebox.showinfo("保存成功",str(save_game(self.game)))
    def leave(self):self.running=False;self.game.clocks[self.game.current_color].stop();self.on_exit()
