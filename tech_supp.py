import os
import time
import dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import gspread
import sqlite3

from fuzzywuzzy import process

name = None
surname = None
phone_number = None
adress = None

NA_name = None
NA_tg_id = None

dotenv.load_dotenv(".env")
api_key = os.environ["TOKEN"]
g_table = os.environ["google_table"]
g_table_access = os.environ["table_access"]
questions_chat_id = os.environ["send_to_chat"]

bot = telebot.TeleBot(api_key)

gc = gspread.service_account(filename=g_table_access)
s = gc.open_by_url(g_table)
worksheet1 = s.worksheet("main_table")
worksheet2 = s.worksheet("FAQ")
list_of_lists = worksheet1.get_all_values()
list_of_questions = worksheet2.get_all_values()

category_list = []
for x in list_of_lists:
    if x[4] not in category_list:
        category_list.append(x[4])
del category_list[category_list.index('Категория')]

category_keyboard = InlineKeyboardMarkup()

for category in category_list:
    category_keyboard.add(InlineKeyboardButton(category, callback_data="aa" + category))
category_keyboard.add(InlineKeyboardButton("Ссылка", url=g_table))

questions_list = []
for x in list_of_questions:
    if x[1] not in questions_list:
        questions_list.append(x[1])
questions_list.remove("Вопрос")

answers_list = []
for x in list_of_questions:
    if x[2] not in answers_list:
        answers_list.append(x[2])
answers_list.remove("Ответ")

QA_diction = dict(zip(questions_list, answers_list))

menu_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
menu_markup.row("Программы", "Рейтинг")
menu_markup.row("F.A.Q", "Задать вопрос")

app_diction = {}
for x in list_of_lists:
    app_diction[x[0]] = {}
    app_diction[x[0]]["Информация"] = x[1]
    app_diction[x[0]]["Инструкция"] = x[2]
    app_diction[x[0]]["Фото"] = x[3]
    app_diction[x[0]]["Категория"] = x[4]

markup = InlineKeyboardMarkup()
markup.add(InlineKeyboardButton("Меню", callback_data="qq"))

markup_card = InlineKeyboardMarkup()
markup_card.add(InlineKeyboardButton("Подробнее", callback_data="x"))


@bot.message_handler(commands=['admin'])
def admin_check(message):
    if message.text == "/admin":
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        id_2check = message.from_user.id
        cur.execute("""SELECT * FROM admins WHERE tg_id = ?""", (id_2check,))
        data = cur.fetchone()
        print(data)
        if data[2] == id_2check and data[3] == 2:
            s_admin_keyb = InlineKeyboardMarkup(row_width=2)
            s_admin_keyb.add(InlineKeyboardButton("Понизить админа", callback_data="AL"),
                             InlineKeyboardButton("Добавить админа", callback_data="AA"),
                             InlineKeyboardButton("Вернуть админа", callback_data="RA"),
                             InlineKeyboardButton("Удалить админа", callback_data="DA"),
                             InlineKeyboardButton("Список пользователей", callback_data="UL"))

            bot.send_message(message.chat.id, text="Добро пожаловать, супер-админ!", reply_markup=s_admin_keyb)

        elif data[2] == id_2check and data[3] == 1:
            admin_keyb = InlineKeyboardMarkup(row_width=2)
            admin_keyb.add(InlineKeyboardButton("Список пользователей", callback_data="UL"))
            bot.send_message(message.chat.id, text="Добро пожаловать, админ!", reply_markup=admin_keyb)
        else:
            pass
        cur.close()
        conn.close()


@bot.message_handler(commands=['new_admin'])
def new_admin(message):
    global NA_name, NA_tg_id
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cur = conn.cursor()
    id_2check = message.from_user.id
    cur.execute("""SELECT * FROM admins WHERE tg_id = ?""", (id_2check,))
    data = cur.fetchone()
    print(data)
    if data[2] == id_2check and data[3] == 2:
        bot.send_message(message.chat.id, "Введите имя нового админа")
        bot.register_next_step_handler(message, new_admin_name)


def new_admin_name(message):
    global NA_name
    NA_name = message.text.strip()
    bot.send_message(message.chat.id, "Введите tg_id нового админа")
    bot.register_next_step_handler(message, id_save)


