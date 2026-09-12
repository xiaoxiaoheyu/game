BOARD_SIZE = 19
WIN_LENGTH = 6
EMPTY = 0
BLACK = 1
WHITE = 2

COLOR_NAMES = {BLACK: "黑方", WHITE: "白方"}


def opponent(color: int) -> int:
    return WHITE if color == BLACK else BLACK

