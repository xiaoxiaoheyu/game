from __future__ import annotations

import json
import socket
import threading
from queue import Queue

from .board import Board, Position, format_position, parse_position
from .constants import BLACK, COLOR_NAMES
from .players import Player


class JsonLineConnection:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.reader = sock.makefile("r", encoding="utf-8", newline="\n")
        self.writer = sock.makefile("w", encoding="utf-8", newline="\n")
        self.lock = threading.Lock()

    def send(self, payload: dict) -> None:
        with self.lock:
            self.writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.writer.flush()

    def receive(self, timeout: float | None = None) -> dict:
        self.sock.settimeout(timeout)
        line = self.reader.readline()
        if not line:
            raise ConnectionError("对方程序已断开连接")
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("协议消息必须是 JSON 对象")
        return value

    def close(self) -> None:
        try:
            self.reader.close(); self.writer.close()
        finally:
            self.sock.close()


class RemotePlayer(Player):
    """Opponent adapter for the documented JSON-line competition protocol."""

    def __init__(self, name: str, connection: JsonLineConnection):
        super().__init__(name)
        self.connection = connection

    def on_game_start(self, color: int) -> None:
        super().on_game_start(color)
        self.connection.send({
            "type": "GAME_START", "color": "BLACK" if color == BLACK else "WHITE",
            "board_size": 19, "win_length": 6, "first_turn_stones": 1,
        })

    def on_opponent_turn(self, moves: list[Position]) -> None:
        self.connection.send({"type": "OPPONENT_TURN", "moves": [format_position(p) for p in moves]})

    def choose_turn(self, board: Board, stone_count: int, time_left: float) -> list[Position]:
        self.connection.send({"type": "YOUR_TURN", "stones": stone_count, "time_left": round(time_left, 3)})
        message = self.connection.receive(timeout=max(0.1, time_left))
        if message.get("type") != "TURN" or not isinstance(message.get("moves"), list):
            raise ValueError("对方程序应发送 {type: TURN, moves: [...]} 消息")
        return [parse_position(value) for value in message["moves"]]

    def send_result(self, payload: dict) -> None:
        self.connection.send(payload)


def listen_once(host: str, port: int, events: Queue, stop: threading.Event) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((host, port)); server.listen(1); server.settimeout(0.5)
        events.put(("listening", f"正在监听 {host}:{port}"))
        while not stop.is_set():
            try:
                client, address = server.accept()
                events.put(("connected", JsonLineConnection(client), address))
                return
            except socket.timeout:
                continue
    except Exception as exc:
        events.put(("error", str(exc)))
    finally:
        server.close()
