import pygame


class SpriteSheet:
    """Ładuje całego spritesheeta i wyciąga z niego poszczególne elementy."""

    def __init__(self, filename):
        """
        Ładuje arkusz sprite'ów z podanego pliku.
        filename: ścieżka do pliku PNG z arkuszem.
        """
        self.sheet = pygame.image.load(filename).convert_alpha()

    def image_at(self, rect):
        """
        Zwraca Surface wycięty z arkusza:
        rect: tuple (x, y, width, height) określający prostokąt do wycięcia.
        """
        x, y, w, h = rect
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        surface.blit(self.sheet, (0, 0), rect)
        return surface

    def images_at(self, rects):
        """
        Zwraca listę Surface'ów dla wielu prostokątów.
        rects: lista tupli (x, y, width, height).
        """
        return [self.image_at(r) for r in rects]