def id_save(message):
    global NA_tg_id
    NA_tg_id = message.text.strip()
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""INSERT INTO admins (name, tg_id, STATUS) VALUES ('%s','%s','%s')""" % (NA_name, NA_tg_id, 1))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, "Администратор добавлен")


@bot.message_handler(commands=['start'])
def start(message):
    global name, surname, phone_number, adress, contacts
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cur = conn.cursor()
    code = message.from_user.id
    cur.execute("""SELECT * FROM users WHERE unique_id = ?""", (code,))

    if cur.fetchone() is not None:
        bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=markup)

    else:
        bot.send_message(message.chat.id,
                         "👋, перед началом работы с ботом необходимо зарегистрироваться!\nВведи имя:")  # NAME
        bot.register_next_step_handler(message, user_name_save)


def user_name_save(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, f"Отлично,{name}\nВведи фамилию:")  # SURNAME
    bot.register_next_step_handler(message, user_surname_save)


def user_surname_save(message):
    global surname
    surname = message.text.strip()
    bot.send_message(message.chat.id, " Ваш номер мобильного телефона: ")
    bot.register_next_step_handler(message, phone_number_save)


def phone_number_save(message):
    global phone_number
    phone_number = message.text.strip()
    bot.send_message(message.chat.id, "Введите адрес для доставки:")
    bot.register_next_step_handler(message, adress_save)


def adress_save(message):
    global adress
    adress = message.text.strip()
    bot.send_message(message.chat.id, "И последнее, оставь контакты для связи(эл. почта,vk)")
    bot.register_next_step_handler(message, finish_reg)


def finish_reg(message):
    contacts = message.text.strip()
    unique_id = message.from_user.id
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (name,surname,telephone,adress,contacts, unique_id) VALUES ('%s','%s','%s','%s','%s','%s')""" % (
            name, surname, phone_number, adress, contacts, unique_id))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, f"Вы зарегистрированы!\n "
                                      f"Ваш уникальный идентификатор: {unique_id}",
                     reply_markup=markup)


