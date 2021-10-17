from pyrogram import Client, filters
from threading import Timer
from tinydb import TinyDB, Query
from captcha.image import ImageCaptcha
import tinydb
from . import main_menu, config
import random
import os
from datetime import datetime
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)


# tinydb objects
db = TinyDB('user.json')
ch = TinyDB('channels.json')
log = TinyDB('log.json')
user = Query()

# captcha object
image = ImageCaptcha(width=250, height=125)


def new_user(message):

    uid = message.from_user.id
    fname = message.from_user.first_name
    username = message.from_user.username

    db.insert({
        'id': uid,
        'username': username,
        'fname': fname,
        'host': None,
        'status': 0,
        'captcha': 1,
        'user_type': 0,
        'search_per_day': 1,
        'search_count': 0,
        'expire': None,
        'memo': None,
        'paymemo': None,
        'alert': 0
    })


def host_works(client, callback_query):

    uid = callback_query.from_user.id
    username = callback_query.from_user.username
    fname = callback_query.from_user.first_name

    user_info = db.search(user.id == uid)[0]
    memo = user_info['memo']
    host = user_info['host']

    if host == None and memo != None:

        alert = int(memo)
        # now = str(datetime.today().strftime('%Y-%m-%#d'))

        # log.insert({
        #     'log': f'SUBCATEGORY {now} : {username}({uid}) were placed in the {alert} subset'
        # })

        db.update({'host': memo}, user.id == uid)
        db.update({'memo': None}, user.id == uid)
        client.send_message(
            chat_id=alert,
            text=config.someone_joined_text.format(fname = fname, username = username)
        )

        host_info = db.search(user.id == alert)[0]
        user_type = host_info['user_type']
        search_per_day = host_info['search_per_day']

        if user_type == 0 or user_type == 1:

            invite_count = len(TinyDB('user.json').search(user.host == alert))

            if search_per_day < 3 and invite_count % 2 == 0:
                search_per_day += 1
                db.update({'search_per_day': search_per_day}, user.id == alert)

            if invite_count % 2 == 0:

                search_for_channel = TinyDB('channels.json').search(
                    user.id == str(int(invite_count / 2)))

                if len(search_for_channel) != 0:

                    try:

                        create_new_link = client.create_chat_invite_link(
                            chat_id=search_for_channel[0]['cid'],
                            member_limit=1
                        )

                        client.send_message(
                            chat_id=alert,
                            text=config.new_link.format(
                                str(int(invite_count / 2))) + '\n' + create_new_link['invite_link']
                        )

                    except Exception as e:
                        pass


def join_in_channel_step(client, callback_query={}, message={}):

    if callback_query == {}:
        data = message
    else:
        data = callback_query.message

    uid = data.chat.id
    try:

        result = client.get_chat_member(config.channel, uid)
        main_menu.show_menu(client, uid)
    except Exception as e:
        client.send_message(
            chat_id=uid,
            text=config.join_in_channel_text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            'Join',
                            url=f'https://t.me/{config.channel}'
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            'Verify',
                            callback_data='verify'
                        )
                    ],
                ]
            )
        )


def video(client, callback_query):

    uid = callback_query.from_user.id
    client.send_video(
        chat_id=uid,
        video=config.video_file_id,
        caption=config.video_caption_text
    )
    r = Timer(config.join_in_channel_time, join_in_channel_step,
              (client, callback_query)).start()


def welcome_text(client, callback_query):
    uid = callback_query.from_user.id

    client.send_message(
        chat_id=uid,
        text=config.after_captcha_text
    )
    r = Timer(config.video_time, video, (client, callback_query)).start()


def captchafunc(client, message):

    uid = message.from_user.id

    a, b = random.choice(list(range(10))), random.choice(list(range(10)))
    c = a + b

    captcha_text = f'{a} + {b}'
    data = image.generate(captcha_text)
    captcha_image = image.write(captcha_text, f'images/{uid}.png')

    false_answers = list(range(c)) + list(range(c + 1, 20))
    random.shuffle(false_answers)

    answers = [
        InlineKeyboardButton(str(c), callback_data="answer-true"),
        InlineKeyboardButton(
            str(false_answers[0]), callback_data="answer-false"),
        InlineKeyboardButton(
            str(false_answers[1]), callback_data="answer-false"),
        InlineKeyboardButton(
            str(false_answers[2]), callback_data="answer-false")
    ]

    random.shuffle(answers)

    client.send_photo(
        chat_id=uid,
        photo=f'images/{uid}.png',
        caption='this is captcha',
        reply_markup=InlineKeyboardMarkup([answers])
    )
    os.remove(f'images/{uid}.png')


