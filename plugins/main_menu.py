from pyrogram import Client, filters, StopPropagation
from tinydb import TinyDB, Query
from . import force_join, config
from datetime import datetime
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import time


db = TinyDB('user.json')
user = Query()


def show_menu(client, user_id):

    uid = user_id
    user_type = TinyDB('user.json').search(user.id == uid)[0]['user_type']


    reply_button = [
        [
            InlineKeyboardButton(
                'pay',
                callback_data='pay'
            )
        ],
        [
            InlineKeyboardButton(
                'refferal link',
                callback_data='link'
            )
        ],
        [
            InlineKeyboardButton(
                'search',
                callback_data='search'
            )
        ],
    ]

    if user_type == 3:
        reply_button.pop(0)

    client.send_message(
        chat_id=uid,
        text=config.main_menu_text,
        reply_markup=InlineKeyboardMarkup(reply_button)
    )

@Client.on_callback_query(filters.regex(r'link'))
def send_refferal_link(client, callback_query):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id
    try:

        result = client.get_chat_member(config.channel, uid)
        callback_query.answer('', show_alert=False)
        client.edit_message_text(
            chat_id=uid,
            message_id=mid,
            text=config.referral_link_text
        )
        client.send_message(
            chat_id=uid,
            text=f'https://t.me/{config.bot_username}?start={uid}'
        )
        show_menu(client, uid)

    except Exception as e:
        callback_query.answer(
            'Please join in public channel!',
            show_alert=False
        )
        callback_query.message.delete()
        force_join.fjoin(client=client, callback_query=callback_query)


@Client.on_callback_query(filters.regex(r'pay') | filters.regex(r'back_pay_option'))
def show_plans(client, callback_query):
    uid = callback_query.from_user.id
    mid = callback_query.message.message_id
    try:

        result = client.get_chat_member(config.channel, uid)
        callback_query.answer('', show_alert=False)

        db = TinyDB('user.json')
        user_info = db.search(user.id == uid)[0]
        user_type = user_info['user_type']
        expire = user_info['expire']

        if user_type == 3:
            callback_query.answer(
                ':)',
                show_alert=False
            )
            return

        if user_type == 0:
            reply_button = [
                [
                    InlineKeyboardButton(
                        'Upgrade',
                        callback_data='upgrade'
                    )
                ],
                [
                    InlineKeyboardButton(
                        'Return',
                        callback_data='return_to_main_menu'
                    )
                ],
            ]

            user_type_alias = 'simple'
            expire = 'live time'
        else:
            reply_button = [
                [
                    InlineKeyboardButton(
                        'Revival',
                        callback_data='revival'
                    )
                ],
                [
                    InlineKeyboardButton(
                        'Upgrade',
                        callback_data='upgrade'
                    )
                ],
                [
                    InlineKeyboardButton(
                        'Return',
                        callback_data='return_to_main_menu'
                    )
                ],
            ]

            now = int(time.time())
            expire = int((expire - now) / 86400)
            expire = str(expire) + ' day' 

            if user_type == 1:
                user_type_alias = 'bronze'
            elif user_type == 2:
                user_type_alias = 'silver'

        text = f'Your plan is {user_type_alias}, and your expire is {expire}'

        client.edit_message_text(
            chat_id=uid,
            message_id=mid,
            text=text,
            reply_markup=InlineKeyboardMarkup(reply_button)
        )

    except Exception as e:
        callback_query.answer(
            'Please join in public channel!',
            show_alert=False
        )
        callback_query.message.delete()
        force_join.fjoin(client=client, callback_query=callback_query)


@Client.on_callback_query(filters.regex(r'search'))
def searcher(client, callback_query):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id
    db = TinyDB('user.json')
    user_info = db.search(user.id == uid)[0]
    search_per_day = user_info['search_per_day']
    search_count = user_info['search_count']

    if search_per_day <= search_count:
        # print(search_per_day)
        # print(search_count)
        callback_query.answer(
            "You can't!",
            show_alert=True
        )
        return

    callback_query.answer(
        '',
        show_alert=False
    )
    reply_button = [
        [
            InlineKeyboardButton(
                'Cancel',
                callback_data='return_to_main_menu'
            )
        ]
    ]

    client.edit_message_text(
        chat_id=uid,
        message_id=mid,
        text=config.search_text,
        reply_markup=InlineKeyboardMarkup(reply_button)
    )
    db.update({'memo': mid, 'status': 1}, user.id == uid)


@Client.on_callback_query(filters.create(
    func = lambda filter, client, update: TinyDB('user.json').search(user.id == update.from_user.id)[0]['status'] == 'block'
), group = -1)
def exit_bot(client, callback_query):
    raise StopPropagation

