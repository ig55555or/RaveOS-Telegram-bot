import requests
import json
import telebot
import threading
import sqlite3

tlgAPIkey = 'your key'

conn = sqlite3.connect("base.db", check_same_thread=False)
cursor = conn.cursor()
bot = telebot.TeleBot(tlgAPIkey)


def getJson(key):
    try:
        r = requests.get('https://oapi.raveos.com/v1/get_workers',
                         headers={'X-Auth-Token': key})

        if r.status_code != 200:
            return 'Ошибка запроса ', r.status_code
        else:
            return json.loads(r.text)

    except Exception as e:
        print(e)
        return 'Ошибка ' + str(e)


@bot.message_handler(commands=['start'])
def start(message):
    sql = "SELECT * FROM users WHERE chatid=?"
    cursor.execute(sql, [(str(message.chat.id))])
    id = cursor.fetchone()
    if id == None:
        sql = "INSERT INTO users (chatid) VALUES (?)"
        cursor.execute(sql, (str(message.chat.id),))
        conn.commit()
        msg = bot.reply_to(message, 'Вы не зарегистрированы, введите ваш api key')
        bot.register_next_step_handler(msg, saveapikey)
    elif id[1] == None:
        msg = bot.reply_to(message, 'Вы не зарегистрированы, введите ваш api key')
        bot.register_next_step_handler(msg, saveapikey)
    else:
        bot.send_message(message.chat.id, ('Вы зарегистрированы, ваш id: ' + str(message.chat.id)))
        bot.send_message(message.chat.id, ('Ваш apikey: ' + str(id[1])))

@bot.message_handler(commands=['stop'])
def stop(message):
    sql = "DELETE FROM users WHERE chatid=?"
    cursor.execute(sql, [(str(message.chat.id))])
    bot.send_message(message.chat.id, 'Ваши данные удалены из бота')
    conn.commit()

def saveapikey(message):
    data = str(getJson(message.text))
    if data.find('Ошибка') > 0:
        msg = bot.reply_to(message, 'Введите apikey еще раз ' + data)
        bot.register_next_step_handler(msg, saveapikey)
        return
    else:
        sql = "UPDATE users SET apikey = ? WHERE chatid = ?"
        cursor.execute(sql, (message.text, (str(message.chat.id))))
        bot.send_message(message.chat.id, 'Регистрация завершена, теперь вы будете получать уведомления, если хотя бы '
                                          'один из ваших ригов офлайн. Проверка выполняется раз в 5 минут. '
                                          'Для удаления аккаунта из бота введите /stop')
        conn.commit()


def f():
    threading.Timer(300.0, f).start()  # Перезапуск через 5 секунд
    #print("300 секунд прошло")
    sql = 'SELECT * FROM users'
    cursor.execute(sql)
    users = cursor.fetchall()

    for i in range(len(users)):
        data = getJson(users[i][1])
        if isinstance(data, dict):
            for workers in data['workers']:
                if workers['status'] == 0:
                    bot.send_message(users[0][i], (workers['name'] + ' off'))
                # else:
                #    bot.send_message(users[0][i], (workers['name'] + ' on'))
        else:
            print(data)



f()

bot.polling()
