from pyrogram import Client, filters
from pyrogram.types.bots_and_keyboards import callback_query
from tinydb import TinyDB, Query
from tronpy import Tron
from eth_account import Account
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import requests
import json
import time
import datetime
from . import config, returnn, main_menu

db = TinyDB('user.json')
ch = TinyDB('channels.json')
log = TinyDB('log.json')
user = Query()
tron_client = Tron()


def send_private_channels(client, uid, mode='all'):

    channel_list = ''

    if mode == 'bronze':
        all_channels = ch.search(user.mode == mode)
    else:
        all_channels = ch.all()

    for channel in all_channels:
        cid = channel['cid']
        try:
            invite_link = client.create_chat_invite_link(
                chat_id=cid,
                member_limit=1
            )['invite_link']

            title = client.get_chat(
                chat_id=cid
            )['title']

            channel_list += f"[{title}]({invite_link}) \n"
        except Exception as e:
            continue

    channel_list = 'channel is empty' if channel_list == '' else channel_list
    client.send_message(
        chat_id=uid,
        text=channel_list,
        parse_mode='markdown'
    )

    main_menu.show_menu(client, uid)


# 3
def choise_wallet(client, callback_query, plan, fee):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id
    fee = float("{:.2f}".format(float(fee)))

    reply_button = [
        [
            InlineKeyboardButton(
                'BEP20',
                callback_data=f'wallet-BEP20-{plan}-{fee}'
            ),
            InlineKeyboardButton(
                'TRC20',
                callback_data=f'wallet-TRC20-{plan}-{fee}'
            ),
        ],
        [
            InlineKeyboardButton(
                'Back',
                callback_data='back_to_upgrade'
            )
        ],
        [
            InlineKeyboardButton(
                'Return to main menu',
                callback_data='return_to_main_menu'
            )
        ]
    ]

    client.edit_message_text(
        chat_id=uid,
        message_id=mid,
        text=config.choise_wallet_text.format(fee),
        reply_markup=InlineKeyboardMarkup(reply_button)
    )


def trc_balance(address):
    url = "https://apilist.tronscan.org/api/account"
    payload = {
        "address": address,
    }
    res = requests.get(url, params=payload)
    trc20token_balances = json.loads(res.text)["trc20token_balances"]
    try:
        for token in trc20token_balances:
            if token['tokenType'] == 'trc20':
                return float(token['balance'] / 1000000)

    except Exception as e:
        return False


def bep_balance(address):
    key = '5K3NV83KT2WYGX36VKNVCSIG5WDR8GRS8J'
    contract = '0x55d398326f99059ff775485246999027b3197955'
    url = f'https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress={contract}&address={address}&tag=latest&apikey={key}'

    try:

        r = requests.get(url)
        balance = float(json.loads(r.content.decode())[
                        'result']) / 1000000000000000000000
        return balance

    except Exception as e:
        return False


