import pygame
import random
import sys

pygame.init()

# 화면 설정
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 120, 0)
CYAN = (0, 200, 220)
DARK_CYAN = (0, 120, 140)
RED = (200, 0, 0)
GRAY = (40, 40, 40)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

BASE_SPEED = 8

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("뱀 게임 - 사람 vs AI")
clock = pygame.time.Clock()

korean_font_path = pygame.font.match_font("applesdgothicneo") or pygame.font.match_font("applegothic")
if korean_font_path:
    font = pygame.font.Font(korean_font_path, 32)
    small_font = pygame.font.Font(korean_font_path, 22)
else:
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 26)


def add(pos, direction):
    return (pos[0] + direction[0], pos[1] + direction[1])


def is_out_of_bounds(pos):
    return pos[0] < 0 or pos[0] >= GRID_WIDTH or pos[1] < 0 or pos[1] >= GRID_HEIGHT


def make_snake(start_pos, direction):
    return {
        "body": [start_pos],
        "direction": direction,
        "alive": True,
        "score": 0,
    }


def random_food_position(*bodies):
    occupied = set()
    for body in bodies:
        occupied.update(body)
    while True:
        pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if pos not in occupied:
            return pos


def ai_choose_direction(ai_snake, other_snake, food):
    head = ai_snake["body"][0]
    current_dir = ai_snake["direction"]
    reverse = (-current_dir[0], -current_dir[1])

    candidates = [d for d in DIRECTIONS if d != reverse]

    self_blocked = set(ai_snake["body"][:-1])
    other_blocked = set(other_snake["body"])

    safe = []
    for d in candidates:
        pos = add(head, d)
        if is_out_of_bounds(pos):
            continue
        if pos in self_blocked or pos in other_blocked:
            continue
        safe.append(d)

    if not safe:
        # 안전한 길이 없으면 그나마 벽/자기 몸은 피하는 방향을 시도
        for d in candidates:
            pos = add(head, d)
            if is_out_of_bounds(pos) or pos in self_blocked:
                continue
            safe.append(d)

    if not safe:
        safe = candidates if candidates else DIRECTIONS

    def distance(d):
        nx, ny = add(head, d)
        return abs(nx - food[0]) + abs(ny - food[1])

    best_dist = min(distance(d) for d in safe)
    best_candidates = [d for d in safe if distance(d) == best_dist]
    return random.choice(best_candidates)


def draw_grid():
    for x in range(0, SCREEN_WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))


def draw_cell(pos, color):
    rect = pygame.Rect(pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, color, rect)


def draw_snake(snake, head_color, body_color):
    for i, segment in enumerate(snake["body"]):
        draw_cell(segment, head_color if i == 0 else body_color)


def show_message(text, y_offset=0, use_font=None):
    use_font = use_font or font
    surface = use_font.render(text, True, WHITE)
    rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
    screen.blit(surface, rect)


def new_game():
    human = make_snake((GRID_WIDTH // 4, GRID_HEIGHT // 2), RIGHT)
    ai = make_snake((GRID_WIDTH * 3 // 4, GRID_HEIGHT // 2), LEFT)
    food = random_food_position(human["body"], ai["body"])
    return human, ai, food


def main():
    human, ai, food = new_game()
    game_over = False
    result_text = ""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                current_dir = human["direction"]
                if event.key == pygame.K_UP and current_dir != DOWN:
                    human["direction"] = UP
                elif event.key == pygame.K_DOWN and current_dir != UP:
                    human["direction"] = DOWN
                elif event.key == pygame.K_LEFT and current_dir != RIGHT:
                    human["direction"] = LEFT
                elif event.key == pygame.K_RIGHT and current_dir != LEFT:
                    human["direction"] = RIGHT
                elif event.key == pygame.K_r and game_over:
                    human, ai, food = new_game()
                    game_over = False
                    result_text = ""
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        if not game_over:
            ai["direction"] = ai_choose_direction(ai, human, food)

            human_new_head = add(human["body"][0], human["direction"])
            ai_new_head = add(ai["body"][0], ai["direction"])

            human_dead = False
            ai_dead = False

            if is_out_of_bounds(human_new_head) or human_new_head in human["body"][:-1]:
                human_dead = True
            if is_out_of_bounds(ai_new_head) or ai_new_head in ai["body"][:-1]:
                ai_dead = True

            if human_new_head in ai["body"]:
                human_dead = True
            if ai_new_head in human["body"]:
                ai_dead = True
            if human_new_head == ai_new_head:
                human_dead = True
                ai_dead = True

            if not human_dead:
                human["body"].insert(0, human_new_head)
                if human_new_head == food:
                    human["score"] += 1
                    food = random_food_position(human["body"], ai["body"])
                else:
                    human["body"].pop()

            if not ai_dead:
                ai["body"].insert(0, ai_new_head)
                if ai_new_head == food:
                    ai["score"] += 1
                    food = random_food_position(human["body"], ai["body"])
                else:
                    ai["body"].pop()

            human["alive"] = not human_dead
            ai["alive"] = not ai_dead

            if human_dead or ai_dead:
                game_over = True
                if human_dead and ai_dead:
                    if human["score"] > ai["score"]:
                        result_text = "둘 다 충돌! 점수로 당신 승리!"
                    elif human["score"] < ai["score"]:
                        result_text = "둘 다 충돌! 점수로 AI 승리!"
                    else:
                        result_text = "둘 다 충돌! 무승부!"
                elif human_dead:
                    result_text = "AI 승리!"
                else:
                    result_text = "당신 승리!"

        screen.fill(BLACK)
        draw_grid()
        draw_cell(food, RED)
        draw_snake(human, GREEN, DARK_GREEN)
        draw_snake(ai, CYAN, DARK_CYAN)

        human_score_surface = small_font.render(f"당신: {human['score']}", True, GREEN)
        ai_score_surface = small_font.render(f"AI: {ai['score']}", True, CYAN)
        screen.blit(human_score_surface, (10, 10))
        screen.blit(ai_score_surface, (SCREEN_WIDTH - ai_score_surface.get_width() - 10, 10))

        if game_over:
            show_message(result_text, -20)
            show_message("R키를 눌러 재시작, ESC로 종료", 20)

        pygame.display.flip()
        speed = BASE_SPEED + max(human["score"], ai["score"]) // 5
        clock.tick(speed)


if __name__ == "__main__":
    main()
