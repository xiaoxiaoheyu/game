from __future__ import annotations

from dataclasses import dataclass, field

from .constants import BOARD_SIZE, EMPTY


Position = tuple[int, int]


@dataclass
class Board:
    grid: list[list[int]] = field(
        default_factory=lambda: [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    )

    def copy(self) -> "Board":
        return Board([row[:] for row in self.grid])

    @staticmethod
    def inside(row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get(self, row: int, col: int) -> int:
        return self.grid[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        return self.inside(row, col) and self.grid[row][col] == EMPTY

    def place(self, row: int, col: int, color: int) -> None:
        if not self.is_empty(row, col):
            raise ValueError(f"位置 {format_position((row, col))} 已被占用或越界")
        self.grid[row][col] = color

    def empty_positions(self) -> list[Position]:
        return [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if self.grid[r][c] == EMPTY
        ]

    def is_full(self) -> bool:
        return not any(EMPTY in row for row in self.grid)


def parse_position(text: str) -> Position:
    value = text.strip().upper()
    if len(value) < 2 or not value[0].isalpha() or not value[1:].isdigit():
        raise ValueError("坐标格式应为 A1 到 S19")
    col = ord(value[0]) - ord("A")
    row = int(value[1:]) - 1
    if not Board.inside(row, col):
        raise ValueError("坐标超出 A1 到 S19")
    return row, col


def format_position(position: Position) -> str:
    row, col = position
    return f"{chr(ord('A') + col)}{row + 1}"

