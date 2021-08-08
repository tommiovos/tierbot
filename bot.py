#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import os
import json
import threading

from pathlib import Path
from dotenv import load_dotenv
from os.path import join, dirname
from twitchio.ext import commands
import eel

dir_path = os.path.dirname(os.path.realpath(__file__))
dotenv_path = join(dir_path, '.env')
load_dotenv(dotenv_path)

online = False
switch_to_next = False
tierlist_images = None
poll_open = False
current_elem_tier = None

# credentials
TMI_TOKEN = os.environ.get('TMI_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
BOT_NICK = os.environ.get('BOT_NICK')
BOT_PREFIX = os.environ.get('BOT_PREFIX')
CHANNEL = os.environ.get('CHANNEL')

JSON_FILE = str(os.path.dirname(os.path.realpath(__file__))) + '/data.json'

bot = commands.Bot(
    irc_token=TMI_TOKEN,
    client_id=CLIENT_ID,
    nick=BOT_NICK,
    prefix=BOT_PREFIX,
    initial_channels=[CHANNEL]
)


def run_server(web, html):
    thread = threading.Thread(target=eel_loop, args=[web, html])
    thread.start()


def eel_loop(web, html):
    eel.init(web)
    eel.start(html, block=False)

    global current_elem_tier
    global tierlist_images
    while online:
        if tierlist_images is not None:
            eel.create_elements_list(tierlist_images)
            tierlist_images = None
        if current_elem_tier is not None:
            eel.place_element_in_tierlist(current_elem_tier)
            current_elem_tier = None
        eel.sleep(0.3)


@bot.event
async def event_ready():
    """ Runs once the bot has established a connection with Twitch """
    print(f"{BOT_NICK} is online!")


@bot.event
async def event_message(ctx):
    """ 
    Runs every time a message is sent to the Twitch chat and relays it to the 
    command callbacks 
    """

    # the bot should not react to itself
    if ctx.author.name.lower() == BOT_NICK.lower():
        return

    # relay message to command callbacks
    await bot.handle_commands(ctx)


# =========== Tier-list Commands =========== #

@bot.command(name='tier')
async def on_tier(ctx):
    if ctx.author.is_mod:
        command_str = ctx.message.content
        command_str = command_str.replace('!tier', '')
        if command_str:
            command_args = command_str.split(' ')
            command_args = [i for i in command_args if i]
            command = command_args[0]
            arg = None if len(command_args) == 1 else command_args[1]
            await ctx.send(exec_tier_cmd(command, arg))


def exec_tier_cmd(command: str, arg: str) -> str:
    if command == 'start':
        return tier_start(arg)
    if command == 'rate':
        return tier_rate(arg)
    else:
        return f'Command "! tier {command}" is not valid.'


def tier_rate(tier: str):
    if tier in ['S', 'A', 'B', 'C', 'D']:
        global current_elem_tier
        current_elem_tier = tier
        return f'Successfully set element in tier {tier} !'
    else:
        return f'Rank {tier} isn\'t valid'


def tier_start(folder: str):
    if folder is None:
        return 'Please specify an existing folder name for the tier-list'
    if Path.is_dir(folder_path := Path(dir_path) / 'web' / 'tierlists' / folder):
        images_png = Path(folder_path).glob('*.png')
        images_jpg = Path(folder_path).glob('*.jpg')
        images_jpeg = Path(folder_path).glob('*.jpeg')
        images_paths = [*images_png, *images_jpg, *images_jpeg]
        init_tierlist_page(images_paths)
        return 'Tier-list found, starting...'
    else:
        return 'Specified tier-list folder not found'


def init_tierlist_page(images_paths):
    global online
    global tierlist_images
    if not online:
        online = True
        images_paths = [str(i) for i in images_paths]
        images_paths_str = []
        for path in images_paths:
            splited = path.split('\\')
            splited_len = len(splited)
            images_paths_str.append(f'./tierlists/{splited[splited_len-2]}/{splited[splited_len - 1]}')
        tierlist_images = images_paths_str
        run_server('web', 'tierlist.html')


if __name__ == "__main__":
    # launch bot
    bot.run()
