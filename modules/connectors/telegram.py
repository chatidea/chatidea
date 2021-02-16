import telepot
import re
from telepot.loop import MessageLoop

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from modules import extractor, caller
from settings import TOKEN_TELEGRAM


# on any simple message
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if msg.get('text'):
        respond(chat_id, msg['text'])


# buttons have been clicked
def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
    message_text = msg.get('message').get('reply_markup').get('inline_keyboard')
    """if re.match("/sel_by_pos{\"pos\":\"\d+\"}",query_data): #check if sel_by_pos intent
        for m in message_text:
            if query_data == m[0]['callback_data']:
                text_title = m[0]['text']
                query_data = query_data[:-1]
                query_data += ";" + '"title":' + '"' + text_title + '"}'
                break"""
    respond(chat_id, query_data)


def respond(chat_id, msg):
    parsed_message = extractor.parse(msg)
    response = caller.run_action_from_parsed_message(parsed_message, "TELEGRAM_"+str(chat_id))
    # print(response.get_printable_string())
    for x in response.get_telegram_or_webchat_format():
        text = x['message']
        if text == 'Pie chart':
            pie = open('static/pie.png', 'rb')
            bot.sendPhoto(chat_id, pie)
        else:
            inline_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=b['title'], callback_data=b['payload'])]
                    for b in x['buttons']
                ]
            ) if x['buttons'] else None
            """
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='/ciao. ' + b['title'])]
                    for b in x['buttons']
                ]
            ) if x['buttons'] else None
            """
            bot.sendMessage(chat_id=chat_id, text=text, reply_markup=inline_keyboard)


def start():
    global bot
    bot = telepot.Bot(TOKEN_TELEGRAM)
    MessageLoop(bot, {'chat': on_chat_message,
                      'callback_query': on_callback_query}).run_as_thread()
