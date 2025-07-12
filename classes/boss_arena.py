import pygame

from classes.world import World
from settings import TILE_SIZE


class BossArena(World):
    """
    Generuje i rysuje prostokątną arenę do walki z bossem.

    """

    def __init__(self, game, center_tile=(0, 0), width_tiles=16, height_tiles=8, seed=None):
        super().__init__(game, seed)

        # Obliczanie środka areny
        cx, cy = int(center_tile[0]), int(center_tile[1])
        self.center_tile = pygame.math.Vector2(cx, cy)
        # Przeliczanie na pixele
        self.center_pixel = pygame.math.Vector2(
            cx * TILE_SIZE + TILE_SIZE / 2,
            cy * TILE_SIZE + TILE_SIZE / 2
        )

        self.width_tiles = width_tiles
        self.height_tiles = height_tiles
        # Obliczanie granic
        half_w = width_tiles // 2
        half_h = height_tiles // 2
        self.left = cx - half_w
        self.right = cx + half_w
        self.top = cy - half_h
        self.bottom = cy + half_h

        # Lista kafelków wewnątrz granic areny
        self.arena_tiles = [
            (x, y)
            for x in range(self.left, self.right + 1)
            for y in range(self.top, self.bottom + 1)
        ]

    def draw(self, surf, cam_off):
        """
        Rysuje prostokątną arenę:
        - podłogę self.floor,
        - obramowanie self.wall wzdłuż krawędzi prostokąta.
        """
        # Rysowanie podłogi
        for tx, ty in self.arena_tiles:
            px = tx * TILE_SIZE - cam_off[0]
            py = ty * TILE_SIZE - cam_off[1]
            surf.blit(self.floor, (px, py))

        # Rysowanie górnej i dolnej krawędzi areny
        for x in range(self.left, self.right + 1):
            for y in (self.top, self.bottom):
                px = x * TILE_SIZE - cam_off[0]
                py = y * TILE_SIZE - cam_off[1]
                surf.blit(self.wall, (px, py))

        # Rysowanie lewej i prawej krawędzi areny
        for y in range(self.top + 1, self.bottom):
            for x in (self.left, self.right):
                px = x * TILE_SIZE - cam_off[0]
                py = y * TILE_SIZE - cam_off[1]
                surf.blit(self.wall, (px, py))
