import pandas as pd
import os
import datetime as dt

log_file = os.path.expanduser("~/.log/mpv.log")

df = pd.DataFrame(
    columns=['timestamp', 'action', 'current_time',
             'total_time', 'filename'])
with open(log_file) as r:
    for i, line in enumerate(r):
        row = line.strip().split(" ", 4)
        df.loc[i, :] = row

df.loc[:, 'isanime'] = df.filename.map(lambda fn: fn.startswith("Ganime:"))

dfanime = df[df.isanime]
dfanime.to_csv("/tmp/anime.csv", index=False)
df = pd.read_csv("/tmp/anime.csv")
animename = df.filename.map(lambda fn: fn[7:])
df.loc[:, 'anime'] = animename.map(lambda x: x.split(':')[0])
df.loc[:, 'episode'] = animename.map(
    lambda x: x.split(':')[1].split(".")[0][3:])


def time_in_seconds(tms):
    data = tms.split(":")
    val = 0
    for d in data:
        val = val*60 + int(d)
    return val


def play_categorize(action):
    if action in ['file-loaded', 'pause', 'seek']:
        return -1
    return 1


df.current_time = df.current_time.map(time_in_seconds)
df.total_time = df.total_time.map(time_in_seconds)
df.loc[:, 'temp'] = df.action.map(play_categorize)
df.temp = df.temp * df.current_time
processed = df.groupby(['anime', 'episode']).agg(
    watchtime=('temp', 'sum'),
    totaltime=('total_time', 'mean'),
    timestamp=('timestamp', 'mean')
)
processed.loc[:, 'percentage'] = (
    processed.watchtime * 100 / processed.totaltime)
dates = processed.timestamp.map(dt.datetime.fromtimestamp)
processed.loc[:, 'year'] = dates.map(lambda t: t.year)
processed.loc[:, 'month'] = dates.map(lambda t: t.month)
processed.loc[:, 'day'] = dates.map(lambda t: t.day)
processed.loc[:, 'dayofweek'] = dates.map(lambda t: t.strftime("%A"))
processed.loc[:, 'hour'] = dates.map(
    lambda t: t.hour + t.minute/60 + t.second/3600)

processed.to_csv("./extras/log_anime.csv")
