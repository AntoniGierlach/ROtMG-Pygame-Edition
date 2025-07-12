import pygame
import random
from settings import TILE_SIZE, WIDTH, HEIGHT, GREEN, PURPLE

CHUNK_SIZE = 16

MAX_TREE_CLUSTERS = 3
CLUSTER_MIN_RADIUS = 2
CLUSTER_MAX_RADIUS = 4
CLUSTER_MIN_TREES = 5
CLUSTER_MAX_TREES = 10

POND_CHANCE = 0.15
POND_MIN_RADIUS = 2
POND_MAX_RADIUS = 4

BUSH_CHANCE = 0.05


class World:
    """
    Odpowiada za proceduralne generowanie i rysowanie nieskończonego świata
    na bazie chunków: trawa, stawy, krzaki i drzewa.
    """

    def __init__(self, game, seed=None):
        """
        Inicjalizuje świat:
        - przechowuje referencję do gry i ziarno losowania,
        - przygotowuje cache chunków,
        - ładuje kafelki trawy, drzew, krzaków i wody.
        """
        self.game = game
        self.seed = seed if seed is not None else random.randrange(2 ** 32)
        self.chunks = {}

        self.grass = self._load_tile("assets/images/tiles/tile_grass.png", GREEN)
        self.tree = self._load_tile("assets/images/tiles/tile_oak_tree.png", GREEN)
        self.pine = self._load_tile("assets/images/tiles/tile_pine_tree.png", GREEN)
        self.bush = self._load_tile("assets/images/tiles/tile_bush.png", GREEN)
        self.water = self._load_tile("assets/images/tiles/tile_water.png", GREEN)
        self.floor = self._load_tile("assets/images/tiles/tile_purple.png", PURPLE)
        self.wall  = self._load_tile("assets/images/tiles/tile_wall.png",   PURPLE)

    def _load_tile(self, path, fallback_color):
        """
        Wczytuje i skaluje kafelek do rozmiaru TILE_SIZE.
        """
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        except Exception:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill(fallback_color)
            return surf

    def _make_chunk(self, cx, cy):
        """
        Generuje i zapisuje do cache listy pozycji:
        - drzew w kilku kępkach,
        - nieregularnego stawu,
        - losowo rozsianych krzaków.
        """
        rnd = random.Random((cx * 341873128712 + cy * 132897987541 + self.seed) & 0xFFFFFFFF)

        trees = []
        clusters = rnd.randint(1, MAX_TREE_CLUSTERS)
        for _ in range(clusters):
            base_x = cx * CHUNK_SIZE + rnd.randrange(CHUNK_SIZE)
            base_y = cy * CHUNK_SIZE + rnd.randrange(CHUNK_SIZE)
            count = rnd.randint(CLUSTER_MIN_TREES, CLUSTER_MAX_TREES)
            radius = rnd.randint(CLUSTER_MIN_RADIUS, CLUSTER_MAX_RADIUS)
            for __ in range(count):
                dx = rnd.randint(-radius, radius)
                dy = rnd.randint(-radius, radius)
                trees.append((base_x + dx, base_y + dy))

        ponds = []
        if rnd.random() < POND_CHANCE:
            cx0 = cx * CHUNK_SIZE
            cy0 = cy * CHUNK_SIZE
            center_x = cx0 + rnd.randrange(CHUNK_SIZE)
            center_y = cy0 + rnd.randrange(CHUNK_SIZE)
            radius = rnd.randint(POND_MIN_RADIUS, POND_MAX_RADIUS)
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    dist2 = dx * dx + dy * dy
                    if dist2 <= radius * radius:
                        noise = rnd.uniform(0.6, 1.3)
                        if dist2 <= (radius * noise) ** 2:
                            ponds.append((center_x + dx, center_y + dy))

        bushes = []
        rnd_b = random.Random((cx * 1610612741 + cy * 805306457 + self.seed + 7) & 0xFFFFFFFF)
        x0, y0 = cx * CHUNK_SIZE, cy * CHUNK_SIZE
        for tx in range(x0, x0 + CHUNK_SIZE):
            for ty in range(y0, y0 + CHUNK_SIZE):
                if rnd_b.random() < BUSH_CHANCE and (tx, ty) not in ponds:
                    bushes.append((tx, ty))

        self.chunks[(cx, cy)] = {
            'trees': trees,
            'ponds': ponds,
            'bushes': bushes
        }

    def draw(self, surf, cam_off):
        """
        Rysuje kafelki w widocznym obszarze:
        - trawę na całym obszarze,
        - stawy, krzaki i drzewa na bazie wygenerowanych chunków.
        """
        sx = cam_off[0] // TILE_SIZE
        sy = cam_off[1] // TILE_SIZE
        ex = (cam_off[0] + WIDTH - 1) // TILE_SIZE
        ey = (cam_off[1] + HEIGHT - 1) // TILE_SIZE

        for ty in range(sy, ey + 1):
            for tx in range(sx, ex + 1):
                px = tx * TILE_SIZE - cam_off[0]
                py = ty * TILE_SIZE - cam_off[1]
                surf.blit(self.grass, (px, py))

        cx0 = sx // CHUNK_SIZE
        cy0 = sy // CHUNK_SIZE
        cx1 = ex // CHUNK_SIZE
        cy1 = ey // CHUNK_SIZE

        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                if (cx, cy) not in self.chunks:
                    self._make_chunk(cx, cy)
                data = self.chunks[(cx, cy)]

                for tx, ty in data['ponds']:
                    if sx <= tx <= ex and sy <= ty <= ey:
                        surf.blit(self.water, (tx * TILE_SIZE - cam_off[0],
                                               ty * TILE_SIZE - cam_off[1]))

                for tx, ty in data['bushes']:
                    if sx <= tx <= ex and sy <= ty <= ey:
                        surf.blit(self.bush, (tx * TILE_SIZE - cam_off[0],
                                              ty * TILE_SIZE - cam_off[1]))

                for tx, ty in data['trees']:
                    if (tx, ty) in data['ponds']:
                        continue
                    if sx <= tx <= ex and sy <= ty <= ey:
                        px = tx * TILE_SIZE - cam_off[0]
                        py = ty * TILE_SIZE - cam_off[1]
                        tile = self.pine if ((tx + ty + self.seed) & 1) == 0 else self.tree
                        surf.blit(tile, (px, py))