# entry points
@Client.on_message(filters.command('start'))
def start(client, message):

    # user information
    text = message.text
    uid = message.from_user.id

    array_text = text.split(' ')
    reply = ''

    # check point
    search_for_user = db.search(user.id == uid)

    if len(search_for_user) != 0:
        status = search_for_user[0]['status']
        captcha = search_for_user[0]['captcha']
        if status == 'block':
            return

        if captcha != 'solved':
            captchafunc(client, message)
            return

        try:

            result = client.get_chat_member(config.channel, uid)
            main_menu.show_menu(client, uid)
        except Exception as e:
            join_in_channel_step(client, message=message)

        return
    else:

        # insert user info
        new_user(message)

    # referral or not!
    try:  # with referral
        host = array_text[1]
        host_info = db.search(user.id == int(host))[0]

        client.send_message(
            chat_id = int(host),
            text = config.someone_joined_in_bot_text
        )

        host_name = host_info['fname']
        username  = host_info['username']
        reply = f'Your host name is: {host_name}-@{username}'
        db.update({'memo': int(host)}, user.id == uid)

    except Exception as e:  # witout referral
        reply = 'without referral'

    # if len(array_text) == 2:  # with referral
    #     reply = f'Your host is'
    # else:

    message.reply_text(reply)
    r = Timer(config.recpatcha_time, captchafunc, (client, message)).start()


@Client.on_callback_query(filters.regex(r'answer-.*'))
def racaptcha_answer(client, callback_query):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id
    answer = callback_query.data.split('-')[1]
    search_for_user = db.search(user.id == uid)[0]
    status = search_for_user['status']
    captcha_status = search_for_user['captcha']

    if status == 'block' or captcha_status == 'solved':
        callback_query.message.delete()
        return

    if answer == 'false':

        number_of_errors = db.search(user.id == uid)[0]['captcha']
        if number_of_errors > config.noe:
            db.update({'status': 'block'}, user.id == uid)
            client.edit_message_text(
                chat_id=uid,
                message_id=callback_query.message.message_id,
                text='You are blocked'
            )
            return

        number_of_errors += 1
        db.update({'captcha': number_of_errors}, user.id == uid)
        callback_query.answer(
            'False, try again.',
            show_alert=True
        )

        a, b = random.choice(list(range(10))), random.choice(list(range(10)))
        c = a + b

        captcha_text = f'{a} + {b}'
        data = image.generate(captcha_text)
        captcha_image = image.write(captcha_text, f'images/{uid}.png')

        false_answers = list(range(c)) + list(range(c + 1, 20))
        random.shuffle(false_answers)

        answers = [
            InlineKeyboardButton(str(c), callback_data="answer-true"),
            InlineKeyboardButton(
                str(false_answers[0]), callback_data="answer-false"),
            InlineKeyboardButton(
                str(false_answers[1]), callback_data="answer-false"),
            InlineKeyboardButton(
                str(false_answers[2]), callback_data="answer-false")
        ]

        random.shuffle(answers)

        client.edit_message_media(
            chat_id = uid,
            message_id = mid,
            media = InputMediaPhoto(media = f'images/{uid}.png'),
            reply_markup = InlineKeyboardMarkup([answers])

        )
        os.remove(f'images/{uid}.png')

    else:
        callback_query.answer(
            'Tankyou',
            show_alert=False
        )
        db.update({'captcha': 'solved'}, user.id == uid)
        callback_query.message.delete()
        welcome_text(client, callback_query)

        try:

            result = client.get_chat_member(config.channel, uid)

            host_works(client, callback_query)

        except Exception as e:
            pass


@Client.on_callback_query(filters.regex(r'verify'))
def verify(client, callback_query):
    uid = callback_query.from_user.id

    try:

        result = client.get_chat_member(config.channel, uid)
        callback_query.answer(
            'Thanks',
            show_alert=False
        )
        callback_query.message.delete()
        main_menu.show_menu(client, uid)

        host_works(client, callback_query)

    except Exception as e:
        callback_query.answer(
            'Please join in channel',
            show_alert=True
        )
