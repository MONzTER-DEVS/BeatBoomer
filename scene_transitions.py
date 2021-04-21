# import pygame, sys

# def simple_scene_transition(WW, WH, window, screen):
#     # d = pygame.Surface((screen.get_width(), screen.get_height()))
#     r1 = pygame.Rect(0, 0, screen.get_width(), 100)
#     r2 = pygame.Rect(0, 0, screen.get_width(), 100)
#     r2.bottom = screen.get_height()
#     # screen.fill((255, 0, 0))
#     while True:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 sys.exit()
#                 return "exit"
#
#         ## DRAWING
#         pygame.draw.rect(screen, (255, 255, 255), r1)
#         pygame.draw.rect(screen, (255, 255, 255), r2)
#
#         ## WINDOW UPDATING
#         window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
#         # clock.tick(45)
#         pygame.display.flip()
