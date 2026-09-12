import json
import socket
import threading
import unittest

from six_stones.board import Board
from six_stones.constants import WHITE
from six_stones.network import JsonLineConnection, RemotePlayer


class NetworkProtocolTest(unittest.TestCase):
    def test_remote_player_handshake_and_turn(self):
        server_socket, client_socket = socket.socketpair()
        remote = RemotePlayer("对方程序", JsonLineConnection(server_socket))
        received = []

        def client():
            reader = client_socket.makefile("r", encoding="utf-8")
            writer = client_socket.makefile("w", encoding="utf-8")
            received.append(json.loads(reader.readline()))
            received.append(json.loads(reader.readline()))
            writer.write(json.dumps({"type": "TURN", "moves": ["J10", "K10"]}) + "\n")
            writer.flush()

        worker = threading.Thread(target=client)
        worker.start()
        remote.on_game_start(WHITE)
        moves = remote.choose_turn(Board(), 2, 5)
        worker.join(timeout=2)
        self.assertEqual(moves, [(9, 9), (9, 10)])
        self.assertEqual(received[0]["type"], "GAME_START")
        self.assertEqual(received[1]["type"], "YOUR_TURN")
        remote.connection.close()
        client_socket.close()


if __name__ == "__main__":
    unittest.main()
