import sys

import pygame

from settings import WIDTH, HEIGHT
from ui.spritesheet import SpriteSheet


class PauseMenu:
    """
    Menu pauzy z trzema przyciskami: Play, Settings, Exit.
    Obsługuje rysowanie oraz kliknięcia myszy i klawisz ESC.
    """

    def __init__(self, game):
        self.game = game
        ui = SpriteSheet("assets/images/ui.png")
        self.frame = ui.image_at((128, 131, 63, 75))
        btn_rects = [
            (5, 138, 52, 14),  # PLAY
            (5, 170, 52, 14),  # SETTINGS
            (5, 202, 52, 14),  # EXIT
        ]
        self.buttons = ui.images_at(btn_rects)

    def handle_event(self, event):
        """
        - ESC: wyjście z pauzy,
        - kliknięcie przycisku: Play → wznowienie gry,
                                Settings → wejście w ustawienia,
                                Exit → zamknięcie aplikacji.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.paused = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            fw, fh = self.frame.get_size()
            fw2 = WIDTH // 3
            scale = fw2 / fw
            fh2 = int(fh * scale)
            fx = (WIDTH - fw2) // 2
            fy = (HEIGHT - fh2) // 2

            bw, bh = self.buttons[0].get_size()
            bw2 = int(bw * scale)
            bh2 = int(bh * scale)
            top = int(0.15 * fh2)
            spacing = int(0.10 * fh2)

            for i, btn in enumerate(self.buttons):
                bx = fx + (fw2 - bw2) // 2
                by = fy + top + i * (bh2 + spacing)
                if pygame.Rect(bx, by, bw2, bh2).collidepoint(mx, my):
                    if i == 0:
                        self.game.paused = False
                    elif i == 1:
                        self.game.in_settings = True
                    elif i == 2:
                        pygame.quit()
                        sys.exit()

    def draw(self, surf):
        """
        Rysuje tło pauzy z przyciskami w centralnej części ekranu.
        """
        fw, fh = self.frame.get_size()
        fw2 = WIDTH // 3
        scale = fw2 / fw
        fh2 = int(fh * scale)
        frame_s = pygame.transform.scale(self.frame, (fw2, fh2))
        fx = (WIDTH - fw2) // 2
        fy = (HEIGHT - fh2) // 2
        surf.blit(frame_s, (fx, fy))

        bw, bh = self.buttons[0].get_size()
        bw2 = int(bw * scale)
        bh2 = int(bh * scale)
        top = int(0.15 * fh2)
        spacing = int(0.10 * fh2)

        for i, btn in enumerate(self.buttons):
            btn_s = pygame.transform.scale(btn, (bw2, bh2))
            bx = fx + (fw2 - bw2) // 2
            by = fy + top + i * (bh2 + spacing)
            surf.blit(btn_s, (bx, by))