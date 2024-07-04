import telebot
from telebot import types
import time
import sqlite3

ADMIN_ID = 'ваш id'
bot = telebot.TeleBot('токен бота')

CONTENT_TYPE = ["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact",
                "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
                "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
                "migrate_from_chat_id", "pinned_message"]


def sms(id_user, message):  # Сюда передаётся id типочка и сообщение. Вынос общей части кода крч.
    if message.photo:
        caption = message.caption
        bot.send_photo(id_user, photo=message.photo[-1].file_id, caption=caption)
    elif message.document:
        caption = message.caption
        bot.send_document(id_user, document=message.document.file_id, caption=caption)
    elif message.contact:
        bot.send_contact(id_user, phone_number=message.contact.phone_number,
                         first_name=message.contact.first_name)
    elif message.location:
        bot.send_location(id_user, latitude=message.location.latitude,
                          longitude=message.location.longitude)
    elif message.video:
        caption = message.caption
        bot.send_video(id_user, video=message.video.file_id, caption=caption)
    elif message.audio:
        caption = message.caption
        bot.send_audio(id_user, audio=message.audio.file_id, caption=caption)
    elif message.voice:
        bot.send_voice(id_user, voice=message.voice.file_id)
    elif message.sticker:
        bot.send_sticker(id_user, sticker=message.sticker.file_id)
    elif message.video_note:
        bot.send_video_note(id_user, message.video_note.file_id)
    elif message.text:
        bot.send_message(id_user, str(message.text))


@bot.message_handler(commands=['start'])  # список команд, при которых будет выполняться функция.
def main(message):
    if str(message.from_user.id) == ADMIN_ID:  # это если я запускаю клиент.
        bot.send_message(message.chat.id, f'Привет, мой величайший господин!')
        with sqlite3.connect('db_secretary.db') as db:
            cursor = db.cursor()
            cursor.execute("SELECT SUM(message_count), COUNT(*) FROM users WHERE message_count != 0")
            result = cursor.fetchone()
            print(result)
            if (result[1] > 0):
                bot.send_message(message.chat.id, f"Мишань, всего было {result[0]}"
                                                  f" сообщений от {result[1]} пользователя(ей). ")
    else:
        with sqlite3.connect('db_secretary.db') as db:
            cur = db.cursor()
            name = str(message.from_user.first_name)
            username = str(message.from_user.username)
            id = message.from_user.id
            # проверка на уникальность пользоватля
            cur.execute(f"SELECT COUNT(*) FROM users WHERE id = '{id}'")
            count = cur.fetchone()[0]
            if count == 0:
                query = f"INSERT INTO users VALUES ({id}, 0, '{name}', '{username}')"
                cur.execute(query)
        bot.send_message(message.chat.id, f'Привет, {name}! Напишите мне сообщение, будто я Михаил. '
                                          f'Последующие разы также пишите в эту переписку. Ответ придёт в этот диалог.')


@bot.message_handler(func=lambda message: message.reply_to_message != None, content_types=CONTENT_TYPE)
def reply_message_handler(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.send_message(message.chat.id, 'Ошибка! Напишите сообщение без ответа на сообщение.')
    else:
        print(message)
        with sqlite3.connect('db_secretary.db') as db:
            cur = db.cursor()
            cur.execute(f"SELECT id_user FROM sms WHERE id_message = '{message.reply_to_message.text}'")
            count = cur.fetchone()
            if count:
                sms(str(count[0]), message)
            else:
                bot.send_message(ADMIN_ID, 'Бро, что-то ты запутался. На циферки ответь')


# практически любое сообщение от пользователя (решение не самое оптимальное, но как смог)
@bot.message_handler(content_types=CONTENT_TYPE)
def info(message):
    user_id = str(message.from_user.id)
    if user_id != ADMIN_ID:

        firstname = str(message.from_user.first_name)
        lastname = str(message.from_user.last_name)
        if lastname == 'None':
            lastname = ''
        username = str(message.from_user.username)
        with sqlite3.connect('db_secretary.db') as db:
            cur = db.cursor()
            cur.execute(f"UPDATE users SET message_count = message_count +1 WHERE id ={user_id}")
            admin_notification = f"Вам пришло сообщение от {firstname} {lastname} (@{username}).Для того, чтобы ему ответить, напишите ответ на следующее сообщение:"
            bot.send_message(ADMIN_ID, admin_notification)
            bot.send_message(ADMIN_ID, str(message.id))
            sms(ADMIN_ID, message)
            query = f"INSERT INTO sms VALUES ('{user_id}', '{message.id}')"
            cur.execute(query)


bot.polling(none_stop=True)  # постоянная работа программы
