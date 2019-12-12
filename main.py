import logging
import logging.config
import json
from functools import wraps

from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram import Update
from pyrogram import Client
from pyrogram.api.functions.account import CheckUsername

from storage import Usernames
from config import config

logger = logging.getLogger(__name__)

updater = Updater(token=config.bot.token, use_context=True)

usernames = Usernames(autosave=False)


def load_logging_config(file_name='logging.json'):
    with open(file_name, 'r') as f:
        logging_config = json.load(f)

    logging.config.dictConfig(logging_config)


def safe_handler(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            return func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error('error while running handler callback: %s', str(e), exc_info=True)
            text = 'An error occurred while processing the message: {}'.format(str(e))
            update.message.reply_text(text)

    return wrapped


def safe_job(func):
    @wraps(func)
    def wrapped(context: CallbackContext, *args, **kwargs):
        try:
            return func(context, *args, **kwargs)
        except Exception as e:
            logger.error('error while running a job: %s', str(e), exc_info=True)
            text = 'An error occurred while running a job: {}'.format(str(e))
            context.bot.send_message(config.other.channel_id, text)

    return wrapped


@safe_handler
def on_add(update: Update, context: CallbackContext):
    logger.info('/add %s', context.args)

    if not context.args:
        update.message.reply_text('Pass one or more usernames')
        return

    for username in context.args:
        usernames.add(username)

    usernames.save()

    text = 'Usernames added.\nList: @' + ', @'.join(usernames.list)
    update.message.reply_text(text)


@safe_handler
def on_remove(update: Update, context: CallbackContext):
    logger.info('/remove %s', context.args)

    if not context.args:
        update.message.reply_text('Pass one or more usernames')
        return

    for username in context.args:
        usernames.remove(username)

    usernames.save()

    text = 'Usernames removed.\nList: @' + ', @'.join(usernames.list)
    update.message.reply_text(text)


@safe_handler
def on_list(update: Update, _):
    logger.info('/list')

    text = '@' + '\n@'.join(usernames.list)
    update.message.reply_text(text)


@safe_handler
def on_help(update: Update, _):
    logger.info('/help')

    update.message.reply_text('/list, /add, /rem')


@safe_job
def check_usernames(context: CallbackContext):
    logger.info('running job')

    username = usernames.next_username()
    logger.info('checking username @%s...', username)

    context.bot.send_message(config.other.channel_id, 'Checking @{}...'.format(username))

    with Client(**config.user, no_updates=True) as client:
        username_is_free = client.send(CheckUsername(username=username))

        if not username_is_free:
            logger.info('username is not free')

            context.bot.send_message(config.other.channel_id, '...not free')
            return

        logger.info('creating channel...')
        context.bot.send_message(config.other.channel_id, 'Username #is_free, creating channel...')

        created_channel = client.create_channel(username, 'Parked!')

        logger.info('...done')
        context.bot.send_message(config.other.channel_id, '...done')

        logger.info('updating username...')
        context.bot.send_message(config.other.channel_id, 'updating username...')

        username_updated = client.update_chat_username(created_channel.id, username)

        logger.info('...done, result: %s', username_updated)
        context.bot.send_message(config.other.channel_id, '...done, result: {}'.format(username_updated))


def main():
    load_logging_config()

    updater.dispatcher.add_handler(CommandHandler(['start', 'help'], on_help))
    updater.dispatcher.add_handler(CommandHandler('add', on_add))
    updater.dispatcher.add_handler(CommandHandler(['rem', 'remove'], on_remove))
    updater.dispatcher.add_handler(CommandHandler('list', on_list))

    updater.job_queue.run_repeating(check_usernames, interval=60*30, first=3*2)

    updater.start_polling()


if __name__ == '__main__':
    main()

