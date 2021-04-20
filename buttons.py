import pygame, os

class RectButton:
    def __init__(self, cpos, size, text, border_radius=10):
        self.rect = pygame.Rect(cpos.x-size.x//2, cpos.y-size.y//2, size.x, size.y)
        self.border_radius = border_radius
        self.text = text
        self.font = pygame.font.Font(os.path.join("fonts", "Roboto", "Roboto-Thin.ttf"), int(size.y//2))

    def clicked(self):
        if self.hovered() and pygame.mouse.get_pressed(3)[0]:
            return True
        return False

    def hovered(self):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx//2, my//2):
            return True
        return False

    def draw(self, screen, color, hover_color, click_color, font_color):
        if self.clicked():
            pygame.draw.rect(screen, click_color, self.rect, border_radius=self.border_radius)
        elif self.hovered():
            pygame.draw.rect(screen, hover_color, self.rect, border_radius=self.border_radius)
        else:
            pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        txt_img = self.font.render(self.text, False, font_color).convert_alpha()
        screen.blit(
            txt_img,
            (
                self.rect.centerx-txt_img.get_rect().width//2,
                self.rect.centery-txt_img.get_rect().height//2
            )
        )
