# from pyrogram import Client, filters


# @Client.on_message(filters.command('ok'))
# def ok(client, message):

#     try:
#         print(1)
#         invite_link = client.create_chat_invite_link(
#             chat_id=-1001579744061,
#             member_limit = 1
#         )['invite_link']
        
#         print(2)
#         title = client.get_chat(
#             chat_id=-1001579744061
#         )['title']
#         print(3)
#         client.send_message(
#             chat_id = message.from_user.id,
#             text = invite_link + '\n' + title
#         )
#     except Exception as e:
#         pass
