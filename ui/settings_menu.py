import pygame

from settings import WIDTH, HEIGHT, WHITE, YELLOW
from ui.spritesheet import SpriteSheet


class SettingsMenu:
    """
    Menu ustawień pozwalające regulować:
    - poziom głośności muzyki,
    - poziom głośności efektów (SFX),
    - poziom przybliżenia (zoom).
    Obsługuje rysowanie oraz nawigację klawiaturą.
    """

    def __init__(self, game):
        self.game = game
        ui = SpriteSheet("assets/images/ui.png")
        self.frame = ui.image_at((128, 131, 63, 75))
        self.button = ui.image_at((5, 234, 52, 14))

    def handle_event(self, event):
        """
        - ESC: wyjście z ekranu ustawień,
        - ↑/↓: zmiana wybranej pozycji (Music, SFX, Zoom),
        - ←/→: zmiana wartości dla aktywnej pozycji.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.in_settings = False
            elif event.key == pygame.K_UP:
                self.game.settings_index = (self.game.settings_index - 1) % len(self.game.settings_items)
            elif event.key == pygame.K_DOWN:
                self.game.settings_index = (self.game.settings_index + 1) % len(self.game.settings_items)
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                delta = 1 if event.key == pygame.K_RIGHT else -1
                idx = self.game.settings_index

                if idx == 0:  # Music Volume
                    self.game.music_volume = round(
                        min(1.0, max(0.0, self.game.music_volume + 0.1 * delta)), 1
                    )
                    pygame.mixer.music.set_volume(self.game.music_volume)

                elif idx == 1:  # SFX Volume
                    self.game.sfx_volume = round(
                        min(1.0, max(0.0, self.game.sfx_volume + 0.1 * delta)), 1
                    )

                elif idx == 2:  # Zoom
                    self.game.zoom = round(
                        min(2.5, max(1, self.game.zoom + 0.1 * delta)), 1
                    )

    def draw(self, surf):
        """
        Rysuje ramkę z przyciskami i etykietami ustawień,
        skalowane proporcjonalnie do ekranu.
        """
        # Oblicz skalę i pozycję ramki
        fw, fh = self.frame.get_size()
        fw2 = WIDTH // 3
        scale = fw2 / fw
        fh2 = int(fh * scale)
        frame_s = pygame.transform.scale(self.frame, (fw2, fh2))
        fx = (WIDTH - fw2) // 2
        fy = (HEIGHT - fh2) // 2
        surf.blit(frame_s, (fx, fy))

        # Przygotuj pojedynczy przycisk
        bw, bh = self.button.get_size()
        bw2 = int(bw * scale)
        bh2 = int(bh * scale)
        btn_s = pygame.transform.scale(self.button, (bw2, bh2))

        top = int(0.15 * fh2)
        spacing = int(0.10 * fh2)

        # Rysuj każdy przycisk i odpowiadający mu tekst
        for i, key in enumerate(self.game.settings_items):
            bx = fx + (fw2 - bw2) // 2
            by = fy + top + i * (bh2 + spacing)
            surf.blit(btn_s, (bx, by))

            # Dobierz tekst i czcionkę
            fs = max(8, int(bh2 * self.game.btn_text_scale))
            font = pygame.font.Font("assets/fonts/PressStart2P.ttf", fs)

            if key == "Music Volume":
                label = f"{int(self.game.music_volume * 100)}%"
            elif key == "SFX Volume":
                label = f"{int(self.game.sfx_volume * 100)}%"
            else:
                label = f"{self.game.zoom:.1f}x"

            color = YELLOW if i == self.game.settings_index else WHITE

            # Render nazwy i wartości
            name_s = font.render(key.split()[0], True, color)
            val_s = font.render(label, True, color)

            # Wyśrodkuj tekst w przycisku
            tx = bx + (bw2 - name_s.get_width()) // 2
            ty = by + (bh2 // 2 - name_s.get_height())
            surf.blit(name_s, (tx, ty))

            vx = bx + (bw2 - val_s.get_width()) // 2
            vy = by + (bh2 // 2)
            surf.blit(val_s, (vx, vy))

        # Wyświetl instrukcje do nawigacji
        navi = pygame.font.Font("assets/fonts/PressStart2P.ttf", 15).render("Navigate: ↑ ↓ | Adjust: ← →", True, WHITE)
        surf.blit(navi, (fx + (fw2 - navi.get_width()) // 2, fy + fh2 - 57))
        back = pygame.font.Font("assets/fonts/PressStart2P.ttf", 15).render("Back: Esc", True, WHITE)
        surf.blit(back, (fx + (fw2 - back.get_width()) // 2, fy + fh2 - 35))
