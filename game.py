import random
import sys

import pygame

from classes.boss import Boss
from classes.boss_arena import BossArena
from classes.enemy import Enemy
from classes.player import Player
from classes.world import World
from settings import *
from ui.pause_menu import PauseMenu
from ui.portal import Portal
from ui.settings_menu import SettingsMenu
from ui.spritesheet import SpriteSheet


class Game:
    """
    Zarządza stanem gry: pętlą główną, obsługą wydarzeń,
    aktualizacją, rysowaniem oraz ekranami pauzy i ustawień.
    """

    def __init__(self):
        # Inicjalizacja gry
        pygame.init()
        pygame.mixer.init()

        # Ustawienie okna gry
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.font = pygame.font.Font("assets/fonts/PressStart2P.ttf", 16)
        self.clock = pygame.time.Clock()
        self.running = True

        # Ustawienie stanu gry po rozpoczęciu
        self.paused = True
        self.in_settings = False
        self.pause_menu = PauseMenu(self)
        self.settings_menu = SettingsMenu(self)

        # Ustawienia
        self.music_volume = 0.2
        self.sfx_volume = 0.2
        self.zoom = 1.0
        self.btn_text_scale = 0.3
        self.settings_items = ["Music Volume", "SFX Volume", "Zoom"]
        self.settings_index = 0

        # Kamera
        self.camera_offset = [0, 0]

        # Włączenie muzyki w tle
        pygame.mixer.music.load("assets/sounds/background_music.wav")
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(-1)

        # Inicjalizacja spriteów do animacji
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()

        # Ustawienie świata i gracza
        self.world = World(self)
        self.player = Player(WIDTH // 2, HEIGHT // 2, self)
        self.all_sprites.add(self.player)

        # Ustawienie stanu bossa na nieaktywny przy rozpoczęciu gry
        self.boss_active = False
        self.portal_active = False
        self.portal_rect = None
        self.boss_room = False
        self.boss_arena = None
        self.portal_sprite = None

        # Ustawienie satystyk do spawny przeciwników
        self.score = 0
        self.last_spawn = pygame.time.get_ticks()
        self.spawn_rate = SPAWN_RATE

        # Ustawienie ramki ze scorem
        sheet = SpriteSheet("assets/images/ui.png")
        self.score_bg_orig = sheet.image_at((8, 105, 47, 15))
        self.skull_orig = sheet.image_at((130, 66, 27, 28))

    def new(self):
        """
        Resetuje stan gry: usuwa sprite’y i przywraca gracza.
        """
        self.portal_active = False
        self.portal_rect = None
        self.boss_room = False
        self.boss_active = False
        self.boss_arena = None

        self.all_sprites.empty()
        self.enemies.empty()
        self.player_projectiles.empty()
        self.enemy_projectiles.empty()
        self.floating_texts.empty()

        self.player = Player(WIDTH // 2, HEIGHT // 2, self)
        self.all_sprites.add(self.player)

        self.score = 0
        self.last_spawn = pygame.time.get_ticks()

    def run(self):
        """
        Główna pętla gry: tick, eventy, update, draw.
        """
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            if not self.paused:
                self.update()
            self.draw()

    def handle_events(self):
        """
        Kontroluje eventy, przechodzi:
        - do ustawień, jeśli in_settings,
        - do pauzy, jeśli paused,
        - lub do rozgrywki.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.in_settings:
                self.settings_menu.handle_event(event)
            elif self.paused:
                self.pause_menu.handle_event(event)
            else:
                self._handle_game_event(event)

    def _handle_game_event(self, event):
        """
        Obsługuje eventy podczas gry:
        - ESC → pauza,
        - lewy klik → strzał,
        - spacja do wejścia do portalu
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.player.shoot(event.pos)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.portal_active:
            if self.portal_rect and self.player.rect.colliderect(self.portal_rect):
                self.enter_boss_room()

    def update(self):
        """
        Aktualizuje sprite’y, floating texts, kamerę, spawnuje wrogów i obsługuje kolizje.
        """
        self.all_sprites.update()
        self.floating_texts.update()

        if self.portal_active and self.portal_sprite:
            self.portal_sprite.update()
            self.portal_rect = self.portal_sprite.rect

        # Oblicza rozmiar viewportu zależnie od zoomu
        vw = int(WIDTH / self.zoom)
        vh = int(HEIGHT / self.zoom)

        # Kamera na gracza: pozycja środka gracza minus połowa viewportu
        cx = self.player.pos.x - vw // 2
        cy = self.player.pos.y - vh // 2

        # Zapisuje w camera_offset jako int
        self.camera_offset[0] = int(cx)
        self.camera_offset[1] = int(cy)

        # Zwiększa częstotliwość spawnu przeciwników z tempem gry
        decrement = (self.score // 200) * 100
        self.spawn_rate = max(100, SPAWN_RATE - decrement)

        # Po osiągnięciu docelowego scora pojawia portal do bossa
        if not self.boss_room and not self.portal_active and self.score >= 100:
            self.spawn_portal()

        now = pygame.time.get_ticks()
        if not self.boss_room and now - self.last_spawn > self.spawn_rate:
            self.last_spawn = now
            self.spawn_enemy()

        # Sprawdza kolizje pocisków i postaci
        self.check_collisions()

        # Ogranicza ruch gracza i bossa do granic areny
        if self.boss_room and self.boss_arena:
            # Liczymy granice w pikselach
            min_x = self.boss_arena.left * TILE_SIZE - TILE_SIZE
            max_x = (self.boss_arena.right + 1) * TILE_SIZE - TILE_SIZE
            min_y = self.boss_arena.top * TILE_SIZE - TILE_SIZE
            max_y = (self.boss_arena.bottom + 1) * TILE_SIZE - TILE_SIZE

            def clamp(v, minn, maxx):
                return max(minn, min(v, maxx))

            self.player.pos.x = clamp(self.player.pos.x, min_x, max_x)
            self.player.pos.y = clamp(self.player.pos.y, min_y, max_y)
            self.player.rect.center = self.player.pos

            for e in self.enemies:
                if isinstance(e, Boss):
                    e.pos.x = clamp(e.pos.x, min_x, max_x)
                    e.pos.y = clamp(e.pos.y, min_y, max_y)
                    e.rect.center = e.pos

    def draw(self):
        """
        Rysuje świat, sprite’y, floating texts oraz UI pauzy i ustawień.
        """
        # Oblicza rozmiar viewportu zależnie od zoomu
        vw = int(WIDTH / self.zoom)
        vh = int(HEIGHT / self.zoom)
        render_surf = pygame.Surface((vw, vh))
        render_surf.fill(BLACK)

        # Rysuje world / boss_room
        render_surf = pygame.Surface((vw, vh))
        if self.boss_room and self.boss_arena:
            self.boss_arena.draw(render_surf, (self.camera_offset[0], self.camera_offset[1]))
        else:
            self.world.draw(render_surf, (self.camera_offset[0], self.camera_offset[1]))

        # Rysowanie spriteów postaci z healthbarami
        for sprite in self.all_sprites:
            if isinstance(sprite, Boss):
                # Boss
                sprite.draw(render_surf, self.camera_offset)
            else:
                # Zwykłe sprite'y
                x = sprite.rect.x - self.camera_offset[0]
                y = sprite.rect.y - self.camera_offset[1]
                render_surf.blit(sprite.image, (x, y))

            # Rysuje healthbar dla wszystkich postaci poza bossem
            if hasattr(sprite, "health") and hasattr(sprite, "max_health") and not hasattr(sprite, "charge_phase"):
                # Wymiary healthbara
                ratio = sprite.health / sprite.max_health
                bar_w, bar_h = 30, 5
                fill_w = int(bar_w * ratio)
                # Obliczenie pozycji dla healthbara
                bar_x = x + (sprite.rect.width - bar_w) // 2
                bar_y = y - 10
                # Kolor w zależności gracz/przeciwnik
                col = GREEN if isinstance(sprite, Player) else RED
                pygame.draw.rect(render_surf, col, (bar_x, bar_y, fill_w, bar_h))
                pygame.draw.rect(render_surf, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # Rysowanie floating textów
        for text in self.floating_texts:
            text.draw(render_surf, (self.camera_offset[0], self.camera_offset[1]))

        # Rysowanie portalu
        if self.portal_active and self.portal_sprite:
            self.portal_sprite.draw(render_surf, (self.camera_offset[0], self.camera_offset[1]))
            # Rysowanie napisu
            tx = self.portal_sprite.rect.centerx - self.camera_offset[0] - 150
            ty = self.portal_sprite.rect.centery - self.camera_offset[1] - 50
            render_surf.blit(self.font.render("Press SPACE to enter", True, WHITE), (tx, ty))

        # Skalowanie na ekran
        final = pygame.transform.smoothscale(render_surf, (WIDTH, HEIGHT))
        self.screen.blit(final, (0, 0))

        # Rysowanie UI menu pauzy / ustawień
        if self.in_settings:
            self.settings_menu.draw(self.screen)
        elif self.paused:
            self.pause_menu.draw(self.screen)
        else:
            self.draw_ui()

        pygame.display.flip()

    def draw_ui(self):
        """
        Rysuje HUD:
        - podczas walki z bossem: czerwony pasek życia bossa na górze z ikoną czaszki na środku,
        - zwykły score w ramce w lewym górnym rogu.
        """
        if self.boss_room:
            boss = next((e for e in self.enemies if isinstance(e, Boss)), None)
            if boss:
                # Wymiary i pozycja healthbara bossa
                bar_w = int(WIDTH * 0.6)
                bar_h = 28
                bar_x = (WIDTH - bar_w) // 2
                bar_y = 40
                outline_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                fill_w = int(bar_w * (boss.health / boss.max_health))
                fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)

                # Rysowanie wypełnienia i obramówki
                pygame.draw.rect(self.screen, RED, fill_rect)
                pygame.draw.rect(self.screen, WHITE, outline_rect, 2)

                # Ikonka czaszki na healtbarze
                skull_h = bar_h * 3
                skull_w = skull_h
                skull = pygame.transform.scale(self.skull_orig, (skull_w, skull_h))
                skull_x = WIDTH // 2 - skull_w // 2
                skull_y = bar_y - skull_h // 4
                self.screen.blit(skull, (skull_x, skull_y))

        # Rysowanie, pozycja i skalowanie tabliczki ze scorem
        score_text = f"Score: {self.score}"
        surf = self.font.render(score_text, True, WHITE)
        w, h = surf.get_size()

        orig_w, orig_h = self.score_bg_orig.get_size()
        padding = 20
        frame_w = max(orig_w, w + 2 * padding)
        frame_h = orig_h * 2
        frame_s = pygame.transform.scale(self.score_bg_orig, (frame_w, frame_h))

        x, y = 10, 10
        self.screen.blit(frame_s, (x, y))
        self.screen.blit(surf, (x + padding, y + (frame_h - h) // 2))

    def spawn_enemy(self):
        """
        Spawnuje wroga na losowej krawędzi widocznego obszaru.
        """
        cx, cy = self.camera_offset
        left, right = cx, cx + WIDTH
        top, bot = cy, cy + HEIGHT

        side = random.randint(0, 3)
        if side == 0:
            x = random.randint(left, right)
            y = top - ENEMY_SIZE
        elif side == 1:
            x = right + ENEMY_SIZE
            y = random.randint(top, bot)
        elif side == 2:
            x = random.randint(left, right)
            y = bot + ENEMY_SIZE
        else:
            x = left - ENEMY_SIZE
            y = random.randint(top, bot)

        e = Enemy(x, y, self)
        self.all_sprites.add(e)
        self.enemies.add(e)

    def check_collisions(self):
        """
        Obsługuje kolizje pocisków i kontaktów.
        """
        # Interakcja pocisków gracza z wrogami
        hits = pygame.sprite.groupcollide(self.enemies, self.player_projectiles, False, True)
        for enemy, projs in hits.items():
            for p in projs:
                died = enemy.take_damage(p.damage)
                if died:
                    # Po zabiciu bossa kończymy grę
                    if isinstance(enemy, Boss):
                        self.game_win()
                    else:
                        # Po zabiciu zwykłego worga dodajemu 10 pkt. do scora
                        self.score += 10

        # Interakcja pocisków wroga z graczem
        hits = pygame.sprite.spritecollide(self.player, self.enemy_projectiles, True)
        for p in hits:
            if self.player.take_damage(p.damage):
                # Game over po zabiciu gracza
                self.game_over()

        # Interakcja gracza w modelami przeciwników
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for e in hits:
            if self.player.take_damage(e.damage * 0.1):
                # Game over po zabiciu gracza
                self.game_over()

    def spawn_portal(self):
        self.portal_active = True
        # Obliczenie pozycji portalu 50px nad graczem
        px = self.player.pos.x
        py = self.player.pos.y - 50
        # Uruchomienie sprite'a portalu
        self.portal_sprite = Portal(px, py, scale=3.0, anim_speed=100)
        self.portal_rect = self.portal_sprite.rect

    def enter_boss_room(self):
        """
        Przenosi gracza i bossa do prostokątnej areny:
        - boss pojawia się na górnej krawędzi,
        - gracz na dolnej krawędzi.
        """
        # Ustawienie stanów gry
        self.portal_active = False
        self.boss_room = True
        self.boss_active = True
        self.portal_rect = None

        # Wyczyść zwykłych wrogów i pociski
        for e in list(self.enemies):
            self.enemies.remove(e)
            self.all_sprites.remove(e)
        for p in list(self.player_projectiles):
            self.player_projectiles.remove(p)
            self.all_sprites.remove(p)
        for p in list(self.enemy_projectiles):
            self.enemy_projectiles.remove(p)
            self.all_sprites.remove(p)

        # Oblicz środek areny
        center_tile = (
            self.camera_offset[0] // TILE_SIZE + (WIDTH // 2) // TILE_SIZE,
            self.camera_offset[1] // TILE_SIZE + (HEIGHT // 2) // TILE_SIZE
        )
        # Stwórz arenę o podanych wymiarach
        self.boss_arena = BossArena(
            self,
            center_tile=center_tile,
            width_tiles=50,
            height_tiles=25
        )

        # Pozycja spawnu bossa na górnej krawędzi
        top_tile = self.boss_arena.top
        boss_x = self.boss_arena.center_tile.x * TILE_SIZE + TILE_SIZE / 2
        boss_y = top_tile * TILE_SIZE + TILE_SIZE / 2
        # Pozycja spawnu gracza na dolnej krawędzi
        bot_tile = self.boss_arena.bottom
        player_x = boss_x
        player_y = bot_tile * TILE_SIZE + TILE_SIZE / 2

        # Utworzenie bossa
        boss = Boss(boss_x, boss_y, self)
        self.all_sprites.add(boss)
        self.enemies.add(boss)

        # Przeniesienie gracza na arenę gracza
        self.player.pos.update(player_x, player_y)
        self.player.rect.center = (player_x, player_y)

        # Zmiana muzyki na bossową
        try:
            pygame.mixer.music.load("assets/sounds/boss_music.wav")
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Nie udało się załadować muzyki bossowej: {e}")

    def game_over(self):
        """
        Wyświetla ekran przegranej i czeka na R, by zrestartować grę.
        """
        # Wymiary okna gry
        w, h = WIDTH, HEIGHT

        # Skalowanie czcionki z zależności od wielkości okna
        font_path = "assets/fonts/PressStart2P.ttf"
        go_size = max(24, int(h * 0.12))
        score_size = max(18, int(h * 0.08))
        restart_size = max(16, int(h * 0.06))
        font_go = pygame.font.Font(font_path, go_size)
        font_score = pygame.font.Font(font_path, score_size)
        font_restart = pygame.font.Font(font_path, restart_size)

        # Odtworzenie muzyki Game Over
        try:
            pygame.mixer.music.load("assets/sounds/game_over.wav")
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(1)
        except pygame.error as e:
            print(f"Nie udało się załadować dźwięku game over: {e}")

        # Renderowanie tekstów
        go_surf = font_go.render("GAME OVER", True, RED)
        score_surf = font_score.render(f"Score: {self.score}", True, WHITE)
        restart_surf = font_restart.render("Press R to restart", True, WHITE)

        # Skalowanie i dynamiczna pozycja ikonki czaszki
        orig_sw, orig_sh = self.skull_orig.get_size()
        skull_w = int(w * 0.15)
        skull_h = int(skull_w * orig_sh / orig_sw)
        skull_surf = pygame.transform.scale(self.skull_orig, (skull_w, skull_h))

        center_x = w // 2
        skull_x = center_x - skull_w // 2
        skull_y = int(h * 0.1)
        gap = int(h * 0.03)

        go_x = center_x - go_surf.get_width() // 2
        go_y = skull_y + skull_h + gap
        score_x = center_x - score_surf.get_width() // 2
        score_y = go_y + go_surf.get_height() + gap
        restart_x = center_x - restart_surf.get_width() // 2
        restart_y = score_y + score_surf.get_height() + gap

        # Rysowanie gotowego ekrany Game Over
        self.screen.fill(BLACK)
        self.screen.blit(skull_surf, (skull_x, skull_y))
        self.screen.blit(go_surf, (go_x, go_y))
        self.screen.blit(score_surf, (score_x, score_y))
        self.screen.blit(restart_surf, (restart_x, restart_y))
        pygame.display.flip()

        # Oczekiwanie na R do restartu gry lub quit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                        # Restart muzyki w tle
                        pygame.mixer.music.load("assets/sounds/background_music.wav")
                        pygame.mixer.music.set_volume(self.music_volume)
                        pygame.mixer.music.play(-1)
                        # Rozpoczęcie nowej gry
                        self.new()

    def game_win(self):
        """
        Wyświetla ekran zwycięstwa i czeka na R, by zrestartować grę.
        """
        w, h = WIDTH, HEIGHT
        font_path = "assets/fonts/PressStart2P.ttf"
        # Skalowanie czcionki z zależności od wielkości okna
        win_size = max(24, int(h * 0.12))
        score_size = max(18, int(h * 0.08))
        restart_size = max(16, int(h * 0.06))
        font_win = pygame.font.Font(font_path, win_size)
        font_score = pygame.font.Font(font_path, score_size)
        font_restart = pygame.font.Font(font_path, restart_size)

        # Skalowanie i dynamiczna pozycja ikonki korony
        try:
            crown = pygame.image.load("assets/images/crown.png").convert_alpha()
            cw = int(w * 0.15)
            ch = int(cw * crown.get_height() / crown.get_width())
            crown = pygame.transform.scale(crown, (cw, ch))
        except Exception as e:
            print(f"Nie udało się załadować korony: {e}")
            crown = None

        # Renderowanie tekstów
        win_surf = font_win.render("YOU WIN!", True, BLACK)
        score_surf = font_score.render(f"Score: {self.score}", True, BLACK)
        restart_surf = font_restart.render("Press R to restart", True, BLACK)

        # Skalowanie czcionki z zależności od wielkości okna
        center_x = w // 2
        y = int(h * 0.1)
        self.screen.fill(YELLOW)
        if crown:
            cx = center_x - crown.get_width() // 2
            self.screen.blit(crown, (cx, y))
            y += crown.get_height() + int(h * 0.03)

        wy = center_x - win_surf.get_width() // 2
        self.screen.blit(win_surf, (wy, y))
        y += win_surf.get_height() + int(h * 0.03)

        sx = center_x - score_surf.get_width() // 2
        self.screen.blit(score_surf, (sx, y))
        y += score_surf.get_height() + int(h * 0.03)

        rx = center_x - restart_surf.get_width() // 2
        self.screen.blit(restart_surf, (rx, y))

        pygame.display.flip()

        # Odtworzenie muzyki Victory
        try:
            pygame.mixer.music.load("assets/sounds/victory_music.ogg")
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except:
            pass

        # Oczekiwanie na R do restartu gry lub quit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                        # Restart muzyki w tle
                        pygame.mixer.music.load("assets/sounds/background_music.wav")
                        pygame.mixer.music.set_volume(self.music_volume)
                        pygame.mixer.music.play(-1)
                        # Rozpoczęcie nowej gry
                        self.new()