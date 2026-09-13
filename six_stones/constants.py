BOARD_SIZE = 19
WIN_LENGTH = 6
EMPTY = 0
BLACK = 1
WHITE = 2

COLOR_NAMES = {BLACK: "黑方", WHITE: "白方"}


def opponent(color: int) -> int:
    """返回另一方颜色；拒绝把空位或任意整数当成棋子颜色。"""
    if color == BLACK:
        return WHITE
    if color == WHITE:
        return BLACK
    raise ValueError(f"无效的棋子颜色：{color}")
