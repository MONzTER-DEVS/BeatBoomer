import json
import os

fp = "assets/data/high scores.json"
if not os.path.exists(fp):
    with open(fp, "w") as f:
        json.dump({}, f)


def get_scores():
    with open(fp, "r") as f:
        return json.load(f)


def save_score(song_name, score):
    data = get_scores()
    if song_name in data.keys():
        data[song_name].append(score)
        data[song_name] = sorted(data[song_name], reverse=True)
    else:
        data[song_name] = [score, ]
        data[song_name] = sorted(data[song_name], reverse=True)

    with open(fp, "w") as f:
        json.dump(data, f)

    return data
