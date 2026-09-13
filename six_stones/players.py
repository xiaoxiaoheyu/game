from __future__ import annotations

import random

from .board import Board, Position
from .constants import BOARD_SIZE, EMPTY, opponent
from .rules import DIRECTIONS, line_length


class Player:
    """所有棋手共有的姓名和开局后分配的颜色。"""

    def __init__(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("棋手名称不能为空")
        self.name = name
        self.color: int | None = None


class HumanPlayer(Player):
    """供界面识别真人回合的棋手类型。"""

    pass


class HeuristicPlayer(Player):
    """启发式电脑棋手：优先成六，其次封堵，再发展自身棋形。"""

    def candidate_positions(self, board: Board) -> list[Position]:
        """把搜索范围限制在已有棋子周围两格，兼顾速度和实用性。"""
        occupied = [
            (row, col)
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
            if board.get(row, col) != EMPTY
        ]
        if not occupied:
            return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

        # 六子棋的有效攻防通常发生在现有棋形附近，跳过远处无关空点。
        candidates: set[Position] = set()
        for row, col in occupied:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    pos = row + dr, col + dc
                    if board.is_empty(*pos):
                        candidates.add(pos)
        return list(candidates) or board.empty_positions()

    @staticmethod
    def positional_score(board: Board, pos: Position, color: int) -> float:
        """综合进攻长度、防守威胁和中心距离计算一个落点评分。"""
        # 分别模拟己方与对方落在这里，避免防守评分干扰进攻棋盘。
        trial = board.copy()
        trial.place(*pos, color)
        own = max(line_length(trial, pos, color, *direction) for direction in DIRECTIONS)
        foe = opponent(color)
        block_trial = board.copy()
        block_trial.place(*pos, foe)
        threat = max(
            line_length(block_trial, pos, foe, *direction)
            for direction in DIRECTIONS
        )
        center = BOARD_SIZE - (abs(pos[0] - 9) + abs(pos[1] - 9))

        # 越接近六连，权重增长越快；五连威胁会压过普通的进攻选择。
        own_weights = {1: 2, 2: 20, 3: 180, 4: 1800, 5: 30000, 6: 1_000_000}
        foe_weights = {1: 1, 2: 18, 3: 220, 4: 2400, 5: 100_000, 6: 900_000}
        return (
            own_weights.get(min(own, 6), 0)
            + foe_weights.get(min(threat, 6), 0)
            + center
            + random.random()
        )

    def choose_turn(self, board: Board, stone_count: int) -> list[Position]:
        """逐颗选择本回合落点；第二颗棋会看到第一颗的模拟结果。"""
        if self.color is None:
            raise RuntimeError("电脑棋手尚未分配黑白颜色")
        if stone_count not in (1, 2):
            raise ValueError("电脑每回合只能选择 1 或 2 颗棋子")
        result: list[Position] = []
        working = board.copy()
        for _ in range(min(stone_count, len(working.empty_positions()))):
            candidates = self.candidate_positions(working)
            move = max(
                candidates,
                key=lambda pos: self.positional_score(working, pos, self.color),
            )
            result.append(move)
            working.place(*move, self.color)
        return result
