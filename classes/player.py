import os

import pygame

from classes.floating_text import FloatingText
from classes.projectile import Projectile
from settings import *


class Player(pygame.sprite.Sprite):
    """
    Gracz z animacjami:
    - idle (3 klatki),
    - walk (4 klatki, loop),
    - attack (3 klatki, jednokrotne odtwarzanie przy shoot()).
    Obsługuje flip L/R w zależności od kierunku ruchu lub strzału.
    """

    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.speed = PLAYER_SPEED

        # Ładowanie animacji
        self.animations = {
            'idle': [],  # 3 klatki
            'walk': [],  # 4 klatki
            'attack': []  # 3 klatki
        }

        for state, count in (('idle', 3), ('walk', 4), ('attack', 3)):
            for i in range(1, count + 1):
                path = os.path.join('assets', 'images', 'player', f'{state}_{i}.png')
                raw = pygame.image.load(path).convert_alpha()
                ow, oh = raw.get_size()
                sh = PLAYER_SIZE
                sw = int(ow * (sh / oh))
                img = pygame.transform.scale(raw, (sw, sh))
                self.animations[state].append(img)

        self.state = 'idle'
        self.frame_index = 0
        self.anim_speed = 120
        self.last_anim = pygame.time.get_ticks()
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(center=(x, y))
        self.facing_left = False

        self.last_shot = 0
        self.shoot_delay = PLAYER_SHOOT_DELAY

        self.attacking = False

        self.health = PLAYER_HEALTH
        self.max_health = PLAYER_HEALTH

    def update(self):
        now = pygame.time.get_ticks()

        # Ruch postaci
        keys = pygame.key.get_pressed()
        self.vel.x = keys[pygame.K_d] - keys[pygame.K_a]
        self.vel.y = keys[pygame.K_s] - keys[pygame.K_w]
        if self.vel.length_squared() > 0:
            self.vel = self.vel.normalize() * self.speed
        self.pos += self.vel
        self.rect.center = self.pos

        # Obracanie modelu lewo/prawo
        if self.vel.x < 0:
            self.facing_left = True
        elif self.vel.x > 0:
            self.facing_left = False

        # Wybór stanu do animacji
        if self.attacking:
            if now - self.last_anim > self.anim_speed:
                self.last_anim = now
                self.frame_index += 1
                if self.frame_index >= len(self.animations['attack']):
                    self.attacking = False
                    self.frame_index = 0
                    self.state = 'idle'
                else:
                    self.state = 'attack'

        else:
            if self.vel.length_squared() > 0:
                self.state = 'walk'
            else:
                self.state = 'idle'
            if self.frame_index >= len(self.animations[self.state]):
                self.frame_index = 0

        if now - self.last_anim > self.anim_speed:
            self.last_anim = now
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])
        frame = self.animations[self.state][self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        old_center = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=old_center)

    def shoot(self, mouse_pos):
        """
        Wystrzelenie pocisku:
        - ustawia attacking=True i restartuje animację attack,
        - flip na podstawie kierunku myszki.
        """
        now = pygame.time.get_ticks()
        if now - self.last_shot < self.shoot_delay:
            return
        self.last_shot = now

        # Oblicz kierunek w zależności od położenia myszki
        mx, my = mouse_pos
        world_x = mx + self.game.camera_offset[0]
        world_y = my + self.game.camera_offset[1]
        dir_vec = pygame.math.Vector2(world_x, world_y) - self.pos
        if dir_vec.length() > 0:
            dir_vec = dir_vec.normalize()

        self.facing_left = dir_vec.x < 0
        self.attacking = True
        self.state = 'attack'
        self.frame_index = 0
        self.last_anim = now

        bullet = Projectile(
            self.pos.x, self.pos.y,
            dir_vec.x, dir_vec.y,
            PLAYER_PROJECTILE_DAMAGE,
            True,
            self.game
        )
        self.game.all_sprites.add(bullet)
        self.game.player_projectiles.add(bullet)

    def take_damage(self, amount):
        """
        Zadawanie obrażeń + floating text.
        """
        self.game.floating_texts.add(
            FloatingText(f"-{int(amount)}", self.pos, self.game, color=RED)
        )
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False
