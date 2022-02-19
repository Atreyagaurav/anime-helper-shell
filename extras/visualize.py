import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.dates import DateFormatter
import datetime as dt
import pandas as pd
import calendar

df = pd.read_csv("./extras/log_anime.csv")

daily = df.groupby(['year', 'month', 'day']).agg(
    watchtime=('watchtime', 'sum'),
    dayofweek=('dayofweek', 'first'),
)

daily.loc[:, 'date'] = daily.apply(
    lambda row: dt.datetime(row.name[0], row.name[1], row.name[2]), axis=1)

day = daily.date.min()
while day <= daily.date.max():
    if (day.year, day.month, day.day) not in daily.index:
        daily.loc[(day.year,
                   day.month,
                   day.day), :] = [0, calendar.day_name[day.dayofweek], day]
        day += dt.timedelta(days=1)

daily.sort_index(inplace=True)

weekdays = daily.groupby('dayofweek').watchtime.mean() / 3600
days_dict = {d: i for i, d in enumerate(calendar.day_name)}
colors = [
    'tab:blue', 'tab:pink', 'tab:gray', 'tab:orange', 'tab:purple',
    'tab:olive', 'tab:green'
]
days_color = {d: c for d, c in zip(calendar.day_name, colors)}
weekdays.sort_index(key=lambda x: x.map(lambda v: days_dict[v]), inplace=True)

all_animes = pd.pivot_table(df,
                            columns=['dayofweek'],
                            index='anime',
                            values='watchtime',
                            aggfunc='sum').fillna(0)

animes = all_animes[all_animes.apply(sum, axis=1) > 1800]  # At least 30 minutes of watchtime
other_animes = all_animes[all_animes.apply(sum, axis=1) <= 1800]  # remaining
others = other_animes.sum() / 3600
animes /= 3600
# animes = df.groupby(['anime', 'dayofweek']).episode.count()
animes.index = animes.index.map(lambda x: x
                                if len(x) < 30 else x[:17] + '...' + x[-10:])
animes.sort_index(inplace=True)
animes.loc['others', :] = others

# watchtime = df.groupby('anime').watchtime.sum()
# watchtime.index = animes.index
# total = watchtime.sum()
# name = watchtime.map(lambda x: x * 100 / total > 2)
# for_pi = watchtime[name]
# for_pi.loc['others'] = watchtime[name == False].sum()

with plt.style.context("ggplot"):
    fig = plt.figure(constrained_layout=True, figsize=(16, 9))
    specs = gridspec.GridSpec(ncols=2, nrows=2, figure=fig)

    top = fig.add_subplot(specs[0, :])
    bleft = fig.add_subplot(specs[1, 0])
    bright = fig.add_subplot(specs[1, 1])

    bottoms = pd.Series(0, index=animes.index)
    top_bars = []
    for col in calendar.day_name:
        tb = top.bar(animes.index,
                     animes[col],
                     color=days_color[col],
                     bottom=bottoms)
        bottoms += animes[col]
        top_bars.append(tb)
        top.tick_params(labelbottom=False, bottom=False)
        top.set_xlabel('Animes watched since 2021-Jan-15')
        top.set_ylabel('Hours spent')
        mean_h = bottoms.max()/2
    for i, bar in enumerate(top_bars[0]):
        h = sum((top_bars[j][i].get_height() for j in range(len(top_bars))))
        if h > mean_h:
            h = 0
            top.annotate(
                animes.index[i],
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                rotation=90,
                ha='center',
                va='bottom')

    bleft_bar = bleft.bar(weekdays.index, weekdays, color=colors)
    bleft.set_ylabel('Hours')
    bleft.set_xlabel('Average Time Spent on Anime')

    # bright_pie = bright.pie(for_pi, labels=for_pi.index)
    # bright.set_xlabel(f'Total time spent on anime={total/3600:.2f}hr')
    bright.plot_date(daily.date, daily.watchtime / 3600, fmt='--',
                     linewidth=0.7)
    # bright.plot_date(daily.date, daily.watchtime/3600, fmt='o',
    #                  color=[days_color[d] for d in daily.dayofweek])
    bright.scatter(daily.date,
                   daily.watchtime / 3600,
                   c=daily.dayofweek.map(days_color))
    bright.xaxis.set_major_formatter(DateFormatter("%b-%d"))

plt.show()
