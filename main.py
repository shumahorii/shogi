import pygame
import sys
from collections import defaultdict

pygame.init()

SQUARE_SIZE = 60
COLS, ROWS = 9, 9
BOARD_WIDTH = SQUARE_SIZE * COLS
BOARD_HEIGHT = SQUARE_SIZE * ROWS
MARGIN = 100
WIDTH = BOARD_WIDTH + MARGIN * 2
HEIGHT = BOARD_HEIGHT

WHITE = (245, 245, 220)
BLACK = (0, 0, 0)
LINE_COLOR = (80, 80, 80)
HIGHLIGHT_COLOR = (255, 255, 0)
SELECTED_COLOR = (200, 200, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("将棋ゲーム")
font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
font = pygame.font.Font(font_path, 28)

SENTE = "先手"
GOTE = "後手"
players = [SENTE, GOTE]
turn = 0
current_player = players[turn]

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

board = initial_board
selected = None
legal_moves = []
captured_pieces = {SENTE: defaultdict(int), GOTE: defaultdict(int)}
selected_piece_from_hand = None

# 成り関連処理
def can_promote(piece, player, from_row, to_row):
    promotable = ['歩', '香', '桂', '銀', '飛', '角']
    if piece not in promotable:
        return False
    enemy_zone = range(0, 3) if player == SENTE else range(6, 9)
    return from_row in enemy_zone or to_row in enemy_zone

def promote(piece):
    return {'歩': 'と', '香': '成香', '桂': '成桂', '銀': '成銀', '飛': '龍', '角': '馬'}.get(piece, piece)

def demote(piece):
    return {'と': '歩', '成香': '香', '成桂': '桂', '成銀': '銀', '龍': '飛', '馬': '角'}.get(piece, piece)

def in_bounds(r, c):
    return 0 <= r < 9 and 0 <= c < 9

def is_valid_target(r, c, player):
    if not in_bounds(r, c):
        return False
    target = board[r][c]
    return target is None or target['player'] != player

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

    if piece in ['歩', 'と']:
        add(row + direction, col)
    elif piece in ['香', '成香']:
        if piece == '香':
            slide(direction, 0)
        else:
            for dr, dc in [(direction, -1), (direction, 0), (direction, 1), (0, -1), (0, 1), (-direction, 0)]:
                add(row + dr, col + dc)
    elif piece in ['桂', '成桂']:
        if piece == '桂':
            for dr, dc in [(2*direction, -1), (2*direction, 1)]:
                add(row + dr, col + dc)
        else:
            for dr, dc in [(direction, -1), (direction, 0), (direction, 1), (0, -1), (0, 1), (-direction, 0)]:
                add(row + dr, col + dc)
    elif piece in ['銀', '成銀']:
        if piece == '銀':
            for dr, dc in [(direction, -1), (direction, 0), (direction, 1), (-direction, -1), (-direction, 1)]:
                add(row + dr, col + dc)
        else:
            for dr, dc in [(direction, -1), (direction, 0), (direction, 1), (0, -1), (0, 1), (-direction, 0)]:
                add(row + dr, col + dc)
    elif piece == '金':
        for dr, dc in [(direction, -1), (direction, 0), (direction, 1), (0, -1), (0, 1), (-direction, 0)]:
            add(row + dr, col + dc)
    elif piece == '角':
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            slide(dr, dc)
    elif piece == '馬':
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            add(row + dr, col + dc)
    elif piece == '飛':
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            slide(dr, dc)
    elif piece == '龍':
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            add(row + dr, col + dc)
    elif piece in ['王', '玉']:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr or dc:
                    add(row + dr, col + dc)
    return moves

def draw_board():
    screen.fill(WHITE)
    for r in range(ROWS):
        for c in range(COLS):
            x = MARGIN + c * SQUARE_SIZE
            y = r * SQUARE_SIZE
            pygame.draw.rect(screen, LINE_COLOR, (x, y, SQUARE_SIZE, SQUARE_SIZE), 1)

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
                screen.blit(text, text.get_rect(center=(x, y)))

def draw_highlights():
    for r, c in legal_moves:
        x = MARGIN + c * SQUARE_SIZE
        y = r * SQUARE_SIZE
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, (x, y, SQUARE_SIZE, SQUARE_SIZE))

def draw_captured_pieces(player, x_offset):
    y = 20
    screen.blit(font.render("自分" if player == SENTE else "相手", True, BLACK), (x_offset, y))
    y += 50
    # 表示順固定
    piece_order = ['歩', '香', '桂', '銀', '金', '角', '飛']
    for i, piece in enumerate(piece_order):
        count = captured_pieces[player][piece]
        if count == 0:
            continue
        rect = pygame.Rect(x_offset - 10, y + i*50 - 5, 100, 35)
        if player == SENTE and selected_piece_from_hand == piece:
            pygame.draw.rect(screen, SELECTED_COLOR, rect)
        text = font.render(f"{piece} x{count}", True, BLACK)
        screen.blit(text, (x_offset, y + i*50))

def check_hand_click(pos):
    x, y = pos
    base_x = WIDTH - MARGIN + 10
    base_y = 70
    piece_order = ['歩', '香', '桂', '銀', '金', '角', '飛']
    for i, piece in enumerate(piece_order):
        count = captured_pieces[SENTE][piece]
        if count == 0:
            continue
        rect = pygame.Rect(base_x - 10, base_y + i*50 - 5, 100, 35)
        if rect.collidepoint(x, y):
            return piece
    return None

def get_cell(pos):
    x, y = pos
    return y // SQUARE_SIZE, (x - MARGIN) // SQUARE_SIZE

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
                r, c = get_cell((x, y))
                if not in_bounds(r, c):
                    continue

                clicked_piece = check_hand_click((x, y))
                if clicked_piece:
                    selected_piece_from_hand = clicked_piece
                    selected = None
                    legal_moves = []
                    continue

                if selected_piece_from_hand:
                    if board[r][c] is None:
                        board[r][c] = {'player': SENTE, 'piece': selected_piece_from_hand}
                        captured_pieces[SENTE][selected_piece_from_hand] -= 1
                        selected_piece_from_hand = None
                        turn = 1
                        current_player = GOTE
                    continue

                if selected:
                    if (r, c) in legal_moves:
                        src_r, src_c = selected
                        moving = board[src_r][src_c]
                        if board[r][c] and board[r][c]['player'] != current_player:
                            base = demote(board[r][c]['piece'])  # 成った駒を戻して持ち駒に
                            captured_pieces[current_player][base] += 1
                        if can_promote(moving['piece'], current_player, src_r, r):
                            moving['piece'] = promote(moving['piece'])
                        board[r][c] = moving
                        board[src_r][src_c] = None
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
        draw_captured_pieces(GOTE, 30)
        draw_captured_pieces(SENTE, WIDTH - MARGIN + 10)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
