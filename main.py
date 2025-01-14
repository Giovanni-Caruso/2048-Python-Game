import pygame
import random
import math

# Initialize pygame
pygame.init()

# Frame rate for the game loop
FPS = 60

# Window dimensions and grid settings
WIDTH, HEIGHT = 800, 800
ROWS = 4
COLS = 4

# Calculate the size of each cell in the grid
RECT_HEIGHT = HEIGHT // ROWS
RECT_WIDTH = WIDTH // COLS

# Colors and UI settings
OUTLINE_COLOR = (187, 173, 160)  # Grid outline color
OUTLINE_THICKNESS = 10
BACKGROUND_COLOR = (205, 192, 180)  # Background color
FONT_COLOR = (119, 110, 101)

# Sound effects
MUSIC_SCORE = pygame.mixer.Sound("music/score.mp3")
MUSIC_GAMEOVER = pygame.mixer.Sound("music/game over.mp3")
MUSIC_WIN = pygame.mixer.Sound("music/congratulations.mp3")

# Flag to manage endgame state
CHECK_ENDGAME = True

# Fonts for displaying text
FONT = pygame.font.SysFont("comicsans", 60, bold=True)
FONT_ENDGAME = pygame.font.SysFont("comicsans", 100, bold=True)

# Movement velocity for animations
MOVE_VEL = 20

# Set up the main game window and surface
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048")
SURFACE = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)


class Tile:
    """Class representing a single tile in the game."""

    # Colors for different tile values
    COLORS = [
        (237, 229, 218),
        (238, 225, 201),
        (243, 178, 122),
        (246, 150, 101),
        (247, 124, 95),
        (247, 95, 59),
        (237, 208, 115),
        (237, 204, 99),
        (236, 202, 80),
        (237, 197, 63),
        (237, 194, 46),
    ]

    def __init__(self, value, row, col):
        self.value = value
        self.row = row
        self.col = col
        self.x = col * RECT_WIDTH
        self.y = row * RECT_HEIGHT

    def get_color(self):
        """Get the color based on the tile value."""
        color_index = int(math.log2(self.value)) - 1
        color = self.COLORS[color_index]
        return color

    def draw(self, window):
        """Draw the tile on the game window."""
        color = self.get_color()
        pygame.draw.rect(window, color, (self.x, self.y, RECT_WIDTH, RECT_HEIGHT))

        # Draw the tile's value
        text = FONT.render(str(self.value), 1, FONT_COLOR)
        window.blit(
            text,
            (
                self.x + (RECT_WIDTH / 2 - text.get_width() / 2),
                self.y + (RECT_HEIGHT / 2 - text.get_height() / 2),
            ),
        )

    def set_pos(self, ceil=False):
        """Set the tile's position based on its coordinates."""
        if ceil:
            self.row = math.ceil(self.y / RECT_HEIGHT)
            self.col = math.ceil(self.x / RECT_WIDTH)
        else:
            self.row = math.floor(self.y / RECT_HEIGHT)
            self.col = math.floor(self.x / RECT_WIDTH)

    def move(self, delta):
        """Move the tile by a given delta."""
        self.x += delta[0]
        self.y += delta[1]


def draw_grid(window):
    """Draw the grid lines on the game window."""
    for row in range(1, ROWS):
        y = row * RECT_HEIGHT
        pygame.draw.line(window, OUTLINE_COLOR, (0, y), (WIDTH, y), OUTLINE_THICKNESS)

    for col in range(1, COLS):
        x = col * RECT_WIDTH
        pygame.draw.line(window, OUTLINE_COLOR, (x, 0), (x, HEIGHT), OUTLINE_THICKNESS)

    pygame.draw.rect(window, OUTLINE_COLOR, (0, 0, WIDTH, HEIGHT), OUTLINE_THICKNESS)


def draw(window, tiles, surface):
    """Draw the game window, tiles, and grid."""
    window.fill(BACKGROUND_COLOR)

    for tile in tiles.values():
        tile.draw(window)

    draw_grid(window)

    global CHECK_ENDGAME

    if game_over(tiles):
        try_again(window, surface)
        if CHECK_ENDGAME:
            MUSIC_GAMEOVER.play()
            CHECK_ENDGAME = False

    if check_victory(tiles):
        you_win(window, surface)
        if CHECK_ENDGAME:
            MUSIC_WIN.play()
            CHECK_ENDGAME = False

    pygame.display.update()


def get_random_pos(tiles):
    """Get a random empty position in the grid."""
    while True:
        row = random.randrange(0, ROWS)
        col = random.randrange(0, COLS)
        if f"{row}{col}" not in tiles:
            break
    return row, col