# 5``
@Client.on_callback_query(filters.create(
    lambda filter, client, update: True if update.data.split(
        '-')[0] == 'checkwallet' else False
))
def payment(client, callback_query):

    uid = callback_query.from_user.id
    username = callback_query.from_user.username
    data = callback_query.data.split('-')
    user_info = db.search(user.id == uid)[0]

    paymemo = user_info['paymemo']
    address = paymemo['address']
    wallet_type = data[1]
    plan = data[2]
    fee = float(data[3])

    if wallet_type == 'TRC20':
        balance = trc_balance(address)
        if balance == False or type(balance) == type(None):
            callback_query.answer(
                'There was a problem, please try again.', show_alert=True)
            return
        elif balance >= fee:
            confirm = True
        else:
            callback_query.answer(
                f'you pay {balance}, plese pay {fee - balance} more!.', show_alert=True)
            return

    else:
        balance = bep_balance(address)
        if balance == False:
            callback_query.answer(
                'There was a problem, please try again.', show_alert=True)
            return
        elif balance >= fee:
            confirm = True
        else:
            callback_query.answer(
                f'you pay {balance}, plese pay {fee - balance} more!.', show_alert=True)
            return

    if confirm == True:

        callback_query.answer('ThankYou', show_alert=False)
        callback_query.message.delete()

        client.send_message(
            chat_id=callback_query.from_user.id,
            text='Tank you for your paying!'
        )

        if plan == 'bronze':
            send_private_channels(client, uid, mode='bronze')

        else:
            send_private_channels(client, uid)

        now = int(time.time())
        get_period = config.period[plan]
        expire = 'unlimited' if get_period == 0 else now + (get_period * 86400)
        db.update({'expire': expire, 'user_type': int(config.user_types.index(plan)),
                  'search_per_day': config.user_search[plan]}, user.id == uid)

        db.update({'paymemo': None}, user.id == uid)

        # now = str(datetime.datetime.today().strftime('%Y-%m-%d'))
        # log.insert({
        #     'log': f'PAYMENT: {now} : from {username}({str(uid)}), token {wallet_type},amount({str(balance)}),plan({plan}), address({address}), privateKey({paymemo["private_key"]}), publicKey({paymemo["public_key"]})'
        # })


# 4`
@Client.on_callback_query(filters.create(
    lambda filter, client, update: True if update.data.split(
        '-')[0] == 'wallet' else False
))
def prepayment(client, callback_query):

    uid = callback_query.from_user.id
    username = callback_query.from_user.username
    mid = callback_query.message.message_id

    data = callback_query.data.split('-')
    wallet_type = data[1]
    plan = data[2]
    fee = data[3]

    if wallet_type == 'TRC20':
        address_info = tron_client.generate_address()
        address = address_info['base58check_address']
        private_key = address_info['private_key']
        public_key = address_info['public_key']

        client.send_message(
            chat_id = private_channel,
            text = config.new_wallet_text.format(wallet_type = wallet_type, address = address, private_key = private_key, public_key = public_key)
        )

    else:
        address_info = Account.create()
        address = address_info.address
        private_key = address_info.privateKey.hex()
        public_key = 'empty'
        client.send_message(
            chat_id = private_channel,
            text = config.new_wallet_text.format(wallet_type = wallet_type, address = address, private_key = private_key, public_key = public_key)
        )

    paymemo = {
        'address': address,
        'private_key': private_key,
        'public_key': public_key
    }
    db.update({'paymemo': paymemo}, user.id == uid)

    # now = str(datetime.datetime.today().strftime('%Y-%m-%d'))
    # log.insert({
    #     'log': f'CREATE WALLET: {now} : from {username}({str(uid)}), token {wallet_type}, address({address}), privateKey({private_key}), publicKey({public_key})'
    # })

    reply_button = [
        [
            InlineKeyboardButton(
                'Done',
                callback_data=f'checkwallet-{wallet_type}-{plan}-{fee}'
            )
        ],
        [
            InlineKeyboardButton(
                'Back',
                callback_data=f'back_to_choise_wallet-{plan}-{fee}'
            )
        ],
    ]

    client.edit_message_text(
        chat_id=uid,
        message_id=mid,
        text=config.prepayment_text.format(address, fee),
        reply_markup=InlineKeyboardMarkup(reply_button)
    )


# 5`
@Client.on_callback_query(filters.create(
    lambda filter, client, update: True if update.data.split(
        '-')[0] == 'back_to_choise_wallet' else False
))
def back_to_choise_wallet(client, callback_query):

    uid = callback_query.from_user.id
    data = callback_query.data.split('-')
    plan = data[1]
    fee = data[2]

    db.update({'paymemo': None}, user.id == uid)

    choise_wallet(client, callback_query, plan, fee)


