from pyrogram import Client, filters
from tinydb import TinyDB, Query
from . import config, main_menu

db = TinyDB('user.json')
posts = TinyDB('posts.json')
finder = Query()
user = Query()

pchannel = -1001516611417


@Client.on_message(filters.text & ~filters.command('start') & filters.create(
    func = lambda filter, client, update: db.search(user.id == update.from_user.id)[0]['status'] == 1
))
def searching(client, message):

    uid = message.from_user.id
    mid = message.message_id
    txt = message.text

    def find_func(c): return txt.lower() in c
    all_posts = posts.search(finder.text.test(find_func))

    if len(all_posts) != 0:
        for post in all_posts:
            client.copy_message(
                chat_id=uid,
                from_chat_id=post['chat_id'],
                message_id=post['mid']
            )
    else:
        message.reply_text('not found!')

    user_info = db.search(user.id == uid)[0]
    memo = user_info['memo']
    search_count = user_info['search_count']
    client.delete_messages(
        chat_id = uid,
        message_ids = memo
    )

    main_menu.show_menu(client, uid)

    db.update({'memo': None, 'search_count': search_count + 1, 'status': 0}, user.id == uid)