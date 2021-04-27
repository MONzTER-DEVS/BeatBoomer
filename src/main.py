import tkinter.filedialog
from tkinter import Tk

import json
import os
import pygame
# import pygame.gfxdraw
import random
import sys
import threading
import math
from pygame.math import Vector2 as vec

from imports.gui_stuff import RectButton, CheckBox, Slider
from imports.load_music import load_music
from imports.particles import ParticleSystem

pygame.init()
pygame.mixer.init()

G = 0.05

WW, WH = 480, 640
window = pygame.display.set_mode((WW, WH))

SW, SH = 240, 320
screen = pygame.Surface((SW, SH)).convert()
vig = pygame.image.load(os.path.join("assets/Vig.png")).convert_alpha()
BnB = pygame.image.load(os.path.join("assets/BeatNBoom.png")).convert_alpha()

clock = pygame.time.Clock()

## SFX
sfx_crash = pygame.mixer.Sound(os.path.join("assets", "sfx", "crash2.wav"))
sfx_boom = pygame.mixer.Sound(os.path.join("assets", "sfx", "crash.wav"))
sfx_hit = pygame.mixer.Sound(os.path.join("assets", "sfx", "crash5.wav"))
sfx_crash.set_volume(0.1)
sfx_boom.set_volume(0.1)
sfx_hit.set_volume(0.5)

## UTILITY FUNCTIONS
def prompt_file():
    """Create a Tk file dialog and cleanup when finished"""
    top = Tk()
    top.withdraw()  # hide window
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    return file_name


def change_music():
    global music_path, beat_times, tempo, music_name, producer_name
    path = prompt_file()
    # f_name = path.split("/")[-1]
    if path != ():
        music_name = os.path.split(path)[-1]
        if ".ogg" in music_name:
            load_music(path)
            music_path, beat_times, tempo = load_music_data()
            producer_name = os.path.basename(os.path.dirname(music_path))
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(loops=-1)
            except pygame.error:
                pass
    return 0


def spawn_background_circles():
    circles = []
    for i in range(250):
        circles.append(
            [
                vec(random.gauss(SW / 2, SW / 8), random.randint(0, SH)),  # POSITION
                random.randint(2, 15),  # RADIUS
                0  # PARALLAX FACTOR(?)
            ]
        )
    return circles


