from __future__ import annotations

from dataclasses import dataclass, field

from .constants import BLACK, BOARD_SIZE, EMPTY, WHITE


Position = tuple[int, int]


@dataclass
class Board:
    grid: list[list[int]] = field(
        default_factory=lambda: [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    )

    def __post_init__(self) -> None:
        """确保外部传入的棋盘仍符合 19×19 和合法棋值约束。"""
        if len(self.grid) != BOARD_SIZE or any(
            len(row) != BOARD_SIZE for row in self.grid
        ):
            raise ValueError(f"棋盘必须是 {BOARD_SIZE}×{BOARD_SIZE}")
        valid_values = {EMPTY, BLACK, WHITE}
        if any(cell not in valid_values for row in self.grid for cell in row):
            raise ValueError("棋盘只能包含空位、黑棋或白棋")

    def copy(self) -> "Board":
        """建立深拷贝，避免试下棋时修改真实棋盘。"""
        return Board([row[:] for row in self.grid])

    @staticmethod
    def inside(row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get(self, row: int, col: int) -> int:
        if not self.inside(row, col):
            raise ValueError(f"位置 {format_position((row, col))} 超出棋盘")
        return self.grid[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        return self.inside(row, col) and self.grid[row][col] == EMPTY

    def place(self, row: int, col: int, color: int) -> None:
        """在空交叉点落一颗合法颜色的棋子。"""
        if color not in (BLACK, WHITE):
            raise ValueError(f"无效的棋子颜色：{color}")
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
    """把 A1～S19 的用户坐标转换为从零开始的行列坐标。"""
    if not isinstance(text, str):
        raise ValueError("坐标必须是 A1 到 S19 格式的文本")
    value = text.strip().upper()
    if len(value) < 2 or not value[0].isalpha() or not value[1:].isdigit():
        raise ValueError("坐标格式应为 A1 到 S19")
    col = ord(value[0]) - ord("A")
    row = int(value[1:]) - 1
    if not Board.inside(row, col):
        raise ValueError("坐标超出 A1 到 S19")
    return row, col


def format_position(position: Position) -> str:
    """生成便于显示的坐标；越界值仍会如实显示以帮助定位错误。"""
    row, col = position
    return f"{chr(ord('A') + col)}{row + 1}"
