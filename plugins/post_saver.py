from pyrogram import Client, filters
from tinydb import TinyDB, Query
import datetime
import time

ch = TinyDB('channels.json')
posts = TinyDB('posts.json')
admin = Query()


@Client.on_message(filters.channel & filters.text)
def save_text(client, message):
    chat_id = message.chat.id
    qualify = []

    all_channels = ch.all()
    for channel in all_channels:
        qualify.append(channel['cid'])


    if str(chat_id) not in qualify:
        return

    posts.insert({
        'text': message.text.lower(),
        'chat_id': chat_id,
        'mid': message.message_id,
        'date': str(time.time())
    })


@Client.on_message(filters.channel & filters.caption)
def save_media(client, message):
    chat_id = message.chat.id
    qualify = []

    all_channels = ch.all()
    for channel in all_channels:
        qualify.append(channel['cid'])


    if str(chat_id) not in qualify:
        return

    posts.insert({
        'text': message.caption.lower(),
        'chat_id': chat_id,
        'mid': message.message_id,
        'date': str(time.time())
    })