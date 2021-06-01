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
import webbrowser
from pygame.math import Vector2 as vec

from imports.gui_stuff import RectButton, CheckBox, Slider, Label, RectButtonImg
from imports.load_music import load_music
from imports.particles import ParticleSystem
from imports.rich_presence import RichPresence
from imports.more_games import get_more_games
import imports.high_scores as high_scores
from imports.debug import debug
pygame.init()
pygame.mixer.init()
rp = RichPresence()

G = 0.05

WW, WH = 480, 640
window = pygame.display.set_mode((WW, WH))
pygame.display.set_caption("Beat n' Boom")
pygame.display.set_icon(pygame.image.load(os.path.join("assets", "BeatNBoom.png")))

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



def set_sfx_vol(percent):
    sfx_crash.set_volume(percent / 100)
    sfx_boom.set_volume(percent / 100)
    sfx_hit.set_volume(percent / 100)


## UTILITY FUNCTIONS
def prompt_file():
    """Create a Tk file dialog and cleanup when finished"""
    top = Tk()
    top.withdraw()  # hide window
    file_name = tkinter.filedialog.askopenfilename(
        parent=top, filetypes=[("Audio Files", ".wav .ogg .mp3")]
    )
    top.destroy()
    return file_name


def change_music():
    global music_path, beat_times, tempo, music_name, producer_name
    path = prompt_file()
    # f_name = path.split("/")[-1]
    try:
        music_name = os.path.split(path)[-1]
        load_music(path)
        music_path, beat_times, tempo = load_music_data()
        producer_name = os.path.basename(os.path.dirname(music_path))
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(loops=-1)
    except Exception as e:
        pass


def spawn_background_circles():
    circles = []
    for i in range(250):
        circles.append(
            [
                vec(random.gauss(SW / 2, SW / 8), random.randint(0, SH)),  # POSITION
                random.randint(2, 15),  # RADIUS
                0,  # PARALLAX FACTOR(?)
            ]
        )
    return circles