def draw_background_circles(circles, circle_color, back_color, scroll):
    for c in circles:
        c[2] = c[1] / 2
        if c[0].y - scroll.y // c[2] < -c[1] * 2:
            c[0].y += SH + c[1] * 4
        c_rect = pygame.draw.circle(screen, circle_color.lerp(back_color, 0.9),
                                    (c[0].x - scroll.x // c[2], c[0].y - scroll.y // c[2]), c[1])


def warp_value(value, min, max):
    if value <= min:
        return max
    elif value > max:
        return min
    else:
        return value


def play_music():
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(data["volume"] / 100)
    pygame.mixer.music.play(loops=-1)


## SCENES
def game():
    ## FONTS
    game_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 11)

    ## MUSIC
    play_music()

    ## WINDOW
    visible_area = pygame.Rect(0, 0, SW, SH)
    scroll = vec(0, 0)
    shake = 0
    back_color = pygame.Color(100, 75, 60)

    ## PLAYER
    player_img = pygame.image.load("assets/player.png").convert_alpha()
    player_rect = player_img.get_rect(center=(SW // 2, SH // 4))
    player_vel = vec(0, 5)
    player_max_vel_y = 10
    score = 0
    score_increment = 10

    ## PICKUPS
    pickups = []
    pick_pos = [65, 120, 175]
    pick_imgs = [
        pygame.image.load(os.path.join("assets/pickups", "one.png")).convert_alpha(),
        pygame.image.load(os.path.join("assets/pickups", "two.png")).convert_alpha(),
        pygame.image.load(os.path.join("assets/pickups", "three.png")).convert_alpha()
    ]
    pick_cache = pick_pos[0]

    ## PARTICLES
    # pos, vel, reduction_rate, size, num, color, spread=vec(5, 5)
    player_particle = ParticleSystem(vec(player_rect.center), vec(0, 0), 0.5, vec(5, 5), 10, (255, 255, 255),
                                     spread=vec(5, 0))
    collide_particle = ParticleSystem(vec(), vec(0, -1), 0.5, vec(10, 10), 50, (242, 166, 94), spread=vec(16, 0))
    pick_back_particle = ParticleSystem(vec(), vec(0, 0), 1, vec(16, 16), 10, (242, 166, 94), spread=vec(16, 0))

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    ## TRANSITIONS STUFF
    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH

    start_ticks = pygame.time.get_ticks()
    frame, beat_index = 0, 0
    while True:
        ## TIME STUFF
        seconds = (pygame.time.get_ticks() - start_ticks) / 1000
        frame += 1

        ## DISPLAY STUFF
        screen.fill(back_color)
        scroll.x += (pick_pos[1] - scroll.x - SW / 2) / 5
        scroll.y += (player_rect.centery + 100 - scroll.y - SH / 2) / 5

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
                        # pygame.mixer.music.fadeout(1000)
                        # pygame.mixer.music.play(loops=-1)
                if event.key == pygame.K_LEFT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += (pick_pos[0] - player_rect.centerx)
                        # cur_x += (target_x-cur_x)*deltatime*k
                    elif player_rect.centerx == pick_pos[2]:
                        player_rect.centerx += (pick_pos[1] - player_rect.centerx)
                if event.key == pygame.K_RIGHT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[0]:
                        player_rect.centerx += (pick_pos[1] - player_rect.centerx)
                    elif player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += (pick_pos[2] - player_rect.centerx)
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
            if (pick[1].bottom + 100 <= visible_area.top):
                pickups.pop(i)
            if pick[1].colliderect(player_rect):
                score += score_increment
                sfx_crash.play()
                shake = 10
                if data["back_change"]:
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
                return "menu"

        ## DRAWING
        draw_background_circles(circles, circle_color, back_color, scroll)

        score_txt = game_font.render("SCORE: " + str(score), False, (255, 255, 255)).convert_alpha()
        score_txt.set_alpha(200)
        screen.blit(score_txt, (SW // 2 - score_txt.get_rect().width // 2, 0))

        music_txt = game_font.render("PLAYING" + music_name + " BY " + producer_name, False,
                                     (255, 255, 255)).convert_alpha()
        music_txt.set_alpha(200)
        screen.blit(music_txt, (SW // 2 - music_txt.get_rect().width // 2, SH - music_txt.get_height()))

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


def obs_mode():
    ## FONTS
    game_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 11)

    ## MUSIC
    play_music()

    ## WINDOW
    visible_area = pygame.Rect(0, 0, SW, SH)
    scroll = vec(0, 0)
    shake = 0
    back_color = pygame.Color(100, 75, 60)
    blood_overlay = pygame.Surface((SW, SH))
    blood_overlay.fill((255, 255, 255))
    blood_alpha = 0
    blood_overlay.set_alpha(blood_alpha)

    ## PLAYER
    player_img = pygame.image.load("assets/player.png").convert_alpha()
    player_rect = player_img.get_rect(center=(SW // 2, SH // 4))
    player_vel = vec(0, 5)
    player_max_vel_y = 10
    score = 0
    score_increment = 10

    ## PICKUPS
    pickups = []
    pick_pos = [65, 120, 175]
    pick_imgs = [
        pygame.image.load(os.path.join("assets/pickups", "one.png")).convert_alpha(),
        pygame.image.load(os.path.join("assets/pickups", "two.png")).convert_alpha(),
        pygame.image.load(os.path.join("assets/pickups", "three.png")).convert_alpha()
    ]
    pick_cache = pick_pos[0]

    ## OBSTACLES
    obstacles = []
    obs_img = pygame.image.load(os.path.join("assets", "obs.png")).convert_alpha()
    obs_pos = pick_pos.copy()

    ## PARTICLES
    # pos, vel, reduction_rate, size, num, color, spread=vec(5, 5)
    player_particle = ParticleSystem(vec(player_rect.center), vec(0, 0), 0.5, vec(5, 5), 10, (255, 255, 255),
                                     spread=vec(5, 0))
    collide_particle = ParticleSystem(vec(), vec(0, -1), 0.5, vec(10, 10), 50, (242, 166, 94), spread=vec(16, 0))
    pick_back_particle = ParticleSystem(vec(), vec(0, 0), 1, vec(16, 16), 10, (242, 166, 94), spread=vec(16, 0))

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    ## TRANSITIONS STUFF
    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH

    start_ticks = pygame.time.get_ticks()
    frame, beat_index = 0, 0
    while True:
        ## TIME STUFF
        seconds = (pygame.time.get_ticks() - start_ticks) / 1000
        frame += 1

        ## DISPLAY STUFF
        screen.fill(back_color)
        scroll.x += (pick_pos[1] - scroll.x - SW / 2) / 5
        scroll.y += (player_rect.centery + 100 - scroll.y - SH / 2) / 5

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
                        # pygame.mixer.music.fadeout(1000)
                        # pygame.mixer.music.play(loops=-1)
                if event.key == pygame.K_LEFT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += (pick_pos[0] - player_rect.centerx)
                        # cur_x += (target_x-cur_x)*deltatime*k
                    elif player_rect.centerx == pick_pos[2]:
                        player_rect.centerx += (pick_pos[1] - player_rect.centerx)
                if event.key == pygame.K_RIGHT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[0]:
                        player_rect.centerx += (pick_pos[1] - player_rect.centerx)
                    elif player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += (pick_pos[2] - player_rect.centerx)
            # if event.type == pygame.KEYUP:
            #     if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            #         player_vel.x = 0
            if event.type == BEAT_EVENT:
                new_pick_pos = pick_pos.copy()
                new_pick_pos.remove(pick_cache)
                obstacles.append(obs_img.get_rect(midtop=(pick_cache, visible_area.bottom)))
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
            if (pick[1].bottom + 100 <= visible_area.top):
                pickups.pop(i)
            if pick[1].colliderect(player_rect):
                score += score_increment
                sfx_crash.play()
                shake = 10
                if data["back_change"]:
                    back_color.r = random.randint(50, 100)
                    back_color.g = random.randint(50, 100)
                    back_color.b = random.randint(50, 100)

                collide_particle.pos = vec(pickups[i][1].center)
                collide_particle.spawn()
                pickups.pop(i)

        ## OBSTACLES
        for i, obs in sorted(enumerate(obstacles), reverse=True):
            if (obs.bottom + 100 <= visible_area.top):
                # print(len(sorted(enumerate(obstacles), reverse=True)))
                obstacles.pop(i)
            if obs.colliderect(player_rect):
                score -= score_increment
                player_vel.y -= 1
                sfx_hit.play()
                # shake = 10
                # if data["back_change"]:
                #     back_color.r = random.randint(50, 100)
                #     back_color.g = random.randint(50, 100)
                #     back_color.b = random.randint(50, 100)
                # print("YOU DED... HUH")
                blood_alpha += 100
                back_color.r += 10
                # collide_particle.pos = vec(obstacles[i].center)
                # collide_particle.spawn()
                obstacles.pop(i)
        # others
        if blood_alpha > 0:
            blood_alpha -= 10
        blood_overlay.set_alpha(blood_alpha)
        blood_overlay.fill((255, 0, 0))
        visible_area.center = (player_rect.centerx, player_rect.centery + 100)


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
                return "menu"

        ## DRAWING
        draw_background_circles(circles, circle_color, back_color, scroll)

        score_txt = game_font.render("SCORE: " + str(score), False, (255, 255, 255)).convert_alpha()
        score_txt.set_alpha(200)
        screen.blit(score_txt, (SW // 2 - score_txt.get_rect().width // 2, 0))

        music_txt = game_font.render("PLAYING" + music_name + " BY " + producer_name, False,
                                     (255, 255, 255)).convert_alpha()
        music_txt.set_alpha(200)
        screen.blit(music_txt, (SW // 2 - music_txt.get_rect().width // 2, SH - music_txt.get_height()))

        if shake > 0:
            scroll.x += random.randint(-4, 4)
            scroll.y += random.randint(-4, 4)
            shake -= 1
        collide_particle.draw(screen, scroll, flags=0)
        player_particle.draw(screen, scroll, lerp_color=(254, 254, 254), flags=0)
        screen.blit(player_img, (player_rect.x - scroll.x, player_rect.y - scroll.y))
        for pick in pickups:
            screen.blit(pick[0], (pick[1].x - scroll.x, pick[1].y - scroll.y))
        for obs in obstacles:
            screen.blit(obs_img, (obs.x - scroll.x, obs.y - scroll.y))
            # pygame.draw.rect(screen, (255, 0, 2), [obs.x-scroll.x, obs.y-scroll.y, obs.w, obs.h], border_radius=10)
        # screen.blit(pick_img1, (obs_rect.x - scroll.x, obs_rect.y - scroll.y))

        screen.blit(blood_overlay, (0, 0))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()


def menu():
    ## FONTS
    # title_font = pygame.font.Font(os.path.join("fonts", "Roboto", "Roboto-BoldItalic.ttf"), 40)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    play_button = RectButton(vec(SW // 2, 3 * SH // 5), vec(100, 25), "PLAY")
    # customize_button = RectButton(vec(SW//2, play_button.rect.bottom + 15), vec(100, 25), "CUSTOMIZE")
    settings_button = RectButton(vec(SW // 2, play_button.rect.bottom + 15), vec(100, 25), "SETTINGS")
    exit_button = RectButton(vec(SW // 2, settings_button.rect.bottom + 15), vec(100, 25), "QUIT")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
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
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

        if play_button.clicked() and not transitioning:
            tr_go_to = "mode_select"
            tr_close_start = True

        # if customize_button.clicked() and not transitioning:
        #     tr_go_to = "customize"
        #     tr_close_start = True

        if settings_button.clicked() and not transitioning:
            tr_go_to = "settings"
            tr_close_start = True

        if exit_button.clicked() and not transitioning:
            tr_go_to = "exit"
            tr_close_start = True
            pygame.mixer.music.fadeout(1000)

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
                return tr_go_to

        ## drawing
        draw_background_circles(circles, circle_color, back_color, scroll)

        screen.blit(BnB, (SW // 2 - BnB.get_width() // 2, 10))
        #
        # title_txt2 = title_font.render("BOOMER", False, (255, 255, 255)).convert_alpha()
        # screen.blit(title_txt2, (SW//2-title_txt2.get_width()//2, 60))

        play_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        settings_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        # customize_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        exit_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()


def settings():
    global change_music_thread
    ## FONTS
    title_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-BoldItalic.ttf"), 40)
    norm_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 15)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    volume_slider = Slider(vec(SW // 2, 90), vec(SW - 50, 60), "MUSIC VOLUME", percent=data["volume"])
    back_changing = CheckBox(vec(SW // 2, 140), vec(SW - 50, 32), "COLOR CHANGE", checked=data["back_change"])
    change_music_button = RectButton(vec(SW // 2, 190), vec(SW - 100, 25), "CHANGE MUSIC")
    back_button = RectButton(vec(60, SH - 25), vec(100, 25), "BACK")
    save_button = RectButton(vec(SW - 60, SH - 25), vec(100, 25), "APPLY")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "menu"

    to_write = data
    # music_path_to_write = music_path

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return "exit"
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

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
                return tr_go_to

        ## CLICKS
        if change_music_button.clicked() and not transitioning:
            # music_path = prompt_file()
            change_music_thread = threading.Thread(target=change_music)
            change_music_thread.setDaemon(True)
            change_music_thread.start()

        if back_button.clicked() and not transitioning:
            tr_go_to = "menu"
            tr_close_start = True

        if save_button.clicked() and not transitioning:
            if change_music_thread.is_alive():
                tr_go_to = "loading"
            else:
                tr_go_to = "menu"
            with open("assets/data/data.json", "w") as jfile:
                json.dump(to_write, jfile)
            # return "loading"
            tr_close_start = True

        ## drawing
        draw_background_circles(circles, circle_color, back_color, scroll)

        back_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        save_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        change_music_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97),
                                 (0, 0, 0))
        volume_slider.draw(screen, (255, 255, 255), back_color.lerp((255, 200, 200), 0.9), (255, 140, 97),
                           (255, 255, 255))
        back_changing.draw(screen, (255, 255, 255), back_color.lerp((255, 200, 200), 0.9), (255, 140, 97),
                           (255, 255, 255))

        to_write["volume"] = volume_slider.percent
        to_write["back_change"] = back_changing.checked
        pygame.mixer.music.set_volume(volume_slider.percent / 100)

        title_txt = title_font.render("SETTINGS", False, (255, 255, 255))
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 0))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()


def loading(thread, nxt_scene):
    ## FONTS
    title_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Light.ttf"), 15)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "game"

    pygame.mixer.music.fadeout(1000)
    l_circle_start = 0
    l_circle_end = 90
    l_circle_rect1 = pygame.Rect(0, 0, 64, 64)
    l_circle_rect1.center = (SW//2, SH//2)

    l_circle_rect2 = pygame.Rect(0, 0, 60, 60)
    l_circle_rect2.center = (SW//2, SH//2)

    l_circle_rect3 = pygame.Rect(0, 0, 56, 56)
    l_circle_rect3.center = (SW//2, SH//2)

    f = 1

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return "exit"
            # if event.type == BEAT_EVENT and data["back_change"]:
            #     back_color.r = random.randint(50, 100)
            #     back_color.g = random.randint(50, 100)
            #     back_color.b = random.randint(50, 100)

        # if play_button.clicked() and not transitioning:
        #     tr_go_to = "game"
        #     tr_close_start = True
        #     pygame.mixer.music.fadeout(1000)

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
                return tr_go_to


        if l_circle_end - l_circle_start == 0:
            f = -1

        print(l_circle_end - l_circle_start)

        l_circle_start += 5 * f
        l_circle_end += 5.5 * f
        l_circle_start = warp_value(l_circle_start, 0, 360)
        l_circle_end = warp_value(l_circle_end, 0, 360)

        ## drawing
        draw_background_circles(circles, circle_color, back_color, scroll)

        #
        title_txt = title_font.render("LOADING...", False, (255, 255, 255)).convert_alpha()
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 60))

        pygame.draw.arc(screen, (255, 255, 255), l_circle_rect1, math.radians(l_circle_start), math.radians(l_circle_end), width=1)
        pygame.draw.arc(screen, (255, 255, 255), l_circle_rect2, math.radians(l_circle_start-45), math.radians(l_circle_end-45), width=1)
        pygame.draw.arc(screen, (255, 255, 255), l_circle_rect3, math.radians(l_circle_start-90), math.radians(l_circle_end-90), width=1)
        # pygame.gfxdraw.arc(screen, SW//2, SH//2, 32, l_circle_start, l_circle_end, (255, 255, 255))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        if not thread.is_alive():
            return nxt_scene
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()


def splash():
    ## MONZTER DEVS src/assets/MonzterDevs.png
    MzR = pygame.image.load(os.path.join("assets", "MonzterDevs1.png")).convert_alpha()
    bloom = pygame.image.load(os.path.join("assets", "Bloom200x200.png")).convert_alpha()
    overlay = pygame.Surface((SW, SH)).convert_alpha()
    overlay.set_alpha(125)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "menu"

    op = 0

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return "exit"
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

        # if play_button.clicked() and not transitioning:
        #     tr_go_to = "game"
        #     tr_close_start = True
        #     pygame.mixer.music.fadeout(1000)

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
                return tr_go_to

        ## drawing
        draw_background_circles(circles, circle_color, back_color, scroll)

        op += 1
        bloom.set_alpha(op // 2)
        MzR.set_alpha(op)

        if op >= 255:
            tr_close_start = True

        screen.blit(overlay, (0, 0))
        screen.blit(bloom, (SW // 2 - bloom.get_width() // 2, SH // 2 - bloom.get_height() // 2))
        screen.blit(MzR, (SW // 2 - MzR.get_width() // 2, SH // 2 - MzR.get_height() // 2))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()


def mode_select():
    ## FONTS
    title_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-BoldItalic.ttf"), 30)
    norm_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 15)

    ## BEAT STUFF
    BEAT_EVENT = pygame.USEREVENT + 1
    tempo = beat_times[len(beat_times) // 2 + 1] - beat_times[len(beat_times) // 2]
    pygame.time.set_timer(BEAT_EVENT, int((tempo) * 1000))

    ## WINDOW STUFF
    scroll = vec()
    back_color = pygame.Color(155, 100, 100)

    ## BACK CIRCLES
    circles = spawn_background_circles()
    circle_color = pygame.Color(255, 255, 255)

    zen_button = RectButton(vec(SW // 2, SH//2-20), vec(SW - 100, 25), "ZEN MODE")
    normal_button = RectButton(vec(SW // 2, zen_button.rect.bottom + 20), vec(SW - 100, 25), "NORMAL MODE")
    back_button = RectButton(vec(SW//2, SH - 25), vec(100, 25), "BACK")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
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
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)

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
                return tr_go_to

        ## CLICKS
        if back_button.clicked() and not transitioning:
            tr_go_to = "menu"
            tr_close_start = True
        if zen_button.clicked() and not transitioning:
            tr_go_to = "game"
            tr_close_start = True
            pygame.mixer.music.fadeout(1000)
        if normal_button.clicked() and not transitioning:
            tr_go_to = "obs_mode"
            tr_close_start = True
            pygame.mixer.music.fadeout(1000)

        ## drawing
        draw_background_circles(circles, circle_color, back_color, scroll)

        back_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        zen_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))
        normal_button.draw(screen, (255, 255, 255), back_color.lerp((155, 100, 100), 0.25), (255, 140, 97), (0, 0, 0))

        title_txt = title_font.render("CHANGE MODE", False, (255, 255, 255))
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 0))

        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect1, border_radius=10)
        pygame.draw.rect(screen, pygame.Color(255, 255, 255).lerp(back_color, 0.5), tr_rect2, border_radius=10)

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()



## THREADS
change_music_thread = threading.Thread(target=change_music)
change_music_thread.setDaemon(True)

## MUSIC DATA
def load_music_data():
    with open("assets/data/music_data.json") as jfile:
        music_data = json.load(jfile)

    music_path = music_data["music_name"]
    beat_times = music_data["beat_times"]
    tempo = music_data["tempo"]
    return music_path, beat_times, tempo


music_path, beat_times, tempo = load_music_data()

music_name = os.path.split(music_path)[-1]
producer_name = os.path.basename(os.path.dirname(music_path))

## NORMAL DATA
with open("assets/data/data.json") as jfile1:
    data = json.load(jfile1)

## MUSIC STUFF
pygame.mixer.music.load(music_path)
pygame.mixer.music.set_volume(data["volume"] / 100)
pygame.mixer.music.play(loops=-1)

scene = "obs_mode"

while True:
    if scene == "splash":
        scene = splash()
    elif scene == "menu":
        scene = menu()
    elif scene == "game":
        scene = game()
    elif scene == "mode_select":
        scene = mode_select()
    elif scene == "obs_mode":
        scene = obs_mode()
    elif scene == "settings":
        scene = settings()
    elif scene == "loading":
        scene = loading(change_music_thread, "menu")
    elif scene == "exit":
        pygame.quit()
        sys.exit()
        break