def move_tiles(window, tiles, clock, direction, surface):
    """Handle the movement and merging of tiles."""
    updated = True
    blocks = set()

    if direction == "left":
        sort_func = lambda x: x.col
        reverse = False
        delta = (-MOVE_VEL, 0)
        boundary_check = lambda tile: tile.col == 0
        get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col - 1}")
        merge_check = lambda tile, next_tile: tile.x > next_tile.x + MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.x > next_tile.x + RECT_WIDTH + MOVE_VEL
        )
        ceil = True
    elif direction == "right":
        sort_func = lambda x: x.col
        reverse = True
        delta = (MOVE_VEL, 0)
        boundary_check = lambda tile: tile.col == COLS - 1
        get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col + 1}")
        merge_check = lambda tile, next_tile: tile.x < next_tile.x - MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.x + RECT_WIDTH + MOVE_VEL < next_tile.x
        )
        ceil = False
    elif direction == "up":
        sort_func = lambda x: x.row
        reverse = False
        delta = (0, -MOVE_VEL)
        boundary_check = lambda tile: tile.row == 0
        get_next_tile = lambda tile: tiles.get(f"{tile.row - 1}{tile.col}")
        merge_check = lambda tile, next_tile: tile.y > next_tile.y + MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.y > next_tile.y + RECT_HEIGHT + MOVE_VEL
        )
        ceil = True
    elif direction == "down":
        sort_func = lambda x: x.row
        reverse = True
        delta = (0, MOVE_VEL)
        boundary_check = lambda tile: tile.row == ROWS - 1
        get_next_tile = lambda tile: tiles.get(f"{tile.row + 1}{tile.col}")
        merge_check = lambda tile, next_tile: tile.y < next_tile.y - MOVE_VEL
        move_check = (
            lambda tile, next_tile: tile.y + RECT_HEIGHT + MOVE_VEL < next_tile.y
        )
        ceil = False

    while updated:
        clock.tick(FPS)
        updated = False
        sorted_tiles = sorted(tiles.values(), key=sort_func, reverse=reverse)

        for i, tile in enumerate(sorted_tiles):
            if boundary_check(tile):
                continue

            next_tile = get_next_tile(tile)
            if not next_tile:
                tile.move(delta)
            elif (
                tile.value == next_tile.value
                and tile not in blocks
                and next_tile not in blocks
            ):
                if merge_check(tile, next_tile):
                    tile.move(delta)
                else:
                    MUSIC_SCORE.play()
                    next_tile.value *= 2
                    sorted_tiles.pop(i)
                    blocks.add(next_tile)
            elif move_check(tile, next_tile):
                tile.move(delta)
            else:
                continue

            tile.set_pos(ceil)
            updated = True

        update_tiles(window, tiles, sorted_tiles, surface)

    return end_move(tiles)


def end_move(tiles):
    """Add a new tile after each move."""
    row, col = get_random_pos(tiles)
    tiles[f"{row}{col}"] = Tile(random.choice([2, 4]), row, col)


def game_over(tiles):
    """Check if no moves are possible."""
    if len(tiles) == 16:
        return True


def try_again(window, surface):
    """Display the Game Over screen."""
    window.blit(surface, (0, 0))

    pygame.draw.rect(
        surface,
        (255, 255, 255, 70),
        (0, 0, WIDTH, HEIGHT),
    )

    text = FONT_ENDGAME.render("Game Over!", 1, (0, 0, 0))
    surface.blit(
        text,
        (
            120,
            300,
        ),
    )


def check_victory(tiles):
    """Check if the player has reached the 2048 tile."""
    tiles_values = list(map(lambda tile: tile.value, tiles.values()))
    if max(tiles_values) == 2048:
        return True


def you_win(window, surface):
    """Display the Victory screen."""
    window.blit(surface, (0, 0))

    pygame.draw.rect(
        surface,
        (255, 255, 250, 70),
        (0, 0, WIDTH, HEIGHT),
    )

    text = FONT_ENDGAME.render("You win!", 1, (0, 0, 0))
    surface.blit(
        text,
        (
            210,
            300,
        ),
    )


def update_tiles(window, tiles, sorted_tiles, surface):
    """Update the tile positions after a move."""
    tiles.clear()
    for tile in sorted_tiles:
        tiles[f"{tile.row}{tile.col}"] = tile

    draw(window, tiles, surface)


def generate_tiles():
    """Initialize the game board with two tiles."""
    tiles = {}
    for _ in range(2):
        row, col = get_random_pos(tiles)
        tiles[f"{row}{col}"] = Tile(2, row, col)

    return tiles


def main(window, surface):
    """Main game loop."""
    clock = pygame.time.Clock()
    run = True

    tiles = generate_tiles()

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if (
                event.type == pygame.KEYDOWN
                and not game_over(tiles)
                and not check_victory(tiles)
            ):
                if event.key == pygame.K_LEFT:
                    move_tiles(window, tiles, clock, "left", surface)
                if event.key == pygame.K_RIGHT:
                    move_tiles(window, tiles, clock, "right", surface)
                if event.key == pygame.K_UP:
                    move_tiles(window, tiles, clock, "up", surface)
                if event.key == pygame.K_DOWN:
                    move_tiles(window, tiles, clock, "down", surface)

        draw(window, tiles, surface)

    pygame.quit()


if __name__ == "__main__":
    main(WINDOW, SURFACE)
