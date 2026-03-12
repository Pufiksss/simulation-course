import random
import sys

import pygame

CELL_SIZE = 8
COLS = 85
ROWS = 75
SCREEN_W = COLS * CELL_SIZE + 200
SCREEN_H = ROWS * CELL_SIZE

EMPTY = 0
TREE = 1
BURNING = 2
ASH = 3
WET = 4

COLORS = {
    EMPTY: (80, 60, 40),
    TREE: (34, 139, 34),
    BURNING: (220, 60, 0),
    ASH: (100, 100, 100),
    WET: (40, 100, 200),
}

P_GROW = 0.005
P_LIGHTNING = 0.00008
P_SPREAD = 0.4

wind_on = False
wind_dir = (0, 1)

rain_on = False
rain_timer = 0
wet_cells = set()


def make_grid():
    grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            if random.random() < 0.55:
                row.append(TREE)
            else:
                row.append(EMPTY)
        grid.append(row)
    return grid


def count_burning_neighbors(grid, r, c):
    count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr = r + dr
            nc = c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if grid[nr][nc] == BURNING:
                    if wind_on:
                        dot = dr * (-wind_dir[0]) + dc * (-wind_dir[1])
                        if dot > 0:
                            count += 3
                        elif dot < 0:
                            count += 0
                        else:
                            count += 1
                    else:
                        count += 1
    return count


def step(grid):
    new_grid = []
    for r in range(ROWS):
        new_row = []
        for c in range(COLS):
            cell = grid[r][c]

            if cell == EMPTY:
                if random.random() < P_GROW:
                    new_row.append(TREE)
                else:
                    new_row.append(EMPTY)

            elif cell == TREE or cell == WET:
                nb = count_burning_neighbors(grid, r, c)

                spread = P_SPREAD
                if cell == WET:
                    spread = P_SPREAD * 0.2

                p_catch = min(1.0, nb * spread)

                if random.random() < p_catch:
                    new_row.append(BURNING)
                elif cell == TREE and random.random() < P_LIGHTNING:
                    new_row.append(BURNING)
                else:
                    if rain_on and (r, c) in wet_cells:
                        new_row.append(WET)
                    elif cell == WET:
                        new_row.append(TREE)
                    else:
                        new_row.append(cell)

            elif cell == BURNING:
                new_row.append(ASH)

            elif cell == ASH:
                new_row.append(EMPTY)

            else:
                new_row.append(cell)

        new_grid.append(new_row)
    return new_grid


def update_rain():
    global wet_cells, rain_timer
    rain_timer += 1
    if rain_timer > 500:
        rain_timer = 0
        wet_cells = set()
        r0 = random.randint(0, ROWS - 1)
        c0 = random.randint(0, COLS - 1)
        rh = random.randint(5, 20)
        rw = random.randint(5, 20)
        for r in range(r0, min(ROWS, r0 + rh)):
            for c in range(c0, min(COLS, c0 + rw)):
                wet_cells.add((r, c))


def draw_grid(screen, grid):
    for r in range(ROWS):
        for c in range(COLS):
            color = COLORS[grid[r][c]]
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))

    if rain_on:
        for r, c in wet_cells:
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            pygame.draw.rect(
                screen, (30, 80, 220), (x, y, CELL_SIZE, CELL_SIZE), 2
            )


def draw_panel(screen, font, grid, gen, paused, speed):
    px = COLS * CELL_SIZE
    pygame.draw.rect(screen, (30, 30, 30), (px, 0, 200, SCREEN_H))

    trees = sum(row.count(TREE) + row.count(WET) for row in grid)
    burning = sum(row.count(BURNING) for row in grid)
    ash = sum(row.count(ASH) for row in grid)

    dir_names = {
        (-1, 0): "Север",
        (1, 0): "Юг",
        (0, -1): "Запад",
        (0, 1): "Восток",
    }
    dir_label = dir_names.get(wind_dir, "?")

    lines = [
        ("Лесной пожар", (255, 200, 50)),
        ("", None),
        (f"Шаг: {gen}", (200, 200, 200)),
        (f"Деревья: {trees}", (50, 200, 50)),
        (f"Горит:   {burning}", (220, 100, 0)),
        (f"Пепел:   {ash}", (150, 150, 150)),
        ("", None),
        (
            f"Ветер: {'ВКЛ' if wind_on else 'ВЫКЛ'}",
            (100, 180, 255) if wind_on else (150, 150, 150),
        ),
        (f"  -> {dir_label}", (100, 180, 255) if wind_on else (100, 100, 100)),
        (
            f"Дождь: {'ВКЛ' if rain_on else 'ВЫКЛ'}",
            (100, 180, 255) if rain_on else (150, 150, 150),
        ),
        (f"Скорость: {speed}x", (200, 200, 200)),
        ("", None),
        ("--- Управление ---", (100, 100, 100)),
        ("ЛКМ - дерево", (150, 150, 150)),
        ("ПКМ - поджечь", (150, 150, 150)),
        ("R - сброс", (150, 150, 150)),
        ("C - очистить", (150, 150, 150)),
        ("W - ветер вкл/выкл", (150, 150, 150)),
        ("D - дождь вкл/выкл", (150, 150, 150)),
        ("стрелки - направление", (150, 150, 150)),
        ("+/- скорость", (150, 150, 150)),
        ("SPACE - пауза", (150, 150, 150)),
    ]

    if paused:
        lines.insert(2, ("  ПАУЗА", (255, 80, 80)))

    y = 10
    for text, color in lines:
        if text == "":
            y += 6
            continue
        img = font.render(text, True, color)
        screen.blit(img, (px + 8, y))
        y += 20


def main():
    global wind_on, wind_dir, rain_on, wet_cells

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Лабораторная 3 - Лесные пожары")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)

    grid = make_grid()
    gen = 0
    paused = False
    speed = 1

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    grid = make_grid()
                    gen = 0
                    wet_cells = set()
                elif event.key == pygame.K_c:
                    grid = [[EMPTY] * COLS for _ in range(ROWS)]
                    gen = 0
                    wet_cells = set()
                elif event.key == pygame.K_w:
                    wind_on = not wind_on
                elif event.key == pygame.K_d:
                    rain_on = not rain_on
                    wet_cells = set()
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    speed = min(10, speed + 1)
                elif event.key == pygame.K_MINUS:
                    speed = max(1, speed - 1)
                elif event.key == pygame.K_UP:
                    wind_dir = (-1, 0)
                elif event.key == pygame.K_DOWN:
                    wind_dir = (1, 0)
                elif event.key == pygame.K_LEFT:
                    wind_dir = (0, -1)
                elif event.key == pygame.K_RIGHT:
                    wind_dir = (0, 1)

        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] or mouse_buttons[2]:
            mx, my = pygame.mouse.get_pos()
            c = mx // CELL_SIZE
            r = my // CELL_SIZE
            if 0 <= r < ROWS and 0 <= c < COLS:
                if mouse_buttons[0]:
                    grid[r][c] = TREE
                else:
                    grid[r][c] = BURNING

        if not paused:
            for _ in range(speed):
                if rain_on:
                    update_rain()
                grid = step(grid)
                gen += 1

        screen.fill((0, 0, 0))
        draw_grid(screen, grid)
        draw_panel(screen, font, grid, gen, paused, speed)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
