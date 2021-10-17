from pyrogram import Client, filters
from . import main_menu, config
from pyrogram.types import (
	InlineKeyboardMarkup,
	InlineKeyboardButton
)
from tinydb import TinyDB, Query
import openpyxl


db = TinyDB('user.json')
user = Query()


@Client.on_callback_query(filters.create(
	func = lambda filter, client, update: update.data.split('-')[0] == 'return1'
))
def return1(client, callback_query):

	uid = callback_query.from_user.id
	mid = callback_query.message.message_id
	ex = callback_query.data.split('-')
	row = ex[1]
	file_name = ex[2]

	reply_button = [
		[
			InlineKeyboardButton(
				'Yes',
				callback_data = f'yes1-{row}-{file_name}' # [1] => row, [2] => file  
			),
			InlineKeyboardButton(
				'No',
				callback_data = f'no1-{row}-{file_name}'
			),
		]
	]

	client.edit_message_text(
		chat_id = uid,
		message_id = mid,
		text = config.question_text,
		reply_markup = InlineKeyboardMarkup(reply_button)
	)





@Client.on_callback_query(filters.create(
	func = lambda filter, client, update: update.data.split('-')[0] == 'yes1'
))
def show_question(client, callback_query):

	ex = callback_query.data.split('-')
	row = ex[1]
	file_name = ex[2]

	path = f'files/{str(file_name)}.xlsx'

	callback_query.answer('', show_alert=False)

	wb_obj = openpyxl.load_workbook(path)
	sheet_obj = wb_obj.active

	reply_button = [
		[
			InlineKeyboardButton(
				'Cancel',
				callback_data = f'cancel1-{row}-{file_name}'
			)
		]
	]

	client.edit_message_text(
		chat_id = callback_query.from_user.id,
		message_id = callback_query.message.message_id,
		text = str(sheet_obj.cell(row = int(row), column = 2).value),
		reply_markup = InlineKeyboardMarkup(reply_button)
	)

	mid = callback_query.message.message_id
	db.update({'status': 2, 'memo': f'{mid}-{row}-{file_name}'}, user.id == callback_query.from_user.id)


@Client.on_callback_query(filters.create(
	func = lambda filter, client, update: update.data.split('-')[0] == 'no1'
))
def down_show(client, callback_query):

	ex = callback_query.data.split('-')
	row = ex[1]
	file_name = ex[2]

	callback_query.answer('', show_alert=False)

	reply_button = [
		[
			InlineKeyboardButton(
				'Confirm',
				callback_data = 'del_post'
			)
		],
		[
			InlineKeyboardButton(
				'Return',
				callback_data = f'return1-{row}-{file_name}'
			)
		],
	]

	client.edit_message_text(
		chat_id = callback_query.from_user.id,
		message_id = callback_query.message.message_id,
		text = config.confirm_delete_text,
		reply_markup = InlineKeyboardMarkup(reply_button)
	)


@Client.on_callback_query(filters.regex('del_post'))
def delete_quesion(client, callback_query):

	callback_query.answer('', show_alert=False)
	callback_query.message.delete()
	client.send_message(
		chat_id = callback_query.from_user.id,
		text = config.delete_quesion_text
	)
	main_menu.show_menu(client, callback_query.from_user.id)


@Client.on_callback_query(filters.create(
	func = lambda filter, client, update: update.data.split('-')[0] == 'cancel1'
))
def canceling(client, callback_query):

	ex = callback_query.data.split('-')
	row = ex[1]
	file_name = ex[2]

	db.update({'status': 0, 'memo': None}, user.id == callback_query.from_user.id)

	callback_query.answer('', show_alert=False)

	reply_button = [
		[
			InlineKeyboardButton(
				'Confirm cancel',
				callback_data = 'del_post'
			)
		],
		[
			InlineKeyboardButton(
				'Return',
				callback_data = f'yes1-{row}-{file_name}'
			)
		],
	]

	client.edit_message_text(
		chat_id = callback_query.from_user.id,
		message_id = callback_query.message.message_id,
		text = config.confirm_cancel_text,
		reply_markup = InlineKeyboardMarkup(reply_button)
	)



@Client.on_message(filters.text & filters.create(
	func = lambda filter, client, update: db.search(user.id == update.from_user.id)[0]['status'] == 2
))
def get_answer(client, message):

	uid = message.from_user.id
	mid = message.message_id
	user_info = db.search(user.id == uid)[0]

	memo = user_info['memo'].split('-')
	del_mid = int(memo[0])
	row = memo[1]
	file_name = memo[2]

	client.delete_messages(
		chat_id = uid,
		message_ids = del_mid
	)




	reply_button = [
		[
			InlineKeyboardButton(
				'Confirm answer',
				callback_data = 'end'
			)
		],
		[
			InlineKeyboardButton(
				'Change',
				callback_data = f'yes1-{row}-{file_name}'
			)
		],
	]

	client.send_message(
		chat_id = uid,
		text = config.confirm_your_answer_text,
		reply_to_message_id = mid,
		reply_markup = InlineKeyboardMarkup(reply_button)
	)

	db.update({'status': 0}, user.id == uid)


@Client.on_callback_query(filters.regex('end'))
def end(client, callback_query):

	reply_to_message_text = callback_query.message.reply_to_message.text
	uid = callback_query.from_user.id
	mid = callback_query.message.message_id

	user_info = db.search(user.id == uid)[0]
	memo = user_info['memo'].split('-')

	row = memo[1]
	file_name = memo[2]

	answers = TinyDB(f'files/answers/{file_name}.json')
	query   = Query()

	search_for_answer = answers.search(query.sender == uid)
	if len(search_for_answer) == 0:
		answers.insert({
			'sender': uid,
			'answer': reply_to_message_text
		})

	else:
		answers.update({'answer': reply_to_message_text}, query.sender == uid)


	client.edit_message_text(
		chat_id = uid,
		message_id = mid,
		text = config.after_answer_text
	)

	main_menu.show_menu(client, callback_query.from_user.id)

















