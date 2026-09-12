import unittest

from six_stones.board import Board, parse_position
from six_stones.constants import BLACK, WHITE
from six_stones.rules import commit_turn, has_won, validate_turn
from six_stones.game import Game, GameStatus
from six_stones.players import HeuristicPlayer


class RulesTest(unittest.TestCase):
    def test_coordinates(self):
        self.assertEqual(parse_position("A1"), (0, 0))
        self.assertEqual(parse_position("S19"), (18, 18))

    def test_six_and_long_line_win(self):
        board = Board()
        moves = [(9, c) for c in range(7)]
        board = commit_turn(board, moves, BLACK)
        self.assertTrue(has_won(board, BLACK, [moves[-1]]))

    def test_diagonal_win(self):
        board = commit_turn(Board(), [(i, i) for i in range(6)], WHITE)
        self.assertTrue(has_won(board, WHITE, [(5, 5)]))

    def test_atomic_validation_does_not_change_board(self):
        board = commit_turn(Board(), [(0, 0)], BLACK)
        with self.assertRaises(ValueError):
            validate_turn(board, [(1, 1), (0, 0)], 2)
        self.assertTrue(board.is_empty(1, 1))

    def test_automatic_match_finishes(self):
        game = Game(HeuristicPlayer("A"), HeuristicPlayer("B"), total_time=30)
        while game.status == GameStatus.RUNNING:
            game.start_current_clock()
            player = game.players[game.current_color]
            moves = player.choose_turn(game.board.copy(), game.expected_stones, 30)
            game.submit_turn(moves)
        self.assertIn(game.status, {GameStatus.BLACK_WIN, GameStatus.WHITE_WIN, GameStatus.DRAW})
        self.assertGreater(len(game.records), 0)


if __name__ == "__main__":
    unittest.main()