def draw_background_circles(circles, circle_color, back_color, scroll):
    for c in circles:
        c[2] = c[1] / 2
        if c[0].y - scroll.y // c[2] < -c[1] * 2:
            c[0].y += SH + c[1] * 4
        c_rect = pygame.draw.circle(
            screen,
            circle_color.lerp(back_color, 0.9),
            (c[0].x - scroll.x // c[2], c[0].y - scroll.y // c[2]),
            c[1],
        )


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


def clamp(value, mini, maxi):
    if value <= mini:
        return mini
    elif value >= maxi:
        return maxi
    return value


## SCENES
def game():
    ## FONTS
    game_font = pygame.font.Font(
        os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 11
    )

    ## MUSIC
    play_music()

    ## WINDOW
    visible_area = pygame.Rect(0, 0, SW, SH)
    scroll = vec(0, 0)
    shake = 0
    back_color = pygame.Color(100, 75, 60)
    playtime = [0, 0, 0]

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
        pygame.image.load(os.path.join("assets/pickups", "three.png")).convert_alpha(),
    ]
    pick_cache = pick_pos[0]

    ## PARTICLES
    # pos, vel, reduction_rate, size, num, color, spread=vec(5, 5)
    player_particle = ParticleSystem(
        vec(player_rect.center),
        vec(0, 0),
        0.5,
        vec(5, 5),
        10,
        (255, 255, 255),
        spread=vec(5, 0),
    )
    collide_particle = ParticleSystem(
        vec(), vec(0, -1), 0.5, vec(10, 10), 50, (242, 166, 94), spread=vec(16, 0)
    )
    pick_back_particle = ParticleSystem(
        vec(), vec(0, 0), 1, vec(16, 16), 10, (242, 166, 94), spread=vec(16, 0)
    )

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
                high_scores.save_score(music_name, score)
                pygame.quit()
                return "exit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not transitioning:
                        tr_close_start = True
                        high_scores.save_score(music_name, score)
                        # pygame.mixer.music.fadeout(1000)
                        # pygame.mixer.music.play(loops=-1)
                if event.key == pygame.K_LEFT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += pick_pos[0] - player_rect.centerx
                        # cur_x += (target_x-cur_x)*deltatime*k
                    elif player_rect.centerx == pick_pos[2]:
                        player_rect.centerx += pick_pos[1] - player_rect.centerx
                if event.key == pygame.K_RIGHT:
                    sfx_boom.play()
                    if player_rect.centerx == pick_pos[0]:
                        player_rect.centerx += pick_pos[1] - player_rect.centerx
                    elif player_rect.centerx == pick_pos[1]:
                        player_rect.centerx += pick_pos[2] - player_rect.centerx
            # if event.type == pygame.KEYUP:
            #     if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            #         player_vel.x = 0
            if event.type == BEAT_EVENT:
                new_pick_pos = pick_pos.copy()
                new_pick_pos.remove(pick_cache)
                pick_cache = random.choice(new_pick_pos)
                i = random.choice(pick_imgs)
                pickups.append(
                    [i, i.get_rect(midtop=(pick_cache, visible_area.bottom))]
                )

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
        player_particle.pos = vec(
            player_rect.centerx - player_particle.radius.x, player_rect.top
        )
        player_particle.spawn()
        collide_particle.update()
        # pickups
        for i, pick in sorted(enumerate(pickups), reverse=True):
            if pick[1].bottom + 100 <= visible_area.top:
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

        score_txt = game_font.render(
            "SCORE: " + str(score), False, (255, 255, 255)
        ).convert_alpha()
        score_txt.set_alpha(200)
        screen.blit(score_txt, (SW // 2 - score_txt.get_rect().width // 2, 0))

        music_txt = game_font.render(
            "PLAYING" + music_name + " BY " + producer_name, False, (255, 255, 255)
        ).convert_alpha()
        music_txt.set_alpha(200)
        screen.blit(
            music_txt,
            (SW // 2 - music_txt.get_rect().width // 2, SH - music_txt.get_height()),
        )

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

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        rp.update_rich_presence(f"Score: {score}, Music: {music_name}")
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

    play_button = RectButton(vec(SW // 2, SH - 130), vec(100, 25), "PLAY")
    more_games_button = RectButton(
        vec(SW // 2, play_button.rect.bottom + 15), vec(100, 25), "MORE GAMES"
    )
    high_scr_button = RectButton(
        vec(SW // 2, more_games_button.rect.bottom + 15), vec(100, 25), "SCORES"
    )
    settings_button = RectButton(
        vec(SW // 2, high_scr_button.rect.bottom + 15), vec(100, 25), "SETTINGS"
    )
    exit_button = RectButton(
        vec(SW // 2, settings_button.rect.bottom + 15), vec(100, 25), "QUIT"
    )
    disc_button = RectButtonImg(
        vec(SW - 30, SH - 30),
        vec(40, 40),
        pygame.image.load(
            os.path.join("assets", "Discord-Logo-Black.png")
        ).convert_alpha()
    )
    github_button = RectButtonImg(
        vec(30, SH - 30),
        vec(40, 40),
        pygame.image.load(
            os.path.join("assets", "GitHub-Mark.png")
        ).convert_alpha()
    )

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "game"

    clicked = False

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "exit"
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                clicked = False

        if play_button.clicked() and not transitioning:
            tr_go_to = "game"
            tr_close_start = True

        if more_games_button.clicked() and not transitioning:
            tr_go_to = "more_games"
            tr_close_start = True

        if high_scr_button.clicked() and not transitioning:
            tr_go_to = "high_score"
            tr_close_start = True

        if settings_button.clicked() and not transitioning:
            tr_go_to = "settings"
            tr_close_start = True

        if disc_button.clicked(clicked) and not transitioning:
            webbrowser.open("https://discord.gg/JWsuCXSwnp")

        if github_button.clicked(clicked) and not transitioning:
            webbrowser.open("https://github.com/monzter-devs/")

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

        play_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )

        more_games_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )

        settings_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )
        high_scr_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )
        exit_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )

        clicked = disc_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            clicked
        )

        clicked = github_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            clicked
        )

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        rp.update_rich_presence("Idling in menu...")
        pygame.display.update()


def settings():
    global change_music_thread
    ## FONTS
    title_font = pygame.font.Font(
        os.path.join("assets/fonts", "Roboto", "Roboto-BoldItalic.ttf"), 40
    )
    norm_font = pygame.font.Font(
        os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 15
    )

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

    volume_slider = Slider(
        vec(SW // 2, 90), vec(SW - 50, 60), "MUSIC VOLUME", percent=data["volume"]
    )
    sfx_slider = Slider(
        vec(SW // 2, 140), vec(SW - 50, 60), "SFX VOLUME", percent=data["sfx"]
    )
    back_changing = CheckBox(
        vec(SW // 2, 190), vec(SW - 50, 32), "COLOR CHANGE", checked=data["back_change"]
    )
    change_music_button = RectButton(
        vec(SW // 2, 240), vec(SW - 100, 25), "CHANGE MUSIC"
    )
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

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
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

        back_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )
        save_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )
        change_music_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )
        volume_slider.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((255, 200, 200), 0.9),
            (255, 140, 97),
            (255, 255, 255),
        )
        sfx_slider.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((255, 200, 200), 0.9),
            (255, 140, 97),
            (255, 255, 255),
        )
        back_changing.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((255, 200, 200), 0.9),
            (255, 140, 97),
            (255, 255, 255),
        )

        to_write["volume"] = volume_slider.percent
        to_write["back_change"] = back_changing.checked
        to_write["sfx"] = sfx_slider.percent
        pygame.mixer.music.set_volume(volume_slider.percent / 100)
        set_sfx_vol(sfx_slider.percent)

        title_txt = title_font.render("SETTINGS", False, (255, 255, 255))
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 0))

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        rp.update_rich_presence("Tweaking settings...")
        clock.tick(45)
        pygame.display.update()