@bot.message_handler(content_types=["text"])
def menu_buttons(message):
    global questions_list, answers_list
    if message.text == "Программы" or message.text == "Возвращаемся в меню":
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        bot.send_message(message.chat.id, "Выберите нужную категорию: ", reply_markup=category_keyboard)
    if message.text == "Задать вопрос":
        question_keyb = InlineKeyboardMarkup()
        question_keyb.add(InlineKeyboardButton("F.A.Q", callback_data="FQ"),
                          InlineKeyboardButton("Остались вопросы", callback_data="ZZ"))
        bot.send_message(message.chat.id,
                         f"Перед тем как задать вопрос, рекомендуем ознакомиться с наиболее часто задаваемыми вопросами в разделе F.A.Q",
                         reply_markup=question_keyb)
    if message.text == "F.A.Q":
        faq_keyb = InlineKeyboardMarkup()
        faq_keyb.add(InlineKeyboardButton("F.A.Q", url="https://t.me/+A1cBuW4XadExM2Q6"))
        bot.send_message(message.chat.id, text="F.A.Q здесь", reply_markup=faq_keyb)
    if "???" in message.text:
        stars_keyb = InlineKeyboardMarkup()
        a = process.extract(message.text, questions_list, limit=1)
        percents = a[0]
        print("Процент совпадений:", percents)
        if percents[1] >= 60:
            stars_keyb = InlineKeyboardMarkup(row_width=5)
            stars_keyb.add(InlineKeyboardButton(text="1⭐", callback_data="1⭐"),
                           InlineKeyboardButton(text="2⭐", callback_data="2⭐"),
                           InlineKeyboardButton(text="3⭐", callback_data="3⭐"),
                           InlineKeyboardButton(text="4⭐", callback_data="4⭐"),
                           InlineKeyboardButton(text="5⭐", callback_data="5⭐"))
            bot.send_message(chat_id=message.chat.id,
                             text="Найдено совпадение по вашему вопросу!")
            bot.send_message(chat_id=message.chat.id,
                             text=f"{QA_diction[percents[0]]}\n\nОцените, насколько ответ был полезен",
                             reply_markup=stars_keyb)
        else:
            bot.send_message(chat_id=message.chat.id,
                             text="Спасибо за обращение! Ваш вопрос находится на рассмотрении оператора.")
            bot.send_message(chat_id=questions_chat_id, text=f"У пользователя {message.from_user.id} вопрос 👇")
            bot.forward_message(chat_id=questions_chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
    if "!!!" in message.text:
        menu_markup = InlineKeyboardMarkup()
        menu_markup.add(InlineKeyboardButton("В меню", callback_data="qq"))
        bot.send_message(chat_id=questions_chat_id, text="📩Требуется модерация инструкции👇")
        bot.forward_message(chat_id=questions_chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
        bot.send_message(chat_id=message.chat.id,
                         text="Благодарим, ваша корректировка теперь находится на рассмотрении!",
                         reply_markup=menu_markup)
    if message.text == "Рейтинг":
        top_keyb = InlineKeyboardMarkup()
        top_keyb.add(InlineKeyboardButton("ТОП рейтинговых", callback_data="TR"),
                     InlineKeyboardButton("ТОП частых", callback_data="TP"))
        bot.send_message(chat_id=message.chat.id, text="Рейтинг ТОП-5 вопросов", reply_markup=top_keyb)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    bot.answer_callback_query(callback_query_id=call.id, )
    id = call.message.chat.id
    flag = call.data[:2]
    data = call.data[2:]
    print("flag = ", flag)
    print("data = ", data)

    if flag == "qq":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(id, "🎊Меню🎊", reply_markup=menu_markup)

    if flag == "aa":
        apps = []
        for list_ in list_of_lists:
            if list_[4] == data and list_[0] not in apps:
                apps.append(list_[0])

        apps_keyb = InlineKeyboardMarkup()
        for app in apps:
            apps_keyb.add(InlineKeyboardButton(app, callback_data="22" + app))
        apps_keyb.add(InlineKeyboardButton("назад", callback_data="MM"))
        bot.edit_message_text(chat_id=id, message_id=call.message.message_id,
                              text=f'Выберите приложение из категории "{data}"', reply_markup=apps_keyb)

    if flag == "22":
        global instr_keyb
        instr_keyb = InlineKeyboardMarkup()
        instr_keyb.add(InlineKeyboardButton("Инструкция", callback_data="++" + data))
        instr_keyb.add(InlineKeyboardButton("В меню", callback_data="MM"))
        # buf = ''
        for list_ in list_of_lists:
            if list_[0] == data:
                # buf = x[0]
                bot.send_photo(id, photo=f"{list_[3]}", caption=f"{list_[0]}\n{list_[1]}", reply_markup=instr_keyb)

    if flag == "++":
        info_keyb = InlineKeyboardMarkup()
        info_keyb.add(InlineKeyboardButton("Информация", callback_data="??" + data))
        info_keyb.add(InlineKeyboardButton("В меню", callback_data="MM"))
        info_keyb.add(InlineKeyboardButton("Редактировать", callback_data="--" + data))

        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                 caption=f"{data}\n{app_diction[data]['Инструкция']}", reply_markup=info_keyb)
    if flag == "??":
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                 caption=f"{data}\n{app_diction[data]['Информация']}", reply_markup=instr_keyb)

    if flag == "MM":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(chat_id=id, text="Меню", reply_markup=menu_markup)

    if flag == "ZZ":
        bot.send_message(chat_id=id, text=f'📝Опишите ваш вопрос ниже и отправьте его боту✍\n\n'
                                          'В начале сообщения поставьте три вопросительных знака(???)')
    if flag == "--":
        sure_keyb = InlineKeyboardMarkup()
        sure_keyb.add(InlineKeyboardButton("Да", callback_data="Ys"), InlineKeyboardButton("Нет", callback_data="No"))
        bot.send_message(chat_id=call.message.chat.id, text="Вы уверены, что хотите изменить инструкцию?",
                         reply_markup=sure_keyb)
    if flag == "No":
        bot.delete_message(chat_id=id, message_id=call.message.message_id)
    if flag == "Ys":
        bot.send_message(chat_id=id, text=f"Напишите ваши корректировки и я отправлю их на модерацию\n"
                                          "В начале сообщения поставьте три восклицательных знака (!!!)")

    if flag[1] == "⭐":
        global questions_list, answers_list
        a = process.extract(call.message.text, questions_list, limit=1)
        percents = a[0]
        stars = flag[0]
        print(stars)
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cur = conn.cursor()
        ans = call.message.text.replace('Оцените, насколько ответ был полезен', '').strip()
        print(str(ans))
        cur.execute(
            f"""UPDATE QA_ratings SET number_of_ratings = number_of_ratings + 1, average_score = ((average_score * number_of_ratings)+{stars})/(number_of_ratings + 1) WHERE answer = '{ans}';""")
        conn.commit()
        cur.close()
        conn.close()
        bot.edit_message_text(chat_id=id, message_id=call.message.message_id,
                              text=f"{QA_diction[percents[0]]}\n\nОцените, насколько ответ был полезен",
                              reply_markup=None)
        bot.send_message(chat_id=id, text="Ваш отзыв учтён!")

    if flag == "AL":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        STATUS = 1
        cur.execute("""SELECT * FROM admins WHERE STATUS = ?""", (STATUS,))
        data = cur.fetchall()
        print(data)
        admins_listing = InlineKeyboardMarkup()

        for el in data:
            admins_listing.add(InlineKeyboardButton(text=el[1], callback_data="ai" + str(el[2])))
        bot.send_message(id, "Список администраторов", reply_markup=admins_listing)

    if flag == "ai":
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        admin_data = call.data.replace("ai", "")
        cur.execute("""UPDATE admins
        SET STATUS = 0
        WHERE tg_id =?""", (admin_data,))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(chat_id=call.message.chat.id, text="Администратор разжалован")

    if flag == "AA":
        bot.send_message(id, text="Добавление админов осуществляется по команде /new_admin")
    if flag == "DA":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        STATUS = 0
        cur.execute("""SELECT * FROM admins WHERE STATUS = ?""", (STATUS,))
        data = cur.fetchall()
        print(data)
        admins_listing = InlineKeyboardMarkup()

        for el in data:
            admins_listing.add(InlineKeyboardButton(text=el[1], callback_data="ai" + str(el[2])))
        bot.send_message(id, "Список администраторов", reply_markup=admins_listing)
        bot.send_message(id, "Если список пуст, сначала понизьте существующего админа")

    if flag == "RA":
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        STATUS = 0
        cur.execute("""SELECT * FROM admins WHERE STATUS = ?""", (STATUS,))
        data = cur.fetchall()
        print(data)
        admins_listing = InlineKeyboardMarkup()
        for el in data:
            admins_listing.add(InlineKeyboardButton(text=el[1], callback_data="re" + str(el[2])))
        bot.send_message(id, "Список бывших администраторов", reply_markup=admins_listing)
        bot.send_message(id, "Если список пуст, значит некого возвращать")

    if flag == "re":
        admin_id = call.data.replace('re', "")
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute(f"""UPDATE admins SET STATUS = 1 WHERE tg_id = {admin_id}""")
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(chat_id=call.message.chat.id, text="Администратор восстановлен")
    if flag == "TR":
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM QA_ratings ORDER BY average_score DESC LIMIT 5""")
        top5 = cur.fetchmany(5)
        bot.send_message(chat_id=call.message.chat.id, text="Топ рейтинговых вопросов⬇")

        for el in top5:
            bot.send_message(chat_id=call.message.chat.id, text=f"Вопрос: {el[1]}\n{round(el[3], 2)}⭐")
            time.sleep(0.5)
        bot.send_message(chat_id=call.message.chat.id, text="Вопросы?😎")
        conn.commit()
        cur.close()
        conn.close()

    if flag == "TP":
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM QA_ratings ORDER BY number_of_ratings DESC LIMIT 5""")
        top5 = cur.fetchmany(5)
        bot.send_message(chat_id=call.message.chat.id, text="Топ популярных вопросов👇")

        for el in top5:
            bot.send_message(chat_id=call.message.chat.id, text=f"Вопрос: {el[1]}\nБыл задан {el[4]} раз!")
            time.sleep(0.5)
        bot.send_message(chat_id=call.message.chat.id, text="Во 🗿👍🏽")

        conn.commit()
        cur.close()
        conn.close()
    if flag == "FQ":
        faq_keyb = InlineKeyboardMarkup()
        faq_keyb.add(InlineKeyboardButton("F.A.Q", url="https://t.me/+A1cBuW4XadExM2Q6"))
        bot.send_message(call.message.chat.id, text="F.A.Q здесь", reply_markup=faq_keyb)
    if flag == "UL":
        conn = sqlite3.connect("users.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM users""")
        people = cur.fetchall()
        print(people)
        for user in people:
            bot.send_message(chat_id=call.message.chat.id, text=f"Пользователь: {user[1], user[2].strip()}\n"
                                                                f"Моб.тел: {user[3]}\n"
                                                                f"Адрес: {user[4]}\n"
                                                                f"Контакты: {user[5]}\n"
                                                                f"Уникальный ID: {user[6]}")
            time.sleep(0.3)


print('Ready')
bot.infinity_polling()
