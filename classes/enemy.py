import pygame
import os
import random

from classes.floating_text import FloatingText
from classes.projectile import Projectile
from settings import (
    ENEMY_SIZE,
    ENEMY_SPEED,
    ENEMY_HEALTH,
    ENEMY_DAMAGE,
    ENEMY_SHOOT_CHANCE,
    ENEMY_MIN_SHOOT_DELAY,
    ENEMY_MAX_SHOOT_DELAY,
    RED
)


class Enemy(pygame.sprite.Sprite):
    """
    Reprezentuje przeciwnika:
    - losowo wybiera grafikę z folderu lub placeholder,
    - porusza się w stronę gracza,
    - może strzelać pociskami z losowym cooldownem,
    - przy otrzymaniu obrażeń wyświetla unoszący się tekst i odtwarza dźwięk.
    """

    def __init__(self, x, y, game):
        """
        Inicjalizuje przeciwnika:
        - pozycja (x, y), referencja do Game,
        - losuje teksturę i statystyki strzału,
        - ustawia zdrowie, prędkość i obrażenia,
        - ładuje dźwięki przy obrażeniach.
        """
        super().__init__()
        self.game = game
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)

        self.images = self._load_images()
        self.original_image = random.choice(self.images)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))

        self.speed = ENEMY_SPEED
        self.health = ENEMY_HEALTH
        self.max_health = ENEMY_HEALTH
        self.damage = ENEMY_DAMAGE

        self.can_shoot = random.random() < ENEMY_SHOOT_CHANCE
        if self.can_shoot:
            self.shoot_delay = random.randint(ENEMY_MIN_SHOOT_DELAY, ENEMY_MAX_SHOOT_DELAY)
            self.last_shot = pygame.time.get_ticks()

        self.sounds = self._load_sounds()

    def _load_images(self):
        """
        Ładuje wszystkie pliki PNG z folderu 'assets/images/enemies',
        zwraca listę Surface; jeśli folder lub pliki nie istnieją,
        zwraca jednolity placeholder.
        """
        folder = os.path.join("assets", "images", "enemies")
        images = []
        if os.path.exists(folder):
            for fn in os.listdir(folder):
                if fn.lower().endswith(".png"):
                    path = os.path.join(folder, fn)
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        if img.get_size() != (ENEMY_SIZE, ENEMY_SIZE):
                            img = pygame.transform.scale(img, (ENEMY_SIZE, ENEMY_SIZE))
                        images.append(img)
                    except Exception:
                        pass
        if not images:
            placeholder = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
            placeholder.fill(RED)
            images = [placeholder]
        return images

    def _load_sounds(self):
        """
        Ładuje wszystkie pliki WAV/OGG/MP3 z folderu 'assets/sounds/enemies';
        zwraca listę Sound, lub pustą listę jeśli żadne nie istnieją.
        """
        folder = os.path.join("assets", "sounds", "enemies")
        sounds = []
        if os.path.exists(folder):
            for fn in os.listdir(folder):
                if fn.lower().endswith((".wav", ".ogg", ".mp3")):
                    path = os.path.join(folder, fn)
                    try:
                        sounds.append(pygame.mixer.Sound(path))
                    except Exception:
                        pass
        return sounds

    def update(self):
        """
        Porusza przeciwnika w stronę gracza, obraca obraz,
        i jeśli może strzelać, wywołuje próbę strzału.
        """
        player = self.game.player
        if not player:
            return

        direction = pygame.math.Vector2(player.rect.center) - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.vel = direction * self.speed
        self.pos += self.vel
        self.rect.center = self.pos

        if self.vel.x < 0:
            self.image = pygame.transform.flip(self.original_image, True, False)
        else:
            self.image = self.original_image

        if self.can_shoot:
            self._try_shoot(direction)

    def _try_shoot(self, direction):
        """
        Strzela pocisk w kierunku gracza, jeśli cooldown wygasł.
        """
        now = pygame.time.get_ticks()
        if now - self.last_shot < self.shoot_delay:
            return
        self.last_shot = now

        dx, dy = direction.x, direction.y
        bullet = Projectile(
            self.pos.x,
            self.pos.y,
            dx,
            dy,
            self.damage,
            False,
            self.game
        )
        self.game.all_sprites.add(bullet)
        self.game.enemy_projectiles.add(bullet)

    def take_damage(self, amount):
        """
        Odtwarza losowy dźwięk obrażeń, wyświetla floating text,
        zmniejsza zdrowie i usuwa sprite przy śmierci.
        Zwraca True jeśli wróg zginął.
        """
        self.game.floating_texts.add(FloatingText(f"-{int(amount)}", self.pos, self.game))

        if self.sounds:
            sound = random.choice(self.sounds)
            sound.set_volume(0.1 * self.game.sfx_volume)
            sound.play()

        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False
