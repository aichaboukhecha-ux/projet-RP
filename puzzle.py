
import pygame

from boxgame import Level, parse_board
from search import bfs


TILE_SIZE = 70
PANEL_WIDTH = 260
DELAY = 600


def draw_text(screen, font, text, x, y):
    image = font.render(text, True, (35, 42, 55))
    screen.blit(image, (x, y))


def draw_board(screen, state, font, cost, explored, step, total):

    screen.fill((245, 245, 245))
    
    for row in range(state.height):
        for col in range(state.width):

            rect = pygame.Rect(
                col * TILE_SIZE,
                row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE
            )

            position = (row, col)

            pygame.draw.rect(screen, (232, 235, 240), rect)

            if position in state.walls:
                pygame.draw.rect(screen, (65, 76, 94), rect)

            if position in state.targets:
                pygame.draw.circle(
                    screen,
                    (70, 170, 100),
                    rect.center,
                    TILE_SIZE // 6
                )


            pygame.draw.rect(screen, (200, 205, 215), rect, 1)

    for row, col in state.boxes:

        rect = pygame.Rect(
            col * TILE_SIZE + 9,
            row * TILE_SIZE + 9,
            TILE_SIZE - 18,
            TILE_SIZE - 18
        )

        pygame.draw.rect(
            screen, (205, 145, 75), rect, border_radius=8
        )

    row, col = state.player

    center = (
        col * TILE_SIZE + TILE_SIZE // 2,
        row * TILE_SIZE + TILE_SIZE // 2
    )

    pygame.draw.circle(
        screen, (55, 115, 210), center, TILE_SIZE // 3
    )

    panel_x = state.width * TILE_SIZE + 18

    draw_text(screen, font, "SOKOBAN", panel_x, 25)
    draw_text(screen, font, "Algorithm: BFS", panel_x, 75)
    draw_text(screen, font, f"Solution cost: {cost}", panel_x, 120)
    draw_text(screen, font, f"Explored nodes: {explored}", panel_x, 165)
    draw_text(screen, font, f"Move: {step}/{total}", panel_x, 210)

    if step == total:
        draw_text(screen, font, "Puzzle solved!", panel_x, 260)

    draw_text(screen, font, "SPACE: pause/resume", panel_x, 330)
    draw_text(screen, font, "R: restart", panel_x, 370)
    draw_text(screen, font, "ESC: quit", panel_x, 410)


def main():

    puzzle = parse_board(Level)
    goal_node, explored = bfs(puzzle)

    if goal_node is None:
        print("No solution exists.")
        return

    path = goal_node.getPath()
    cost = goal_node.g
    total = len(goal_node.getSolution())

    pygame.init()

    screen_width = puzzle.width * TILE_SIZE + PANEL_WIDTH
    screen_height = max(puzzle.height * TILE_SIZE, 480)

    screen = pygame.display.set_mode(
        (screen_width, screen_height)
    )

    pygame.display.set_caption("Sokoban - BFS Solver")

    font = pygame.font.SysFont(None, 27)
    clock = pygame.time.Clock()

    step = 0
    paused = False
    last_update = pygame.time.get_ticks()
    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    last_update = pygame.time.get_ticks()

                elif event.key == pygame.K_r:
                    step = 0
                    paused = False
                    last_update = pygame.time.get_ticks()

        now = pygame.time.get_ticks()

        if not paused and step < total:
            if now - last_update >= DELAY:
                step += 1
                last_update = now

        current_state = path[step]

        draw_board(
            screen,
            current_state,
            font,
            cost,
            explored,
            step,
            total
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
