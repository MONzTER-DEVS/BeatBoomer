import pygame, sys, json, random, os
from pygame.math import Vector2 as vec
from particles import ParticleSystem
from gui_stuff import RectButton

pygame.init()
pygame.mixer.init()

G = 0.05

WW, WH = 480, 640
window = pygame.display.set_mode((WW, WH))

SW, SH = 240, 320
screen = pygame.Surface((SW, SH)).convert()
vig = pygame.image.load(os.path.join("Vig.png")).convert_alpha()
BnB = pygame.image.load(os.path.join("BeatNBoom.png")).convert_alpha()

clock = pygame.time.Clock()

def game():

    ## MUSIC DATA
    with open("music_data.json") as jfile:
        music_data = json.load(jfile)

    music_name = music_data["music_name"]
    beat_times = music_data["beat_times"]
    tempo = music_data["tempo"]

    ## FONTS
    game_font = pygame.font.Font(os.path.join("fonts", "Roboto", "Roboto-Thin.ttf"), 11)

    ## MUSIC
    pygame.mixer.music.load(music_name)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(loops=-1)

    ## SFX
    sfx_crash = pygame.mixer.Sound(os.path.join("sfx", "crash2.wav"))
    sfx_boom = pygame.mixer.Sound(os.path.join("sfx", "crash.wav"))
    sfx_crash.set_volume(0.1)
    sfx_boom.set_volume(0.1)

    ## WINDOW
    visible_area = pygame.Rect(0, 0, SW, SH)
    scroll = vec(0, 0)
    shake = 0
    back_color = pygame.Color(100, 75, 60)

    ## PLAYER
    player_img = pygame.image.load("player.png").convert_alpha()
    player_rect = player_img.get_rect(center=(SW//2, SH//4))
    player_vel = vec()
    player_max_vel_y = 10
    score = 0
    score_increment = 10

    ## PICKUPS
    pickups = []
    pick_pos = [65, 120, 175]
    pick_imgs = [
        pygame.image.load(os.path.join("pickups", "one.png")).convert_alpha(),
        pygame.image.load(os.path.join("pickups", "two.png")).convert_alpha(),
        pygame.image.load(os.path.join("pickups", "three.png")).convert_alpha()
    ]
    pick_cache = pick_pos[0]

    ## PARTICLES
    # pos, vel, reduction_rate, size, num, color, spread=vec(5, 5)
    player_particle = ParticleSystem(vec(player_rect.center), vec(0, 0), 0.5, vec(5, 5), 10, (255, 255, 255), spread=vec(5, 0))
    collide_particle = ParticleSystem(vec(), vec(0, -1), 0.5, vec(10, 10), 50, (242, 166, 94), spread=vec(16, 0))
    pick_back_particle = ParticleSystem(vec(), vec(0, 0), 1, vec(16, 16), 10, (242, 166, 94), spread=vec(16, 0))

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times)//2 + 1] - beat_times[len(beat_times)//2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo)*1000))

    ## BACK CIRCLES
    circles = []
    circle_color = pygame.Color(255, 255, 255)
    for i in range(100):
        circles.append(
            [
                vec(random.randint(50, SW-50), random.randint(0, SH)),      # POSITION
                random.randint(5, 25),                                      # RADIUS
                0                                                           # PARALLAX FACTOR(?)
            ]
        )

    ## TRANSITIONS STUFF
    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH//2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH//2)
    tr_rect2.bottom = SH

    start_ticks = pygame.time.get_ticks()
    frame, beat_index = 0, 0
    while True:
        ## TIME STUFF
        seconds = (pygame.time.get_ticks() - start_ticks)/1000
        frame += 1

        ## DISPLAY STUFF
        screen.fill(back_color)
        scroll.x += (pick_pos[1] - scroll.x - SW/2) / 5
        scroll.y += (player_rect.centery + 100 - scroll.y - SH/2) / 5

        ## EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return "exit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not transitioning:
                        tr_close_start = True
                if event.key == pygame.K_LEFT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += (pick_pos[0]-player_rect.centerx)
                        # cur_x += (target_x-cur_x)*deltatime*k
                    elif player_rect.centerx == pick_pos[2]:
                        player_rect.centerx += (pick_pos[1]-player_rect.centerx)
                if event.key == pygame.K_RIGHT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[0]:
                        player_rect.centerx += (pick_pos[1]-player_rect.centerx)
                    elif player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += (pick_pos[2]-player_rect.centerx)
            # if event.type == pygame.KEYUP:
            #     if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            #         player_vel.x = 0
            if event.type == BEAT_EVENT:
                new_pick_pos = pick_pos.copy()
                new_pick_pos.remove(pick_cache)
                pick_cache = random.choice(new_pick_pos)
                i = random.choice(pick_imgs)
                pickups.append([
                    i,
                    i.get_rect(midtop=(pick_cache, visible_area.bottom))
                ])

        ## UPDATING
        # player
        player_vel.y += G
        player_rect.x += player_vel.x
        player_rect.y += player_vel.y
        if player_vel.y > player_max_vel_y:
            player_vel.y = player_max_vel_y
        elif player_vel.y < -player_max_vel_y:
            player_vel.y = -player_max_vel_y
        # particles
        player_particle.update()
        player_particle.pos = vec(player_rect.centerx - player_particle.radius.x, player_rect.top)
        player_particle.spawn()
        collide_particle.update()
        # pickups
        for i, pick in sorted(enumerate(pickups), reverse=True):
            if (pick[1].bottom+100 <= visible_area.top):
                pickups.pop(i)
            if pick[1].colliderect(player_rect):
                score += score_increment
                sfx_crash.play()
                shake = 10
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

                collide_particle.pos = vec(pickups[i][1].center)
                collide_particle.spawn()
                pickups.pop(i)
        # others
        visible_area.center = (player_rect.centerx, player_rect.centery + 100)
        ## OPENING TRANSITION
        if tr_open_start:
            transitioning = True
            tr_rect1.y -= 10
            tr_rect2.y += 10
            tr_rect2.bottom = SH
            if tr_rect1.bottom < 0 or tr_rect2.top > SH:
                tr_open_start = False
                transitioning = False

        ## CLOSING TRANSITION
        if tr_close_start:
            transitioning = True
            tr_rect1.y += 10
            tr_rect2.y -= 10
            tr_rect2.bottom = SH
            if tr_rect1.colliderect(tr_rect2):
                tr_close_start = False
                transitioning = False
                return "menu"

        ## DRAWING
        for c in circles:
            c[2] = c[1]/2
            if c[0].y-scroll.y//c[2] < -c[1]*2:
                c[0].y += SH+c[1]*4
            c_rect = pygame.draw.circle(screen, circle_color.lerp(back_color, 0.9), (c[0].x-scroll.x//c[2], c[0].y-scroll.y//c[2]), c[1])

        score_txt = game_font.render("SCORE: "+str(score), False, (255, 255, 255)).convert_alpha()
        screen.blit(score_txt, (SW//2 - score_txt.get_rect().width//2, 0))

        if shake > 0:
            scroll.x += random.randint(-4, 4)
            scroll.y += random.randint(-4, 4)
            shake -= 1
        collide_particle.draw(screen, scroll, flags=0)
        player_particle.draw(screen, scroll, lerp_color=(254, 254, 254), flags=0)
        screen.blit(player_img, (player_rect.x - scroll.x, player_rect.y - scroll.y))
        for pick in pickups:
            screen.blit(pick[0], (pick[1].x - scroll.x, pick[1].y - scroll.y))
        # screen.blit(pick_img1, (obs_rect.x - scroll.x, obs_rect.y - scroll.y))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()

def menu():
    ## FONTS
    # title_font = pygame.font.Font(os.path.join("fonts", "Roboto", "Roboto-BoldItalic.ttf"), 40)

    ## MUSIC DATA
    with open("music_data.json") as jfile:
        music_data = json.load(jfile)

    music_name = music_data["music_name"]
    beat_times = music_data["beat_times"]
    tempo = music_data["tempo"]

    ## MUSIC STUFF
    pygame.mixer.music.load(music_name)
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(loops=-1)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times)//2 + 1] - beat_times[len(beat_times)//2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo)*1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = []
    circle_color = pygame.Color(255, 255, 255)
    for i in range(100):
        circles.append(
            [
                vec(random.randint(50, SW-50), random.randint(0, SH)),      # POSITION
                random.randint(5, 25),                                      # RADIUS
                0                                                           # PARALLAX FACTOR(?)
            ]
        )

    play_button = RectButton(vec(SW//2, 2*SH//3), vec(100, 25), "PLAY")
    settings_button = RectButton(vec(SW//2, 3*SH//4), vec(100, 25), "SETTINGS")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH//2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH//2)
    tr_rect2.bottom = SH
    tr_go_to = "game"

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return "exit"
            if event.type == BEAT_EVENT:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

        if play_button.clicked() and not transitioning:
            tr_go_to = "game"
            tr_close_start = True

        if settings_button.clicked() and not transitioning:
            tr_go_to = "settings"
            tr_close_start = True

        ## OPENING TRANSITION
        if tr_open_start:
            transitioning = True
            tr_rect1.y -= 10
            tr_rect2.y += 10
            tr_rect2.bottom = SH
            if tr_rect1.bottom < 0 or tr_rect2.top > SH:
                tr_open_start = False
                transitioning = False

        ## CLOSING TRANSITION
        if tr_close_start:
            transitioning = True
            tr_rect1.y += 10
            tr_rect2.y -= 10
            tr_rect2.bottom = SH
            if tr_rect1.colliderect(tr_rect2):
                tr_close_start = False
                transitioning = False
                if tr_go_to == "game":
                    return "game"
                elif tr_go_to == "settings":
                    return "settings"

        ## drawing
        for c in circles:
            c[2] = c[1]/2
            if c[0].y-scroll.y//c[2] < -c[1]*2:
                c[0].y += SH+c[1]*4
            c_rect = pygame.draw.circle(screen, circle_color.lerp(back_color, 0.9), (c[0].x-scroll.x//c[2], c[0].y-scroll.y//c[2]), c[1])

        screen.blit(BnB, (SW//2-BnB.get_width()//2, 10))
        #
        # title_txt2 = title_font.render("BOOMER", False, (255, 255, 255)).convert_alpha()
        # screen.blit(title_txt2, (SW//2-title_txt2.get_width()//2, 60))

        play_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        settings_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()

def settings():
    ## FONTS
    # title_font = pygame.font.Font(os.path.join("fonts", "Roboto", "Roboto-BoldItalic.ttf"), 40)

    ## MUSIC DATA
    with open("music_data.json") as jfile:
        music_data = json.load(jfile)

    music_name = music_data["music_name"]
    beat_times = music_data["beat_times"]
    tempo = music_data["tempo"]

    ## MUSIC STUFF
    pygame.mixer.music.load(music_name)
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(loops=-1)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times)//2 + 1] - beat_times[len(beat_times)//2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo)*1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = []
    circle_color = pygame.Color(255, 255, 255)
    for i in range(100):
        circles.append(
            [
                vec(random.randint(50, SW-50), random.randint(0, SH)),      # POSITION
                random.randint(5, 25),                                      # RADIUS
                0                                                           # PARALLAX FACTOR(?)
            ]
        )

    back_button = RectButton(vec(SW//2, SH-25), vec(100, 25), "BACK")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH//2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH//2)
    tr_rect2.bottom = SH
    tr_go_to = "menu"

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return "exit"
            if event.type == BEAT_EVENT:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

        ## CLICKS
        if back_button.clicked() and not transitioning:
            tr_go_to = "menu"
            tr_close_start = True

        ## OPENING TRANSITION
        if tr_open_start:
            transitioning = True
            tr_rect1.h -= 10
            tr_rect2.h -= 10
            tr_rect2.bottom = SH
            if tr_rect1.bottom < 0 or tr_rect2.top > SH:
                tr_open_start = False
                transitioning = False

        ## CLOSING TRANSITION
        if tr_close_start:
            transitioning = True
            tr_rect1.h += 10
            tr_rect2.h += 10
            tr_rect2.bottom = SH
            if tr_rect1.colliderect(tr_rect2):
                tr_close_start = False
                transitioning = False
                if tr_go_to == "menu":
                    return "menu"

        ## drawing
        for c in circles:
            c[2] = c[1]/2
            if c[0].y-scroll.y//c[2] < -c[1]*2:
                c[0].y += SH+c[1]*4
            c_rect = pygame.draw.circle(screen, circle_color.lerp(back_color, 0.9), (c[0].x-scroll.x//c[2], c[0].y-scroll.y//c[2]), c[1])

        back_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))

        #
        # title_txt2 = title_font.render("BOOMER", False, (255, 255, 255)).convert_alpha()
        # screen.blit(title_txt2, (SW//2-title_txt2.get_width()//2, 60))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()

scene = "menu"

while True:
    if scene == "menu":
        scene = menu()
    elif scene == "game":
        scene = game()
    elif scene == "settings":
        scene = settings()
    elif scene == "exit":
        break
