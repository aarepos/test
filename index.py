from pyrogram import Client, filters
from tinydb import TinyDB, Query
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from plugins import config
import time


api = Client('api') #api bot
db = TinyDB('user.json') #user.json database
log = TinyDB('log.json')
user = Query() #query signals
event_loop_time = 10 # second
timer24_time = 86400 # second (1 day)
admin = 956473054


def event_loop():
    all_users = db.search(user.user_type > 0)
    bronze_alert = [10, 3, 1]
    silver_alert = [30, 10, 3, 1]
    
    for person in all_users:

        user_type = person['user_type']
        if user_type == 3: continue
        uid = person['id']
        expire = person['expire']
        alert_index = int(person['alert'])

        now = int(time.time())
        leftover = float(expire) - float(now)

        if leftover <= 0:
            db.update({
                'user_type': 0,
                'expire': None,
                'alert': 0,
                'search_per_day': 1
            }, user.id == uid)
            api.send_message(
                chat_id = uid,
                text = 'your time is lost.'
            )
            # now = str(datetime.datetime.today().strftime('%Y-%m-%d'))
            # log.insert({
            #     'log': f'TIMEOUT: {now} : user {str(uid)}, from {config.user_types[user_type]}'
            # })
            continue
        
        leftover = float(leftover / 86400)

        if user_type == 1 & bronze_alert[alert_index] > leftover:
            api.send_message(
                chat_id = uid,
                text = 'Your time is low, left over: {}'.format(bronze_alert[alert_index])
            )
            alert_index += 1
            db.update({'alert': alert_index}, user.id == uid)

        if user_type == 2 & silver_alert[alert_index] > leftover:
            api.send_message(
                chat_id = uid,
                text = 'Your time is low, left over: {}'.format(silver_alert[alert_index])
            )
            alert_index += 1
            db.update({'alert': alert_index}, user.id == uid)
      

def timer24():
    all_simples = db.search(user.user_type == 0)
    all_vips = db.search(user.user_type > 0)
    all_logs = log.all()

    for person in all_simples:
        uid = person['id']
        db.update({'search_per_day': 1, 'search_count': 0}, user.id == uid)

    for person in all_vips:
        uid = person['uid']
        db.update({'search_count': 0}, user.id == uid)
    
    if len(all_logs) == 0: return
    
    events = ''
    for event in all_logs:
        events += event['log'] + '\n'

    log.truncate()
    api.send_message(
        chat_id = admin,
        text = events
    )



event_loop_timer = BackgroundScheduler()
event_loop_timer.add_job(event_loop, "interval", seconds=event_loop_time)
event_loop_timer.start()

search_reset = BackgroundScheduler()
search_reset.add_job(timer24, "interval", seconds=timer24_time)
search_reset.start()


api.run()