import pygame
from settings import RED


class FloatingText(pygame.sprite.Sprite):
    """
    Wyświetla unoszący się, zanikanący tekst nad postacią otrzymującą obrażenia.
    """

    def __init__(
            self,
            text: str,
            world_pos: pygame.math.Vector2,
            game,
            color=RED,
            font_name="assets/fonts/PressStart2P.ttf",
            font_size=16,
            duration=1000,
            rise=30
    ):
        """
        Inicjalizuje unoszący się tekst:
        - text: treść do wyświetlenia,
        - world_pos: wektorowa pozycja w świecie,
        - game: referencja do obiektu Game (dla offsetu kamery),
        - color: kolor napisu,
        - font_name: ścieżka do pliku czcionki,
        - font_size: rozmiar czcionki,
        - duration: czas wyświetlania w ms,
        - rise: dystans uniesienia w px.
        """
        super().__init__()
        self.game = game
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.rise = rise

        self.start_pos = pygame.math.Vector2(world_pos)
        self.pos = pygame.math.Vector2(world_pos)

        self.font = pygame.font.Font(font_name, font_size)
        self.image = self.font.render(text, True, color)
        self.alpha = 255
        self.image.set_alpha(self.alpha)

        self.rect = self.image.get_rect()

    def update(self):
        """
        Aktualizuje pozycję i przezroczystość tekstu:
        - po czasie >= duration usuwa sprite,
        - stopniowo zmniejsza przezroczystość (fade out),
        - unosi tekst w górę proporcjonalnie do upływu czasu.
        """
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.kill()
            return

        t = elapsed / self.duration
        self.alpha = max(0, int(255 * (1 - t)))
        self.image.set_alpha(self.alpha)

        self.pos.y = self.start_pos.y - self.rise * t

    def draw(self, surface, camera_offset):
        """
        Rysuje tekst na ekranie z offsetem kamery.
        """
        screen_x = self.pos.x - camera_offset[0]
        screen_y = self.pos.y - camera_offset[1]

        self.rect.center = (screen_x, screen_y)
        surface.blit(self.image, self.rect)
