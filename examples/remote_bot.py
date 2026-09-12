"""连接比赛配置界面的最小对手程序示例。"""
from __future__ import annotations

import argparse
import json
import socket

from six_stones.board import Board, format_position, parse_position
from six_stones.constants import BLACK, WHITE
from six_stones.players import HeuristicPlayer


def send(writer, payload):
    writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
    writer.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    sock = socket.create_connection((args.host, args.port))
    reader = sock.makefile("r", encoding="utf-8")
    writer = sock.makefile("w", encoding="utf-8")
    board = Board()
    bot = HeuristicPlayer("远程示例程序")
    for line in reader:
        message = json.loads(line)
        kind = message.get("type")
        if kind == "GAME_START":
            bot.on_game_start(BLACK if message["color"] == "BLACK" else WHITE)
        elif kind == "OPPONENT_TURN":
            foe = WHITE if bot.color == BLACK else BLACK
            for text in message["moves"]:
                board.place(*parse_position(text), foe)
        elif kind == "YOUR_TURN":
            moves = bot.choose_turn(board, message["stones"], message["time_left"])
            send(writer, {"type": "TURN", "moves": [format_position(p) for p in moves]})
            for position in moves:
                board.place(*position, bot.color)
        elif kind == "GAME_OVER":
            break


if __name__ == "__main__":
    main()
