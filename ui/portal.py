import pygame

class Portal(pygame.sprite.Sprite):
    """
    Animowany portal ładowany z portal.png (7 klatek 64×64: 4 w pierwszym rzędzie, 3 w drugim).
    scale — o ile razy pomnożyć oryginalny rozmiar klatki (64×64).
    anim_speed — ile ms między klatkami.
    """

    def __init__(self, x, y, scale: float = 1.0, anim_speed: int = 100):
        super().__init__()
        sheet = pygame.image.load("assets/images/portal.png").convert_alpha()

        orig_w, orig_h = 64, 64
        self.scale = scale
        w = int(orig_w * self.scale)
        h = int(orig_h * self.scale)

        self.frames = []
        for i in range(7):
            row = 0 if i < 4 else 1
            col = i if i < 4 else i - 4
            r = pygame.Rect(col * orig_w, row * orig_h, orig_w, orig_h)
            frame = sheet.subsurface(r)
            if self.scale != 1.0:
                frame = pygame.transform.scale(frame, (w, h))
            self.frames.append(frame)

        self.index = 0
        self.anim_speed = anim_speed
        self.last_upd = pygame.time.get_ticks()
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_upd > self.anim_speed:
            self.last_upd = now
            self.index = (self.index + 1) % len(self.frames)
            self.image = self.frames[self.index]
            c = self.rect.center
            self.rect = self.image.get_rect(center=c)

    def draw(self, surf, cam_off):
        """
        Rysuje portal na powierzchni surf, uwzględniając przesunięcie kamery.
        """
        x = self.rect.x - cam_off[0]
        y = self.rect.y - cam_off[1]
        surf.blit(self.image, (x, y))