def loading(thread, nxt_scene):
    ## FONTS
    title_font = pygame.font.Font(
        os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 15
    )

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
    l_circle_rect1.center = (SW // 2, SH // 2)

    l_circle_rect2 = pygame.Rect(0, 0, 60, 60)
    l_circle_rect2.center = (SW // 2, SH // 2)

    l_circle_rect3 = pygame.Rect(0, 0, 56, 56)
    l_circle_rect3.center = (SW // 2, SH // 2)

    f = 1

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
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

        l_circle_start += 5 * f
        l_circle_end += 5.5 * f
        l_circle_start = warp_value(l_circle_start, 0, 360)
        l_circle_end = warp_value(l_circle_end, 0, 360)

        ## drawing
        draw_background_circles(circles, circle_color, back_color, scroll)

        #
        title_txt = title_font.render(
            "LOADING...", False, (255, 255, 255)
        ).convert_alpha()
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 60))

        pygame.draw.arc(
            screen,
            (255, 255, 255),
            l_circle_rect1,
            math.radians(l_circle_start),
            math.radians(l_circle_end),
            width=1,
        )
        pygame.draw.arc(
            screen,
            (255, 255, 255),
            l_circle_rect2,
            math.radians(l_circle_start - 45),
            math.radians(l_circle_end - 45),
            width=1,
        )
        pygame.draw.arc(
            screen,
            (255, 255, 255),
            l_circle_rect3,
            math.radians(l_circle_start - 90),
            math.radians(l_circle_end - 90),
            width=1,
        )
        # pygame.gfxdraw.arc(screen, SW//2, SH//2, 32, l_circle_start, l_circle_end, (255, 255, 255))

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        ## WINDOW UPDATING
        if not thread.is_alive():
            return nxt_scene
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        rp.update_rich_presence("Loading new song... B)")
        clock.tick(45)
        pygame.display.update()


def splash():
    ## MONZTER DEVS src/assets/MonzterDevs.png
    MzR = pygame.image.load(os.path.join("assets", "MonzterDevs1.png")).convert_alpha()
    bloom = pygame.image.load(
        os.path.join("assets", "Bloom200x200.png")
    ).convert_alpha()
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
        screen.blit(
            bloom, (SW // 2 - bloom.get_width() // 2, SH // 2 - bloom.get_height() // 2)
        )
        screen.blit(
            MzR, (SW // 2 - MzR.get_width() // 2, SH // 2 - MzR.get_height() // 2)
        )

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        clock.tick(45)
        pygame.display.update()


def high_score():
    ## FONTS
    title_font = pygame.font.Font(
        os.path.join("assets/fonts", "Roboto", "Roboto-BoldItalic.ttf"), 30
    )
    # norm_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 15)

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

    back_button = RectButton(vec(SW // 2, SH - 25), vec(100, 25), "BACK")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "menu"

    scores = high_scores.get_scores()

    songs = [k for k in scores]
    high_scr = [scores[k][0] for k in scores]

    gui_scroll = vec(0, 0)
    gui_scroll_area = pygame.Rect(0, 30, SW, SH - 70)

    labels = []
    for i, s in enumerate(sorted(high_scr, reverse=True)):
        labels.append(
            Label(
                vec(SW // 3, 100 + (i * 20)),
                vec(SW - 10, 100),
                songs[high_scr.index(s)],
            )
        )
        labels.append(
            Label(vec(5 * SW // 6, 100 + (i * 20)), vec(SW - 10, 100), str(s))
        )

    # lab_surf = pygame.Surface((gui_scroll_area.w, len(songs)*100)).convert_alpha()
    # lab_surf.set_colorkey((0, 0, 0))
    # for l in labels:
    #     l.draw(lab_surf, (255, 255, 255))

    if len(scores) <= 0:
        labels.append(Label(vec(SW // 2, SH // 2), vec(SW - 10, 100), "NO DATA FOUND"))

    while True:
        scroll.y += 5
        screen.fill(back_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "exit"
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)
            if event.type == pygame.MOUSEWHEEL:
                gui_scroll.y -= event.y * 20
            # else:
            #     gui_scroll.y = 0

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

        gui_scroll.y = clamp(gui_scroll.y, 0, labels[-1].rect.bottom // 2)

        ## CLICKS
        if back_button.clicked() and not transitioning:
            tr_go_to = "menu"
            tr_close_start = True

        ## drawing

        draw_background_circles(circles, circle_color, back_color, scroll)

        for l in labels:
            l.draw(screen, (255, 255, 255), gui_scroll, gui_scroll_area)

        back_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )

        title_txt = title_font.render("HIGH SCORES", False, (255, 255, 255))
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 0))

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        rp.update_rich_presence("Staring at their High Scores...")
        clock.tick(45)
        pygame.display.update()


## THREADS
change_music_thread = threading.Thread(target=change_music)
change_music_thread.setDaemon(True)


## SCORE DEBUG THINGY
# for i in range(10, 20):
#     high_scores.save_score("song"+str(i), i*10)

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


def more_games():
    # FONTS
    title_font = pygame.font.Font(
        os.path.join("assets/fonts", "Roboto", "Roboto-BoldItalic.ttf"), 30
    )
    # norm_font = pygame.font.Font(os.path.join("assets/fonts", "Roboto", "Roboto-Thin.ttf"), 15)

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

    back_button = RectButton(vec(SW // 2, SH - 25), vec(100, 25), "BACK")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "menu"

    games = get_more_games()

    game_names = [k for k in games.keys()]

    gui_scroll = vec(0, 0)
    gui_scroll_area = pygame.Rect(0, 30, SW, SH - 70)

    labels = []
    buttons = []
    for i, y in zip(game_names, range(1, len(game_names) + 1)):
        l = Label(
            vec(SW // 2, 75 + (y * 100)),
            vec(SW - 10, 100),
            i.capitalize()
        )
        labels.append(l)
        buttons.append(
            RectButton(
                vec(l.rect.centerx, l.rect.centery - 10),
                vec(120, 25),
                "Download Now!"
            )
        )
        # back_button = RectButton(vec(SW // 2, SH - 25), vec(100, 25), "BACK")
        # labels.append(
        #    Label(vec(5 * SW // 6, 100 + (i * 20)), vec(SW - 10, 100), str(s))
        # )
    current_game_img = games[game_names[0]]['image_surface']
    title_txt = title_font.render("More Games", False, (255, 255, 255))
    while True:
        scroll.y += 5
        screen.fill(back_color)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "exit"
            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)
            if event.type == pygame.MOUSEWHEEL:
                gui_scroll.y -= event.y * 20

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
        gui_scroll.y = clamp(gui_scroll.y, 0, labels[-1].rect.bottom // 2)
        if back_button.clicked() and not transitioning:
            tr_go_to = "menu"
            tr_close_start = True
        for button, name in zip(buttons, game_names):
            if button.hovered():
                current_game_img = games[name]['image_surface']
            if button.clicked():
                # print(games[name]['download_link'])
                webbrowser.open(games[name]['download_link'])
                pygame.time.wait(500)

        ## drawing

        screen.blit(current_game_img, (-gui_scroll.x // 5, -gui_scroll.y // 5))
        draw_background_circles(circles, circle_color, back_color, scroll)
        for l in labels:
            l.draw(screen, (255, 255, 255), gui_scroll, gui_scroll_area)
        for b in buttons:
            b.draw(
                screen,
                (255, 255, 255),
                back_color.lerp((155, 100, 100), 0.25),
                (255, 140, 97),
                (0, 0, 0),
                gui_scroll
            )

        back_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )

        # title_txt = title_font.render("More Games", False, (255, 255, 255))
        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 0))

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        ## WINDOW UPDATING
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        rp.update_rich_presence("Staring at other games by MonZteR Games...")
        clock.tick(45)
        pygame.display.update()

def draw_rect_bounding_box(rect, screen):
    pygame.draw.rect(screen, (255, 0, 0), (*rect.topleft, rect.w, rect.h), 2)

def more_games_2():
    # FONTS
    font_dir = os.path.join("assets", "fonts", "Roboto")

    title_font = pygame.font.Font(os.path.join(font_dir, "Roboto-BoldItalic.ttf"), 30)
    norm_font = pygame.font.Font(os.path.join(font_dir, "Roboto-Thin.ttf"), 17)

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

    back_button = RectButton(vec(SW // 2, SH - 25), vec(100, 25), "BACK")

    tr_close_start = False
    tr_open_start = True
    transitioning = True
    tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
    tr_rect2.bottom = SH
    tr_go_to = "menu"

    game_data_unavailable_text = norm_font.render("Service currently unavailable", True, (255, 255, 255))
    game_data_unavailable_rect = game_data_unavailable_text.get_rect(center=(SW // 2, SH // 2))
    gui_scroll = vec(0, 0)
    gui_scroll_area = pygame.Rect(0, 30, SW, SH - 70)
    title_txt = title_font.render("More Games", False, (255, 255, 255))

    try:
        games = get_more_games()
        game_names = [k for k in games.keys()]
    except:
        games = None
        game_names = []

    arrow_image = pygame.image.load("assets/arrow.png")

    arrow_right = pygame.transform.rotate(arrow_image, 90)
    arrow_right_rect = arrow_right.get_rect(center=(60, SH//2))

    arrow_left = pygame.transform.rotate(arrow_right, 180)
    arrow_left_rect = arrow_left.get_rect(center=(SW-60, SH//2))

    arrow_right_rect.x = 10
    arrow_left_rect.x = SW-50

    cg_index = 0
    cg_name = game_names[cg_index]
    cg_data = games[cg_name]

    cg_image = cg_data["image_surface"]
    cg_image = pygame.transform.scale(cg_image, (130, 130))
    cg_image_rect = cg_image.get_rect(center=(SW // 2, 0))
    cg_image_rect.top = 40

    exiting = False
    while True:
        scroll.y += 5
        screen.fill(back_color)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

                return "exit"

            if event.type == BEAT_EVENT and data["back_change"]:
                back_color.r = random.randint(50, 100)
                back_color.g = random.randint(50, 100)
                back_color.b = random.randint(50, 100)
            if event.type == pygame.MOUSEWHEEL:
                gui_scroll.y -= event.y * 20

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
                if exiting:
                    return tr_go_to

                tr_close_start = False
                tr_open_start = True
                transitioning = True
                tr_rect1 = pygame.Rect(0, 0, SW, SH // 2)
                tr_rect2 = pygame.Rect(0, 0, SW, SH // 2)
                tr_rect2.bottom = SH

        # gui_scroll.y = clamp(gui_scroll.y, 0, labels[-1].rect.bottom // 2)

        if back_button.clicked() and not transitioning:
            tr_go_to = "menu"
            tr_close_start = True
            exiting = True

        draw_background_circles(circles, circle_color, back_color, scroll)

        # more games content here
        if games is None:
            screen.blit(game_data_unavailable_text, game_data_unavailable_rect)

        else:
            # screen.blit(cg_name_surf, cg_name_rect)
            screen.blit(cg_image, cg_image_rect)

            screen.blit(arrow_left, arrow_left_rect)
            screen.blit(arrow_right, arrow_right_rect)
            if debug:
                draw_rect_bounding_box(cg_image_rect, screen)
                draw_rect_bounding_box(arrow_right_rect, screen)
                draw_rect_bounding_box(arrow_left_rect, screen)

        # more games content end

        back_button.draw(
            screen,
            (255, 255, 255),
            back_color.lerp((155, 100, 100), 0.25),
            (255, 140, 97),
            (0, 0, 0),
        )

        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect1,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            pygame.Color(255, 255, 255).lerp(back_color, 0.5),
            tr_rect2,
            border_radius=10,
        )

        screen.blit(title_txt, (SW // 2 - title_txt.get_width() // 2, 0))
        screen.blit(vig, (0, 0))
        window.blit(pygame.transform.scale(screen, (WW, WH)), (0, 0))
        rp.update_rich_presence("Staring at other games by MonZteR Games...")
        clock.tick(45)
        pygame.display.update()


scene = "more_games"
while True:

    if scene == "splash":
        scene = splash()

    elif scene == "menu":
        scene = menu()

    elif scene == "game":
        scene = game()

    elif scene == "settings":
        scene = settings()

    elif scene == "loading":
        scene = loading(change_music_thread, "menu")

    elif scene == "high_score":
        scene = high_score()

    elif scene == "more_games":
        # scene = more_games()
        scene = more_games_2()

    elif scene == "exit":
        rp.RPC.clear()
        rp.RPC.close()
        pygame.quit()
        sys.exit()
