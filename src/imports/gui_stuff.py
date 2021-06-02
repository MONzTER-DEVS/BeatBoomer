import pygame, os
from pygame.math import Vector2 as vec

FONT_SIZE = 15


class RectButton:
    def __init__(self, cpos, size, text, border_radius=15):
        self.rect = pygame.Rect(cpos.x - size.x // 2, cpos.y - size.y // 2, size.x, size.y)
        self.original_rect = self.rect.copy()
        self.border_radius = border_radius
        self.text = text
        self.font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), FONT_SIZE)

    def clicked(self):
        if self.hovered() and pygame.mouse.get_pressed(3)[0]:
            return True
        return False

    def hovered(self):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx // 2, my // 2):
            return True
        return False

    def draw(self, screen, color, hover_color, click_color, font_color, scroll=vec()):
        self.rect.topleft = self.original_rect.topleft - scroll
        if self.clicked():
            pygame.draw.rect(screen, click_color, self.rect, border_top_left_radius=self.border_radius,
                             border_bottom_right_radius=self.border_radius)
        elif self.hovered():
            pygame.draw.rect(screen, hover_color, self.rect, border_top_left_radius=self.border_radius,
                             border_bottom_right_radius=self.border_radius)
        else:
            pygame.draw.rect(screen, color, self.rect, border_top_left_radius=self.border_radius,
                             border_bottom_right_radius=self.border_radius)
        txt_img = self.font.render(self.text, False, font_color).convert_alpha()
        screen.blit(
            txt_img,
            (
                self.rect.centerx - txt_img.get_rect().width // 2,
                self.rect.centery - txt_img.get_rect().height // 2
            )
        )


class RectButtonImg:
    def __init__(self, cpos, size, img, border_radius=15):
        self.rect = pygame.Rect(cpos.x - size.x // 2, cpos.y - size.y // 2, size.x, size.y)
        self.original_rect = self.rect.copy()
        self.border_radius = border_radius
        self.image = img

    def clicked(self, clicke):
        if self.hovered() and clicke:
            return True
        else:
            return False

    def hovered(self):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx // 2, my // 2):
            return True
        return False

    def draw(self, screen, color, hover_color, click_color, clicke, scroll=vec()):
        self.rect.topleft = self.original_rect.topleft - scroll
        if clicke and self.hovered():
            pygame.draw.rect(screen, click_color, self.rect, border_top_left_radius=self.border_radius,
                             border_bottom_right_radius=self.border_radius)
            clicke = False
        elif self.hovered():
            pygame.draw.rect(screen, hover_color, self.rect, border_top_left_radius=self.border_radius,
                             border_bottom_right_radius=self.border_radius)
        else:
            pygame.draw.rect(screen, color, self.rect, border_top_left_radius=self.border_radius,
                             border_bottom_right_radius=self.border_radius)
        screen.blit(
            self.image,
            (
                self.rect.centerx - self.image.get_rect().width // 2,
                self.rect.centery - self.image.get_rect().height // 2
            )
        )
        return clicke


class CheckBox:
    def __init__(self, center, size, text, checked=True):
        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = center
        self.check_box_rect = pygame.Rect(0, 0, size.y, size.y)
        self.check_box_rect.topright = self.rect.topright
        self.text = text
        self.font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), FONT_SIZE)
        self.checked = checked
        self.clickable = False
        self.f = 0

    def clicked(self):
        if self.hovered() and pygame.mouse.get_pressed(3)[0]:
            return True
        return False

    def hovered(self):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx // 2, my // 2):
            return True
        return False

    def draw(self, screen, color, hover_color, click_color, font_color):
        self.f += 1
        if self.f >= 22:
            self.f = 0
            self.clickable = True
        c = color
        if self.clicked() and self.clickable:
            if self.checked:
                self.checked = False
                self.clickable = False
            else:
                self.checked = True
                self.clickable = False
            c = click_color
        elif self.hovered():
            c = hover_color
        else:
            c = color

        txt_img = self.font.render(self.text, False, c).convert_alpha()
        screen.blit(txt_img, (self.rect.x, self.rect.midleft[1] - txt_img.get_rect().height / 2))

        if not self.checked:
            pygame.draw.rect(screen, c, self.check_box_rect, border_radius=10, width=2)
        else:
            pygame.draw.rect(screen, c, self.check_box_rect, border_radius=10, width=0)


