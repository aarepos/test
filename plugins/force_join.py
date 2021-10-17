from pyrogram import Client
from . import config

from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def fjoin(client, callback_query={}, message={}):

    if callback_query == {}:
        data = message
    else:
        data = callback_query.message

    uid = data.chat.id
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