# 1
@Client.on_callback_query(filters.regex(r'upgrade') | filters.regex(r'back_to_upgrade'))
def upgrade(client, callback_query):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id

    user_info = db.search(user.id == uid)[0]
    user_type = user_info['user_type']

    reply_button = [
        [InlineKeyboardButton('Gold', callback_data='gold')],
        [InlineKeyboardButton('Silver', callback_data='silver')],
        [InlineKeyboardButton('Bronze', callback_data='bronze')],
        [InlineKeyboardButton('Back', callback_data='back_pay_option')],
        [InlineKeyboardButton('Return to main menu',
                              callback_data='return_to_main_menu')],
    ]

    if user_type == 3:
        return
    elif user_type == 2:
        reply_button.pop(2)
        reply_button.pop(1)
    elif user_type == 1:
        reply_button.pop(2)

    callback_query.answer('', show_alert=False)

    client.edit_message_text(
        chat_id=uid,
        message_id=mid,
        text=config.select_plan_text,
        reply_markup=InlineKeyboardMarkup(reply_button)
    )


# 2`
@Client.on_callback_query(filters.regex(r'bronze'))
def bronze(client, callback_query):

    uid = callback_query.from_user.id

    user_info = db.search(user.id == uid)[0]
    user_type = user_info['user_type']

    if user_type != 0:

        returnn.return_to_main_manu(client, callback_query)
        callback_query.answer('', show_alert=False)
        return

    callback_query.answer('', show_alert=False)
    choise_wallet(client, callback_query, 'bronze',
                  float(config.fee['bronze']))

# 2``


@Client.on_callback_query(filters.regex(r'silver'))
def silver(client, callback_query):

    uid = callback_query.from_user.id

    user_info = db.search(user.id == uid)[0]
    user_type = user_info['user_type']
    expire = user_info['expire']

    if user_type >= 2:

        returnn.return_to_main_manu(client, callback_query)
        callback_query.answer('', show_alert=False)
        return

    fee_arg = float(config.fee['silver'])

    if expire != None:
        now = int(time.time())
        expire = int((expire - now) / 86400)
        user_type = config.user_types[user_type]
        pfee = config.fee[user_type]
        period = config.period[user_type]
        neg = float((pfee / period)) * expire
        fee_arg = float(config.fee['silver']) - neg

    callback_query.answer('', show_alert=False)
    choise_wallet(client, callback_query, 'silver', fee_arg)

# 2```


@Client.on_callback_query(filters.regex(r'gold'))
def gold(client, callback_query):

    uid = callback_query.from_user.id

    user_info = db.search(user.id == uid)[0]
    user_type = user_info['user_type']
    expire = user_info['expire']

    if user_type >= 3:

        returnn.return_to_main_manu(client, callback_query)
        callback_query.answer('', show_alert=False)
        return

    fee_arg = float(config.fee['gold'])

    if expire != None:
        now = int(time.time())
        expire = int((expire - now) / 86400)
        user_type = config.user_types[user_type]
        pfee = config.fee[user_type]
        period = config.period[user_type]
        neg = (float(pfee) / float(period)) * expire
        fee_arg = float(config.fee['gold']) - neg

    callback_query.answer('', show_alert=False)
    choise_wallet(client, callback_query, 'gold', fee_arg)


@Client.on_callback_query(filters.regex(r'revival'))
def revival(client, callback_query):

    uid = callback_query.from_user.id
    mid = callback_query.message.message_id

    user_info = db.search(user.id == uid)[0]
    user_type = user_info['user_type']
    user_type = config.user_types[user_type]
    expire = user_info['expire']
    now = int(time.time())
    expire = int((expire - now) / 86400)
    pfee = float(config.fee[user_type])
    period = float(config.period[user_type])

    neg = (pfee / period) * expire
    fee_arg = pfee - neg

    if fee_arg <= 3:
        callback_query.answer('You cant!', show_alert=False)
        return

    callback_query.answer('', show_alert=False)
    choise_wallet(client, callback_query, user_type, fee_arg)