class Slider:
    def __init__(self, center, size, text, percent=50):
        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = center
        self.text = text
        self.font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), FONT_SIZE)
        self.handle = pygame.Rect(0, 0, size.y // 4, size.y // 4)
        self.percent = percent
        self.handle.centery = self.rect.centery
        self.handle.centerx = self.rect.x + ((self.rect.right - self.rect.left) * (self.percent / 100))

    def clicked(self):
        if self.hovered() and pygame.mouse.get_pressed(3)[0]:
            return True
        return False

    def hovered(self):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint(mx // 2, my // 2):
            return True
        return False

    def draw(self, screen, color, hover_color, click_color, font_color):
        c = color
        if self.clicked():
            c = click_color
            mx, my = pygame.mouse.get_pos()
            if mx // 2 in range(self.rect.midleft[0], self.rect.midright[0] + 1):
                self.handle.centerx = mx // 2
        elif self.hovered():
            c = hover_color
        else:
            c = color

        self.percent = (self.handle.centerx - self.rect.left) * (100 / (self.rect.right - self.rect.left))

        txt_img = self.font.render(self.text, False, c).convert_alpha()
        pygame.draw.line(screen, c, self.rect.midleft, self.rect.midright)
        screen.blit(txt_img, (self.rect.midtop[0] - txt_img.get_width() // 2, self.rect.y))
        pygame.draw.rect(screen, c, self.handle, border_radius=10)


class Label:
    def __init__(self, center, size, text):
        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = center
        self.text = text
        self.font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), FONT_SIZE)

    def draw(self, screen, color, scroll, area):
        txt_img = self.font.render(self.text, False, color).convert_alpha()
        if area.collidepoint((self.rect.midtop[0] - txt_img.get_width() // 2) - scroll.x, self.rect.y - scroll.y):
            screen.blit(txt_img, ((self.rect.midtop[0] - txt_img.get_width() // 2) - scroll.x, self.rect.y - scroll.y))


def draw(screen, img, x, y):
    screen.blit(img, (x, y))


class Button:

    def __init__(self, img, x, y, min_size, frames=5):
        """

        :param img: pygame.Surface
        :param min_size: minimum size of image to which it will be shrunk down (during animation)
        :param frames: the number of frames to iterate over

        the x and y coordinates are according to pygame coordinate system
        """

        self.img = img  # the original image which will be shrunk down for animations
        self.w, self.h = img.get_size()  # width and height of original image
        self.x = x  # x coordinate
        self.y = y  # y coordinate
        self.mw, self.mh = min_size  # width and height of smallest frame which will be drawn
        self.frames = frames  # the number of frames over which the image will be animated

        self.frame = 0  # internal variable to keep track of on which frame the animation is on
        _, self.last_drawn_rect = self.resize_image(min_size)

    def resize_image(self, size: tuple) -> (pygame.Surface, pygame.rect.Rect):
        """
        :param size: tuple - (width, height) of new size of image
        :return: pygame.Surface and corresponding pygame rect object
        """

        n_w, n_h = size  # new width and height
        dw = self.w - n_w  # change in width
        dh = self.h - n_h  # change in height

        img = pygame.transform.scale(self.img, size)  # resizing image according to size
        rect = img.get_rect()  # making rect object
        rect.topleft = self.x + (dw / 2), self.y + (dh / 2)  # setting correct x and y coordinates for the rect object

        return img, rect

    def draw(self, screen, mouse_rect):

        if self.hover(mouse_rect):  # moving to next frame is hovered over last frame

            if self.frame < self.frames:
                self.frame += 1  # updating current frame

        else:
            if self.frame > 0:
                self.frame -= 1  # updating current frame

        w = ((self.w - self.mw) * self.frame) // self.frames + self.mw
        h = ((self.h - self.mh) * self.frame) // self.frames + self.mh
        img, rect = self.resize_image((w, h))
        draw(screen, img, rect.x, rect.y)
        self.last_drawn_rect = rect

    def hover(self, mouse_rect):
        return mouse_rect.colliderect(self.last_drawn_rect)
