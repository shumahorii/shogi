import pygame
import sys
from collections import defaultdict

# Pygame初期化
pygame.init()

# 定数定義
SQUARE_SIZE = 60
COLS, ROWS = 9, 9
BOARD_WIDTH = SQUARE_SIZE * COLS
BOARD_HEIGHT = SQUARE_SIZE * ROWS
MARGIN = 100
WIDTH = BOARD_WIDTH + MARGIN * 2
HEIGHT = BOARD_HEIGHT

# 色定義
WHITE = (245, 245, 220)
BLACK = (0, 0, 0)
LINE_COLOR = (80, 80, 80)
HIGHLIGHT_COLOR = (255, 255, 0)
SELECTED_COLOR = (200, 200, 255)

# ウィンドウとフォント設定
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("将棋ゲーム")
font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
font = pygame.font.Font(font_path, 28)

# プレイヤー定義
SENTE = "先手"
GOTE = "後手"
players = [SENTE, GOTE]
turn = 0
current_player = players[turn]

# 初期盤面
initial_board = [
    [{'player': GOTE, 'piece': p} for p in ['香', '桂', '銀', '金', '玉', '金', '銀', '桂', '香']],
    [None, {'player': GOTE, 'piece': '飛'}, None, None, None, None, None, {'player': GOTE, 'piece': '角'}, None],
    [{'player': GOTE, 'piece': '歩'} for _ in range(9)],
    [None] * 9,
    [None] * 9,
    [None] * 9,
    [{'player': SENTE, 'piece': '歩'} for _ in range(9)],
    [None, {'player': SENTE, 'piece': '角'}, None, None, None, None, None, {'player': SENTE, 'piece': '飛'}, None],
    [{'player': SENTE, 'piece': p} for p in ['香', '桂', '銀', '金', '王', '金', '銀', '桂', '香']],
]

# グローバル状態
board = initial_board
selected = None
legal_moves = []
captured_pieces = {SENTE: defaultdict(int), GOTE: defaultdict(int)}
selected_piece_from_hand = None

# 範囲チェック
def in_bounds(r, c):
    return 0 <= r < 9 and 0 <= c < 9

# 移動先が空または敵の駒か
def is_valid_target(r, c, player):
    if not in_bounds(r, c):
        return False
    cell = board[r][c]
    return cell is None or cell['player'] != player

# 駒の移動ルール
def get_legal_moves(row, col):
    cell = board[row][col]
    if not cell:
        return []
    piece = cell['piece']
    player = cell['player']
    direction = -1 if player == SENTE else 1
    moves = []

    def add(r, c):
        if is_valid_target(r, c, player):
            moves.append((r, c))

    def slide(dr, dc):
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            if board[r][c] is None:
                moves.append((r, c))
            elif board[r][c]['player'] != player:
                moves.append((r, c))
                break
            else:
                break
            r += dr
            c += dc

    if piece == '歩':
        add(row + direction, col)
    elif piece == '香':
        slide(direction, 0)
    elif piece == '桂':
        for dr, dc in [(2*direction, -1), (2*direction, 1)]:
            add(row + dr, col + dc)
    elif piece == '銀':
        for dr, dc in [(direction, -1), (direction, 0), (direction, 1),
                       (-direction, -1), (-direction, 1)]:
            add(row + dr, col + dc)
    elif piece == '金' or piece == 'と':
        for dr, dc in [(direction, -1), (direction, 0), (direction, 1),
                       (0, -1), (0, 1), (-direction, 0)]:
            add(row + dr, col + dc)
    elif piece == '角':
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            slide(dr, dc)
    elif piece == '飛':
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            slide(dr, dc)
    elif piece == '王' or piece == '玉':
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr or dc:
                    add(row + dr, col + dc)
    return moves

# 盤を描画（中央寄せ）
def draw_board():
    screen.fill(WHITE)
    for row in range(ROWS):
        for col in range(COLS):
            x = MARGIN + col * SQUARE_SIZE
            y = row * SQUARE_SIZE
            pygame.draw.rect(screen, LINE_COLOR, (x, y, SQUARE_SIZE, SQUARE_SIZE), 1)

