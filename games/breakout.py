"""
블럭깨기 (Breakout) 게임
- tkinter만 사용 (외부 라이브러리 불필요)
- 조작: 마우스 이동 또는 좌우 방향키로 패들 이동, 스페이스바로 시작/일시정지
"""

import tkinter as tk
import random

WIDTH = 600
HEIGHT = 650
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
BALL_SIZE = 12
BRICK_ROWS = 6
BRICK_COLS = 8
BRICK_HEIGHT = 24
BRICK_PADDING = 4
BRICK_TOP_OFFSET = 60

BRICK_COLORS = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"]


class Ball:
    def __init__(self, canvas, x, y, radius, color, speed):
        self.canvas = canvas
        self.radius = radius
        self.id = canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius, fill=color, outline=""
        )
        self.dx = speed
        self.dy = -speed

    def pos(self):
        return self.canvas.coords(self.id)

    def move(self):
        self.canvas.move(self.id, self.dx, self.dy)

    def bounce_x(self):
        self.dx *= -1

    def bounce_y(self):
        self.dy *= -1


class Paddle:
    def __init__(self, canvas, x, y, width, height, color):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.id = canvas.create_rectangle(
            x - width / 2, y - height / 2, x + width / 2, y + height / 2,
            fill=color, outline=""
        )

    def pos(self):
        return self.canvas.coords(self.id)

    def move_to(self, x):
        coords = self.pos()
        half = self.width / 2
        x = max(half, min(WIDTH - half, x))
        current_center = (coords[0] + coords[2]) / 2
        self.canvas.move(self.id, x - current_center, 0)

    def move_by(self, dx):
        coords = self.pos()
        new_left = coords[0] + dx
        new_right = coords[2] + dx
        if new_left < 0:
            dx = -coords[0]
        elif new_right > WIDTH:
            dx = WIDTH - coords[2]
        self.canvas.move(self.id, dx, 0)


class BreakoutGame:
    def __init__(self, root):
        self.root = root
        self.root.title("블럭깨기")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#1e1e2e", highlightthickness=0)
        self.canvas.pack()

        self.lives = 3
        self.score = 0
        self.level = 1
        self.running = False
        self.game_over = False

        self.paddle = Paddle(self.canvas, WIDTH / 2, HEIGHT - 40, PADDLE_WIDTH, PADDLE_HEIGHT, "#f5f5f5")
        self.ball = None
        self.bricks = {}

        self.status_text = self.canvas.create_text(
            10, 10, anchor="nw", fill="white", font=("Helvetica", 14),
            text=self.status_string()
        )

        self.message_text = self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2, fill="white",
            font=("Helvetica", 20, "bold"),
            text="스페이스바를 눌러 시작하세요"
        )

        self.build_bricks()
        self.reset_ball()

        self.canvas.bind_all("<space>", self.toggle_running)
        self.canvas.bind_all("<Left>", lambda e: self.paddle.move_by(-30))
        self.canvas.bind_all("<Right>", lambda e: self.paddle.move_by(30))
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.update()

    def status_string(self):
        return f"점수: {self.score}   목숨: {self.lives}   레벨: {self.level}"

    def build_bricks(self):
        for item_id in self.bricks:
            self.canvas.delete(item_id)
        self.bricks = {}

        total_padding = BRICK_PADDING * (BRICK_COLS + 1)
        brick_width = (WIDTH - total_padding) / BRICK_COLS

        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x1 = BRICK_PADDING + col * (brick_width + BRICK_PADDING)
                y1 = BRICK_TOP_OFFSET + row * (BRICK_HEIGHT + BRICK_PADDING)
                x2 = x1 + brick_width
                y2 = y1 + BRICK_HEIGHT
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                brick_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#1e1e2e")
                self.bricks[brick_id] = 10 * (BRICK_ROWS - row)

    def reset_ball(self):
        if self.ball:
            self.canvas.delete(self.ball.id)
        speed = 4 + (self.level - 1) * 0.5
        self.ball = Ball(self.canvas, WIDTH / 2, HEIGHT - 60, BALL_SIZE / 2, "#f5f5f5", speed)

    def on_mouse_move(self, event):
        self.paddle.move_to(event.x)

    def toggle_running(self, event=None):
        if self.game_over:
            self.restart()
            return
        self.running = not self.running
        if self.running:
            self.canvas.itemconfig(self.message_text, text="")
        else:
            self.canvas.itemconfig(self.message_text, text="일시정지 (스페이스바)")

    def restart(self):
        self.lives = 3
        self.score = 0
        self.level = 1
        self.game_over = False
        self.running = False
        self.build_bricks()
        self.reset_ball()
        self.canvas.itemconfig(self.status_text, text=self.status_string())
        self.canvas.itemconfig(self.message_text, text="스페이스바를 눌러 시작하세요")

    def check_collisions(self):
        bx1, by1, bx2, by2 = self.ball.pos()

        if bx1 <= 0 or bx2 >= WIDTH:
            self.ball.bounce_x()
        if by1 <= 0:
            self.ball.bounce_y()

        if by2 >= HEIGHT:
            self.lives -= 1
            self.canvas.itemconfig(self.status_text, text=self.status_string())
            if self.lives <= 0:
                self.end_game(False)
            else:
                self.running = False
                self.reset_ball()
                self.canvas.itemconfig(self.message_text, text="스페이스바를 눌러 계속하세요")
            return

        px1, py1, px2, py2 = self.paddle.pos()
        if bx2 >= px1 and bx1 <= px2 and by2 >= py1 and by1 <= py2 and self.ball.dy > 0:
            paddle_center = (px1 + px2) / 2
            ball_center = (bx1 + bx2) / 2
            offset = (ball_center - paddle_center) / ((px2 - px1) / 2)
            speed = (self.ball.dx ** 2 + self.ball.dy ** 2) ** 0.5
            self.ball.dx = speed * offset
            self.ball.dy = -abs(self.ball.dy)

        hit_id = None
        for brick_id in list(self.bricks.keys()):
            bx = self.canvas.coords(brick_id)
            if not bx:
                continue
            if bx2 >= bx[0] and bx1 <= bx[2] and by2 >= bx[1] and by1 <= bx[3]:
                hit_id = brick_id
                break

        if hit_id is not None:
            self.score += self.bricks[hit_id]
            self.canvas.delete(hit_id)
            del self.bricks[hit_id]
            self.canvas.itemconfig(self.status_text, text=self.status_string())
            self.ball.bounce_y()

            if not self.bricks:
                self.level += 1
                self.build_bricks()
                self.reset_ball()
                self.running = False
                self.canvas.itemconfig(self.message_text, text=f"레벨 {self.level}! 스페이스바를 눌러 계속하세요")

    def end_game(self, won):
        self.running = False
        self.game_over = True
        text = "승리했습니다!" if won else "게임 오버"
        self.canvas.itemconfig(
            self.message_text,
            text=f"{text}  최종 점수: {self.score}\n스페이스바를 눌러 다시 시작"
        )

    def update(self):
        if self.running and not self.game_over:
            self.ball.move()
            self.check_collisions()
        self.root.after(16, self.update)


def main():
    root = tk.Tk()
    BreakoutGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
