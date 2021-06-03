import requests
import io
import urllib.request
import pygame
from copy import deepcopy


def get_image(image_url):
    r = requests.get(image_url)
    img = io.BytesIO(r.content)
    return pygame.image.load(img)


def get_more_games():
    data = requests.get("https://monzter-devs.github.io/MONzTER-DEVS.api/more_from_creator.json").json()

    # try:
    #     del data["games"]["beat n boom"]
    #
    # except:
    #     pass

    games = deepcopy(data["games"])

    for game_name in games:
        game = games[game_name]
        image_url = game["image_url"]
        image = get_image(image_url)

        del data["games"][game_name]["image_url"]
        data["games"][game_name]["image_surface"] = image

    return data["games"]

