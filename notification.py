import notify2
import utils


def send_notification(summary, body):
    notify2.init('Gogoanime CLI')
    n = notify2.Notification(summary, message=body)
    n.show()


def episodes_update(updates):
    if len(updates) == 0:
        return
    if len(updates) == 1:
        anime_name = list(updates)[0]
        epl = len(updates[anime_name])
        eps = utils.compress_range(updates[anime_name])
        summary = f'{epl} New episode(s)'
        msg = f'{anime_name} has {epl} new episodes ({eps})'
        send_notification(summary, msg)
    else:
        summary = f'{len(updates)} anime updates'
        msg = ''
        for anime_name, ep in updates.items():
            epl = len(updates[anime_name])
            eps = utils.compress_range(updates[anime_name])
            msg += f'{epl} new ({eps}) : {anime_name}\n'
        send_notification(summary, msg)
