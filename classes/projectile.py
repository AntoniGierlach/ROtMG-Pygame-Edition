import math
import pygame

from settings import (
    PLAYER_PROJECTILE_IMAGE,
    PLAYER_PROJECTILE_SOUND,
    PLAYER_PROJECTILE_SIZE,
    PLAYER_PROJECTILE_SPEED,
    ENEMY_PROJECTILE_IMAGE,
    ENEMY_PROJECTILE_SOUND,
    ENEMY_PROJECTILE_SIZE,
    ENEMY_PROJECTILE_SPEED
)


class Projectile(pygame.sprite.Sprite):
    """
    Reprezentuje pocisk wystrzelony przez gracza lub wroga.
    Obsługuje grafikę, dźwięk, ruch wektorowy i usuwanie po upłynięciu czasu życia.
    """

    def __init__(self, x, y, dx, dy, damage, is_player, game):
        """
        Inicjalizuje pocisk:
        - zapisuje referencję do gry, obrażenia i typ strzelca,
        - wczytuje i skaluje grafikę odpowiednią dla gracza lub wroga,
        - oblicza prędkość na podstawie kierunku (dx, dy) i stałej prędkości,
        - obraca obraz pod właściwym kątem,
        - ustawia czas życia i odtwarza dźwięk strzału z uwzględnieniem głośności efektów.
        """
        super().__init__()
        self.game = game

        if is_player:
            img_path = PLAYER_PROJECTILE_IMAGE
            sound_path = PLAYER_PROJECTILE_SOUND
            size = PLAYER_PROJECTILE_SIZE
            speed = PLAYER_PROJECTILE_SPEED
        else:
            img_path = ENEMY_PROJECTILE_IMAGE
            sound_path = ENEMY_PROJECTILE_SOUND
            size = ENEMY_PROJECTILE_SIZE
            speed = ENEMY_PROJECTILE_SPEED

        try:
            image = pygame.image.load(img_path).convert_alpha()
            if image.get_size() != (size, size):
                image = pygame.transform.scale(image, (size, size))
            self.original_image = image
        except Exception:
            self.original_image = pygame.Surface((size, size), pygame.SRCALPHA)
            placeholder_color = (255, 255, 0) if is_player else (255, 100, 100)
            self.original_image.fill(placeholder_color)

        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)

        direction = pygame.math.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()
        self.vel = direction * speed

        self.angle = math.degrees(math.atan2(-dy, dx))
        self._rotate_image()

        self.damage = damage
        self.is_player = is_player
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 5000  # milliseconds

        try:
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(0.1 * self.game.sfx_volume)
            sound.play()
        except Exception:
            print(f"Nie udało się załadować dźwięku: {sound_path}")

    def _rotate_image(self):
        """
        Obraca grafikę pocisku zgodnie z obliczonym kątem self.angle.
        """
        rotated = pygame.transform.rotate(self.original_image, self.angle)
        center = self.rect.center
        self.image = rotated
        self.rect = self.image.get_rect(center=center)

    def update(self):
        """
        Aktualizuje pozycję pocisku oraz niszczy go, gdy przekroczy czas życia.
        """
        self.pos += self.vel
        self.rect.center = self.pos

        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()