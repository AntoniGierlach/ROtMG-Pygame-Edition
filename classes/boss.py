import pygame

from classes.floating_text import FloatingText
from classes.projectile import Projectile
from settings import (
    BOSS_HEALTH,
    BOSS_SPEED,
    BOSS_DAMAGE,
    BOSS_SIZE,
    RED,
    WHITE,
    PLAYER_SPEED
)

class Boss(pygame.sprite.Sprite):
    """
    Logika bossa z atakami, szarżą,
    od 50% HP pojawia się pod graczem spowalniająca plama.
    """

    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.pos = pygame.math.Vector2(x, y)
        self.facing_left = True

        # Ładowanie animacji bossa
        self.animations = {}
        for state in ("idle", "flying", "attack", "death"):
            sheet = pygame.image.load(f"assets/images/boss/{state.upper()}.png").convert_alpha()
            frame_w, frame_h = 81, 71
            count = sheet.get_width() // frame_w
            frames = []
            for i in range(count):
                rect = (i * frame_w, 0, frame_w, frame_h)
                frame = sheet.subsurface(rect)
                # Skalowanie modelu
                frame = pygame.transform.scale(frame,(frame_w * BOSS_SIZE, frame_h * BOSS_SIZE))
                frames.append(frame)
            self.animations[state] = frames

        # Początkowe wartości dla bossa
        self.state = "idle"
        self.frame_index = 0
        self.anim_speed = 100
        self.last_anim = pygame.time.get_ticks()
        self.last_patch_time = pygame.time.get_ticks()
        self.image = self.animations["idle"][0]
        self.rect = self.image.get_rect(center=(x, y))

        # Wczytanie statystyk bossa z ustawień
        self.health = BOSS_HEALTH
        self.max_health = BOSS_HEALTH
        self.speed = BOSS_SPEED
        self.damage = BOSS_DAMAGE

        # Ustawienia dotyczące ataków, szarży i plamy
        self.attack_patterns = {
            'circle': {'cd': 2000, 'last': 0, 'b': 24},
            'charge': {'cd': 10000, 'last': 0}
        }
        self.phase = 0
        self.charge_phase = 0  # 0=wait,1=telegraph,2=leap
        self.charge_wait = 1500
        self.charge_speed = 2000
        self.charge_start = 0
        self.charge_dir = pygame.math.Vector2()
        self.last_distance = 0
        self.patch = None

    def update(self):
        now = pygame.time.get_ticks()

        # Animacje śmierci bossa
        if self.health <= 0 and self.state != "death":
            self.state = "death"
            self.frame_index = 0
            self.last_anim = now

        if self.state == "death":
            self._animate(now, loop=False)
            return

        # Poniżej 50% życia boss pojawia spowalniajce plamy pod graczem
        if self.health < self.max_health * 0.5:
            if now - self.last_patch_time >= 10_000:
                p = self.game.player
                patch = SlowingPatch(p.pos, self.game)
                self.game.all_sprites.add(patch)
                self.last_patch_time = now

        # Śledzenie gracza i ruch w jego kierunku
        pl = self.game.player
        if pl:
            dir_vec = pygame.math.Vector2(pl.pos) - self.pos
            if dir_vec.length() > 0:
                n = dir_vec.normalize()
                self.facing_left = n.x < 0
                self.pos += n * self.speed
                self.rect.center = self.pos
                self.state = "flying"
            else:
                self.state = "idle"

        # Ataki: circle i charge
        self._try_circle(now)
        self._try_charge(now)

        self._animate(now)

    def _try_circle(self, now):
        # Wystrzeliwanie pocisków dookoła bossa
        pat = self.attack_patterns['circle']
        if now - pat['last'] > pat['cd']:
            for i in range(pat['b']):
                angle = 360 / pat['b'] * i
                dir_vec = pygame.math.Vector2(1, 0).rotate(angle)
                self._shoot(dir_vec)
            pat['last'] = now
            self.state = "attack"
            self.frame_index = 0

    def _try_charge(self, now):
        # Szarża w kierunku gracza
        pat = self.attack_patterns['charge']
        if self.state == "death":
            return
        if self.charge_phase == 0 and now - pat['last'] > pat['cd']:
            self.charge_phase = 1
            self.charge_start = now
            dir_vec = (pygame.math.Vector2(self.game.player.pos) - self.pos).normalize()
            self.charge_dir = dir_vec
            self.facing_left = dir_vec.x < 0

        elif self.charge_phase == 1 and now - self.charge_start > self.charge_wait:
            self.charge_phase = 2
            pat['last'] = now
            self.last_distance = 0

        elif self.charge_phase == 2:
            dt = (now - self.charge_start - self.charge_wait) / 1000
            dist = min(self.charge_speed * dt, 1000)
            delta = dist - self.last_distance
            if delta > 0:
                self.pos += self.charge_dir * delta
                self.last_distance = dist
                self.rect.center = self.pos
            if dist >= 1000:
                # reset
                self.charge_phase = 0
                self.last_distance = 0

    def _shoot(self, dir_vec):
        # Wystrzeliwanie pocisków
        dmg = self.damage * (1 + 0.5 * (self.phase - 1))
        b = Projectile(self.pos.x, self.pos.y,
                       dir_vec.x, dir_vec.y,
                       dmg, False, self.game)
        self.game.all_sprites.add(b)
        self.game.enemy_projectiles.add(b)

    def take_damage(self, amount):
        # Wyświetlanie floating textu przy otrzymywaniu obrażeń
        self.game.floating_texts.add(FloatingText(f"-{int(amount)}", self.pos, self.game, WHITE))
        self.health -= amount
        return self.health <= 0

    def _animate(self, now, loop=True):
        # Obsługa animacji bossa
        if now - self.last_anim > self.anim_speed:
            self.last_anim = now
            self.frame_index += 1
            frames = self.animations[self.state]
            if self.frame_index >= len(frames):
                if loop:
                    self.frame_index = 0
                else:
                    self.frame_index = len(frames) - 1
            frame = frames[self.frame_index]
            if not self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            c = self.rect.center
            self.image = frame
            self.rect = self.image.get_rect(center=c)

    def draw(self, surf, cam_off):
        # Rysowanie wskaźnika szarży bossa
        if self.charge_phase == 1:
            px = self.pos.x - cam_off[0]
            py = self.pos.y - cam_off[1]
            start = (px + BOSS_SIZE / 2, py + BOSS_SIZE / 2)
            end = (start[0] + self.charge_dir.x * 1000 / self.game.zoom,
                   start[1] + self.charge_dir.y * 1000 / self.game.zoom)
            pygame.draw.line(surf, RED, start, end, 3)

        px = self.rect.x - cam_off[0]
        py = self.rect.y - cam_off[1]
        surf.blit(self.image, (px, py))

class SlowingPatch(pygame.sprite.Sprite):
    """
    Plama pod graczem: spowalnia i zadaje 1 dmg/s, gdy
    gracz stoi na niej.
    """

    def __init__(self, pos, game, radius=128):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 0, 0, 150), (radius, radius), radius)
        self.rect = self.image.get_rect(center=(pos.x, pos.y))
        self.last_damage = pygame.time.get_ticks()
        self.slowed = set()

    def update(self):
        player = self.game.player
        now = pygame.time.get_ticks()
        if self.rect.colliderect(player.rect):
            # Spowalnianie gracza, gdy stoi w plamie
            player.speed = PLAYER_SPEED * 0.5
            # Zadaje obrażenia co sekunde
            if now - self.last_damage >= 1000:
                self.last_damage = now
                player.take_damage(1)
        else:
            # Przywraca normalną prędkość graczowi, gry wyjdzie z plamy
            if player.speed < PLAYER_SPEED:
                player.speed = PLAYER_SPEED