# 駒の描画
def draw_pieces():
    for r in range(ROWS):
        for c in range(COLS):
            cell = board[r][c]
            if cell:
                text = font.render(cell['piece'], True, BLACK)
                if cell['player'] == GOTE:
                    text = pygame.transform.rotate(text, 180)
                x = MARGIN + c * SQUARE_SIZE + SQUARE_SIZE // 2
                y = r * SQUARE_SIZE + SQUARE_SIZE // 2
                rect = text.get_rect(center=(x, y))
                screen.blit(text, rect)

# 合法手を黄色で表示
def draw_highlights():
    for r, c in legal_moves:
        x = MARGIN + c * SQUARE_SIZE
        y = r * SQUARE_SIZE
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, (x, y, SQUARE_SIZE, SQUARE_SIZE))

# 持ち駒描画（左または右に表示）
def draw_captured_pieces(player, x_offset):
    y = 20  # ← ラベルのY位置を少し上に
    label = "自分" if player == SENTE else "相手"
    screen.blit(font.render(label, True, BLACK), (x_offset, y))

    y += 50  # ← ラベルと1つ目の駒の間のスペースを拡張

    for i, (piece, count) in enumerate(captured_pieces[player].items()):
        if count == 0:
            continue
        rect = pygame.Rect(x_offset - 10, y + i*50 - 5, 100, 35)  # ← i*50 に
        if player == SENTE and selected_piece_from_hand == piece:
            pygame.draw.rect(screen, SELECTED_COLOR, rect)
        text = font.render(f"{piece} x{count}", True, BLACK)
        screen.blit(text, (x_offset, y + i*50))  # ← i*50 に


# 持ち駒クリック判定（先手側のみ）
def check_hand_click(pos):
    x, y = pos
    base_x = WIDTH - MARGIN + 10
    base_y = 70
    for i, (piece, count) in enumerate(captured_pieces[SENTE].items()):
        if count == 0:
            continue
        rect = pygame.Rect(base_x - 10, base_y + i*40 - 5, 100, 35)
        if rect.collidepoint(x, y):
            return piece
    return None

# クリック位置からマス取得
def get_cell(pos):
    x, y = pos
    col = (x - MARGIN) // SQUARE_SIZE
    row = y // SQUARE_SIZE
    return row, col

# メインループ
def main():
    global selected, legal_moves, board, selected_piece_from_hand, turn, current_player
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                clicked_piece = check_hand_click((x, y))
                if clicked_piece:
                    selected = None
                    legal_moves = []
                    selected_piece_from_hand = clicked_piece
                    continue

                r, c = get_cell((x, y))
                if not in_bounds(r, c):
                    continue

                if selected_piece_from_hand:
                    if board[r][c] is None:
                        board[r][c] = {'player': SENTE, 'piece': selected_piece_from_hand}
                        captured_pieces[SENTE][selected_piece_from_hand] -= 1
                        selected_piece_from_hand = None
                        turn = (turn + 1) % 2
                        current_player = players[turn]
                    continue

                if selected:
                    if (r, c) in legal_moves:
                        target = board[r][c]
                        if target and target['player'] != current_player:
                            captured_pieces[current_player][target['piece']] += 1
                        board[r][c] = board[selected[0]][selected[1]]
                        board[selected[0]][selected[1]] = None
                        selected = None
                        legal_moves = []
                        turn = (turn + 1) % 2
                        current_player = players[turn]
                    elif board[r][c] and board[r][c]['player'] == current_player:
                        selected = (r, c)
                        legal_moves = get_legal_moves(r, c)
                    else:
                        selected = None
                        legal_moves = []
                else:
                    if board[r][c] and board[r][c]['player'] == current_player:
                        selected = (r, c)
                        legal_moves = get_legal_moves(r, c)
                        selected_piece_from_hand = None

        draw_board()
        if selected:
            draw_highlights()
        draw_pieces()
        draw_captured_pieces(GOTE, 30)                  # 左側表示（後手）
        draw_captured_pieces(SENTE, WIDTH - MARGIN + 10) # 右側表示（先手）
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
