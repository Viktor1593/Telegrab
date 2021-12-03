import os
import re
import configparser

# pip install pyTelegramBotAPI
import telebot
from telebot.types import Message


# ---------------- Config ---------------- #
password = 'testpass'
source_chat_password = 'source_chat_password'
settingsPath = './setings.ini'
# ---------------- Config ---------------- #


config = None
contexts = {}


def getSettings():
    global config
    if config is None:
        config = configparser.ConfigParser()
    if os.path.exists(settingsPath):
        config.read(settingsPath)

    if 'default' not in config:
        config['default'] = {}

    config['default'] = checkConfig(config['default'])
    saveConfig(config)
    return config


def saveConfig(config):
    with open(settingsPath, 'w') as f:
        config.write(f)


def editConfig(**kwargs):
    global config
    for k, v in kwargs.items():
        config['default'][k] = v
    
    with open(settingsPath, 'w') as f:
        config.write(f)


def checkConfig(config):
    defaults = {
        'token': '',
        'admin_id': '',
        'source_chat_id': '',
        'target_chat_id': '',
        'pattern': '',
        'replacement': ''
    }
    config = {**defaults, **config}
    if config['token'] == '':
        config['token'] = input("Please, input bot Token: ")
        
    return config


def setContext(message: Message, context: str):
    global contexts
    contexts[message.chat.id] = context
    print(contexts)

def checkContext(message: Message, context: str):
    if message.chat.id not in contexts:
        return False
    return contexts[message.chat.id] == context


def checkAdmin(message: Message):
    if message.from_user.id == int(config['default']['admin_id']):
        return True

    bot.reply_to(message, 'You are not my admin')
    return False


config = getSettings()
bot = telebot.TeleBot(config['default']['token'])


@bot.message_handler(commands = ['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "\n".join([
        '/start /help - print this message',
        '/set_admin - Set you as admin. need to enter password. Works in private',
        '/set_source_chat - Set chat as source for copy',
        '/set_target_chat - Set chat as target for copy',
        '/set_pattern - Setup message replacement'
    ]))


# Admin setup
@bot.message_handler(commands = ['set_admin'], func = lambda message: message.chat.type == 'private')
def set_admin(message: Message):
    setContext(message, 'set_admin')
    bot.send_message(message.chat.id, 'Enter password')


@bot.message_handler(func = lambda message: checkContext(message, 'set_admin'))
def check_password(message: Message):
    if message.text != password:
        bot.send_message(message.chat.id, 'Wrong password')
    else:
        setContext(message, None)
        editConfig(admin_id = str(message.chat.id))
        bot.send_message(message.chat.id, 'You are admin now')


# Set source chat
@bot.message_handler(commands = ['set_source_chat'])
def set_source_chat(message: Message):
    setContext(message, 'set_source_chat')
    bot.send_message(message.chat.id, 'Enter password')

@bot.message_handler(func = lambda message: checkContext(message, 'set_source_chat'))
def check_source_password(message: Message):
    if message.text != source_chat_password:
        bot.send_message(message.chat.id, 'Wrong password')
        return

    setContext(message, None)
    editConfig(source_chat_id = str(message.chat.id))
    bot.send_message(message.chat.id, 'Chat is saved as source')


# Set target chat
@bot.message_handler(commands = ['set_target_chat'])
def set_target_chat(message: Message):
    if not checkAdmin(message):
        return

    editConfig(target_chat_id = str(message.chat.id))
    bot.send_message(message.chat.id, 'Chat is saved as target')


# Set pattern 
@bot.message_handler(commands = ['set_pattern'])
def set_pattern(message: Message):
    setContext(message, 'set_pattern')
    bot.send_message(message.chat.id, 'Enter pattern')


@bot.message_handler(func = lambda message: checkContext(message, 'set_pattern'))
def save_pattern(message: Message):
    if not checkAdmin(message):
        return

    setContext(message, 'set_replacement')
    editConfig(pattern = str(message.text))
    bot.send_message(message.chat.id, 'Enter replacement')


@bot.message_handler(func = lambda message: checkContext(message, 'set_replacement'))
def save_replacement(message: Message):
    if not checkAdmin(message):
        return

    setContext(message, None)
    editConfig(replacement = str(message.text))
    bot.send_message(message.chat.id, 'replacement and pattern saved')


# Coping
@bot.message_handler(func = lambda message: message.chat.id == int(config['default']['source_chat_id']))
def copy(message: Message):
    default = config['default']
    message_id = bot.copy_message(default['target_chat_id'], message.chat.id, message.id).message_id
    text = message.text
    if 'pattern' in default and 'replacement' in default:
        text = text.replace(default['pattern'], default['replacement'])
        # text = re.sub(default['pattern'], default['replacement'], text)
    bot.edit_message_text(text, default['target_chat_id'], message_id)


bot.infinity_polling()
