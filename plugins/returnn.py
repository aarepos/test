from pyrogram import Client, filters
from tinydb import TinyDB, Query
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from . import config

db = TinyDB('user.json')
user = Query()


@Client.on_callback_query(filters.regex(r'return_to_main_menu'))
def return_to_main_manu(client, callback_query):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id

    user_type = db.search(user.id == uid)[0]['user_type']
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

    db.update({'status': 0}, user.id == uid)

    client.edit_message_text(
        chat_id=uid,
        message_id=mid,
        text=config.return_to_main_menu_text,
        reply_markup=InlineKeyboardMarkup(reply_button)
    )

