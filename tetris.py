

import tkinter as tk
import random
import time

CELL = 30
COLUMNS = 10
ROWS = 20
WIDTH = CELL * COLUMNS
HEIGHT = CELL * ROWS
SIDEBAR = 6 * CELL

SHAPES = {
    'I': [[1, 1, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
}

COLORS = {
    'I': '#00ffff',
    'J': '#0000ff',
    'L': '#ff7f00',
    'O': '#ffff00',
    'S': '#00ff00',
    'T': '#800080',
    'Z': '#ff0000',
    None: '#111111'
}

SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

def rotate(shape):
    # rotate clockwise: transpose + reverse rows
    return [list(row) for row in zip(*shape[::-1])]

class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.x = COLUMNS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = rotate(self.shape)

    def width(self):
        return len(self.shape[0])

    def height(self):
        return len(self.shape)

class Tetris:
    def __init__(self, root):
        self.root = root
        root.title('Tetris - Python 3.12')
        self.canvas = tk.Canvas(root, width=WIDTH + SIDEBAR, height=HEIGHT, bg='black')
        self.canvas.pack()
        self.board = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.drop_interval = 700  # ms
        self.paused = False
        self.game_over = False

        self.next_piece = self.random_piece()
        self.curr = self.spawn_piece()
        self.last_drop_time = time.time()
        self.fast_down = False

        self.draw_static()
        self.bind_keys()
        self.tick()

    def random_piece(self):
        return Piece(random.choice(list(SHAPES.keys())))

    def spawn_piece(self):
        p = self.next_piece
        self.next_piece = self.random_piece()
        p.x = COLUMNS // 2 - len(p.shape[0]) // 2
        p.y = 0
        if self.check_collision(p, dx=0, dy=0):
            self.game_over = True
        return p

    def check_collision(self, piece, dx=0, dy=0, shape=None):
        if shape is None:
            shape = piece.shape
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if not val:
                    continue
                x = piece.x + c + dx
                y = piece.y + r + dy
                if x < 0 or x >= COLUMNS or y >= ROWS:
                    return True
                if y >= 0 and self.board[y][x] is not None:
                    return True
        return False

    def lock_piece(self, piece):
        for r, row in enumerate(piece.shape):
            for c, val in enumerate(row):
                if not val:
                    continue
                x = piece.x + c
                y = piece.y + r
                if 0 <= y < ROWS and 0 <= x < COLUMNS:
                    self.board[y][x] = piece.kind
        self.clear_lines()
        self.curr = self.spawn_piece()

    def clear_lines(self):
        new_board = []
        cleared = 0
        for row in self.board:
            if all(cell is not None for cell in row):
                cleared += 1
            else:
                new_board.append(row)
        for _ in range(cleared):
            new_board.insert(0, [None for _ in range(COLUMNS)])
        self.board = new_board
        if cleared:
            self.lines += cleared
            self.score += SCORES.get(cleared, 0) * self.level
            # level up every 10 lines
            new_level = self.lines // 10 + 1
            if new_level > self.level:
                self.level = new_level
                self.drop_interval = max(80, int(self.drop_interval * 0.85))

    def move(self, dx):
        if not self.check_collision(self.curr, dx=dx, dy=0):
            self.curr.x += dx

    def soft_drop(self):
        if not self.check_collision(self.curr, dx=0, dy=1):
            self.curr.y += 1
            self.score += 1  # small reward
            return True
        else:
            self.lock_piece(self.curr)
            return False

    def hard_drop(self):
        while not self.check_collision(self.curr, dx=0, dy=1):
            self.curr.y += 1
            self.score += 2
        self.lock_piece(self.curr)

    def rotate_piece(self):
        original = [row[:] for row in self.curr.shape]
        newshape = rotate(self.curr.shape)
        # try kicks: 0, +1, -1, +2, -2
        for kick in (0, 1, -1, 2, -2):
            if not self.check_collision(self.curr, dx=kick, dy=0, shape=newshape):
                self.curr.shape = newshape
                self.curr.x += kick
                return
        # otherwise keep original
        self.curr.shape = original

    def tick(self):
        if not self.paused and not self.game_over:
            now = time.time()
            interval = self.drop_interval / 1000.0
            if self.fast_down:
                interval = 0.02
            if now - self.last_drop_time >= interval:
                self.last_drop_time = now
                if not self.soft_drop():
                    pass
        self.draw()
        if self.game_over:
            self.draw_game_over()
        self.root.after(16, self.tick)  # ~60fps draw

    def draw_static(self):
        # border
        x0 = WIDTH
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, outline='#333', width=2)
        # sidebar background
        self.canvas.create_rectangle(WIDTH, 0, WIDTH + SIDEBAR, HEIGHT, fill='#111', outline='#111')

    def draw(self):
        self.canvas.delete('cells')
        # draw board
        for r in range(ROWS):
            for c in range(COLUMNS):
                kind = self.board[r][c]
                x1 = c * CELL
                y1 = r * CELL
                x2 = x1 + CELL
                y2 = y1 + CELL
                color = COLORS[kind]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#222', tags='cells')

        # draw current piece
        for r, row in enumerate(self.curr.shape):
            for c, val in enumerate(row):
                if not val: continue
                x = (self.curr.x + c) * CELL
                y = (self.curr.y + r) * CELL
                if y + CELL < 0:
                    continue
                self.canvas.create_rectangle(x, y, x + CELL, y + CELL, fill=COLORS[self.curr.kind], outline='#222', tags='cells')

        # grid lines
        for i in range(ROWS + 1):
            self.canvas.create_line(0, i * CELL, WIDTH, i * CELL, fill='#0b0b0b', tags='cells')
        for j in range(COLUMNS + 1):
            self.canvas.create_line(j * CELL, 0, j * CELL, HEIGHT, fill='#0b0b0b', tags='cells')

        # sidebar info
        sx = WIDTH + 10
        sy = 10
        self.canvas.create_text(sx, sy, anchor='nw', text=f"Score: {self.score}", fill='white', font=('Arial', 14), tags='cells')
        self.canvas.create_text(sx, sy + 30, anchor='nw', text=f"Lines: {self.lines}", fill='white', font=('Arial', 14), tags='cells')
        self.canvas.create_text(sx, sy + 60, anchor='nw', text=f"Level: {self.level}", fill='white', font=('Arial', 14), tags='cells')

        # next piece preview
        self.canvas.create_text(sx, sy + 110, anchor='nw', text="Next:", fill='white', font=('Arial', 12), tags='cells')
        self.draw_preview(self.next_piece, sx + 8, sy + 140)

        # controls
        ctrl_text = "Controls:\n← → Move\n↑ Rotate\n↓ Soft drop\nSpace Hard drop\nP Pause\nR Restart"
        self.canvas.create_text(sx, sy + 260, anchor='nw', text=ctrl_text, fill='white', font=('Arial', 10), tags='cells')

        if self.paused:
            self.canvas.create_text(WIDTH//2, HEIGHT//2, text="PAUSED", fill='white', font=('Arial', 36), tags='cells')

    def draw_preview(self, piece, sx, sy):
        # center preview
        shape = piece.shape
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if not val: continue
                x1 = sx + c * (CELL // 1)
                y1 = sy + r * (CELL // 1)
                x2 = x1 + CELL
                y2 = y1 + CELL
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS[piece.kind], outline='#222', tags='cells')

    def bind_keys(self):
        self.root.bind('<Left>', lambda e: self.key_move(-1))
        self.root.bind('<Right>', lambda e: self.key_move(1))
        self.root.bind('<Up>', lambda e: self.key_rotate())
        self.root.bind('<Down>', lambda e: self.key_soft())
        self.root.bind('<space>', lambda e: self.key_hard())
        self.root.bind('p', lambda e: self.key_pause())
        self.root.bind('P', lambda e: self.key_pause())
        self.root.bind('r', lambda e: self.restart())
        self.root.bind('R', lambda e: self.restart())
        # hold fast drop on keypress
        self.root.bind('<KeyPress-Down>', lambda e: self.set_fast(True))
        self.root.bind('<KeyRelease-Down>', lambda e: self.set_fast(False))

    def set_fast(self, val):
        self.fast_down = val

    def key_move(self, dx):
        if self.paused or self.game_over: return
        self.move(dx)

    def key_rotate(self):
        if self.paused or self.game_over: return
        self.rotate_piece()

    def key_soft(self):
        if self.paused or self.game_over: return
        self.soft_drop()

    def key_hard(self):
        if self.paused or self.game_over: return
        self.hard_drop()

    def key_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused

    def draw_game_over(self):
        self.canvas.create_rectangle(50, HEIGHT//2 - 60, WIDTH - 50, HEIGHT//2 + 60, fill='#000000aa', outline='')
        self.canvas.create_text(WIDTH//2, HEIGHT//2 - 10, text="GAME OVER", fill='red', font=('Arial', 30))
        self.canvas.create_text(WIDTH//2, HEIGHT//2 + 25, text=f"Score: {self.score}    Press R to restart", fill='white', font=('Arial', 12))

    def restart(self):
        self.board = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.drop_interval = 700
        self.next_piece = self.random_piece()
        self.curr = self.spawn_piece()
        self.paused = False
        self.game_over = False

if __name__ == '__main__':
    root = tk.Tk()
    game = Tetris(root)
    root.mainloop()
