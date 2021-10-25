# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2021 TeamBadStyle
# Copyright (C) 2020 Inuka Asith

# This file is part of Daisy (Telegram Bot)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from time import sleep
from os import getenv

from pyrogram import Client
from pyrogram.raw.functions.messages import Search
from pyrogram.raw.types import InputPeerSelf, InputMessagesFilterEmpty
from pyrogram.raw.types.messages import ChannelMessages
from pyrogram.errors import FloodWait, UnknownError

from aiogram.dispatcher.filters import CommandStart

from BadStyle.decorator import register
from BadStyle.services.mongo import db

from .utils.connections import chat_connection
from .utils.disable import disableable_dec
from .utils.language import get_strings_dec
from .utils.notes import (
    ALLOWED_COLUMNS,
    BUTTONS,
    get_parsed_note_list,
    send_note,
    t_unparse_note_item,
)

class Cleaner:
    def __init__(self, chats=None, search_chunk_size=100, delete_chunk_size=100):
        self.chats = chats or []
        if search_chunk_size > 100:
            # https://github.com/gurland/telegram-delete-all-messages/issues/31
            #
            # The issue is that pyrogram.raw.functions.messages.Search uses
            # pagination with chunks of 100 messages. Might consider switching
            # to search_messages, which handles pagination transparently.
            raise ValueError('search_chunk_size > 100 not supported')
        self.search_chunk_size = search_chunk_size
        self.delete_chunk_size = delete_chunk_size

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l.
        https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks#answer-312464"""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    @staticmethod
    def get_all_chats():
        dialogs = app.get_dialogs(pinned_only=True)

        dialog_chunk = app.get_dialogs()
        while len(dialog_chunk) > 0:
            dialogs.extend(dialog_chunk)
            dialog_chunk = app.get_dialogs(offset_date=dialogs[-1].top_message.date-1)

        return [d.chat for d in dialogs]

    def select_groups(self):
        chats = self.get_all_chats()
        groups = [c for c in chats if c.type in ('group', 'supergroup')]

        print('Delete all your messages in')
        for i, group in enumerate(groups):
            print(f'  {i+1}. {group.title}')

        print(
            f'  {len(groups) + 1}. '
            '(!) DELETE ALL YOUR MESSAGES IN ALL OF THOSE GROUPS (!)\n'
        )

        nums_str = input('Insert option numbers (comma separated): ')
        nums = map(lambda s: int(s.strip()), nums_str.split(','))

        for n in nums:
            if not 1 <= n <= len(groups) + 1:
                print('Invalid option selected. Exiting...')
                exit(-1)

            if n == len(groups) + 1:
                print('\nTHIS WILL DELETE ALL YOUR MESSSAGES IN ALL GROUPS!')
                answer = input('Please type "I understand" to proceed: ')
                if answer.upper() != 'I UNDERSTAND':
                    print('Better safe than sorry. Aborting...')
                    exit(-1)
                self.chats = groups
                break
            else:
                self.chats.append(groups[n - 1])
        
        groups_str = ', '.join(c.title for c in self.chats)
        print(f'\nSelected {groups_str}.\n')

    def run(self):
        for chat in self.chats:
            peer = app.resolve_peer(chat.id)
            message_ids = []
            add_offset = 0

            while True:
                q = self.search_messages(peer, add_offset)
                message_ids.extend(msg.id for msg in q['messages'])
                messages_count = len(q['messages'])
                print(f'Found {messages_count} of your messages in "{chat.title}"')
                if messages_count < self.search_chunk_size:
                    break
                add_offset += self.search_chunk_size

            self.delete_messages(chat.id, message_ids)

    def delete_messages(self, chat_id, message_ids):
        print(f'Deleting {len(message_ids)} messages with message IDs:')
        print(message_ids)
        for chunk in self.chunks(message_ids, self.delete_chunk_size):
            try:
                app.delete_messages(chat_id=chat_id, message_ids=chunk)
            except FloodWait as flood_exception:
                sleep(flood_exception.x)

    def search_messages(self, peer, add_offset):
        print(f'Searching messages. OFFSET: {add_offset}')
        return app.send(
            Search(
                peer=peer,
                q='',
                filter=InputMessagesFilterEmpty(),
                min_date=0,
                max_date=0,
                offset_id=0,
                add_offset=add_offset,
                limit=self.search_chunk_size,
                max_id=0,
                min_id=0,
                hash=0,
                from_id=InputPeerSelf()
            ),
            sleep_threshold=60
        )


if __name__ == '__main__':
    try:
        deleter = Cleaner()
        deleter.select_groups()
        deleter.run()
    except UnknownError as e:
        print(f'UnknownError occured: {e}')
        print('Probably API has changed, ask developers to update this utility')
    finally:
        app.stop()
@register(cmds=["setrules", "saverules"], user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("rules")
async def set_rules(message, chat, strings):
    chat_id = chat["chat_id"]

    # FIXME: documents are allow to saved (why?), check for args if no 'reply_to_message'
    note = await get_parsed_note_list(message, allow_reply_message=True, split_args=-1)
    note["chat_id"] = chat_id

    if (
        await db.rules.replace_one({"chat_id": chat_id}, note, upsert=True)
    ).modified_count > 0:
        text = strings["updated"]
    else:
        text = strings["saved"]

    await message.reply(text % chat["chat_title"])


@register(cmds="rules")
@disableable_dec("rules")
@chat_connection(only_groups=True)
@get_strings_dec("rules")
async def rules(message, chat, strings):
    chat_id = chat["chat_id"]
    send_id = message.chat.id

    if "reply_to_message" in message:
        rpl_id = message.reply_to_message.message_id
    else:
        rpl_id = message.message_id

    if len(args := message.get_args().split()) > 0:
        arg1 = args[0].lower()
    else:
        arg1 = None
    noformat = arg1 in ("noformat", "raw")

    if not (db_item := await db.rules.find_one({"chat_id": chat_id})):
        await message.reply(strings["not_found"])
        return

    text, kwargs = await t_unparse_note_item(
        message, db_item, chat_id, noformat=noformat
    )
    kwargs["reply_to"] = rpl_id

    await send_note(send_id, text, **kwargs)


@register(cmds="resetrules", user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("rules")
async def reset_rules(message, chat, strings):
    chat_id = chat["chat_id"]

    if (await db.rules.delete_one({"chat_id": chat_id})).deleted_count < 1:
        await message.reply(strings["not_found"])
        return

    await message.reply(strings["deleted"])


BUTTONS.update({"rules": "btn_rules"})


@register(CommandStart(re.compile("btn_rules")))
@get_strings_dec("rules")
async def rules_btn(message, strings):
    chat_id = (message.get_args().split("_"))[2]
    user_id = message.chat.id
    if not (db_item := await db.rules.find_one({"chat_id": int(chat_id)})):
        await message.answer(strings["not_found"])
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id)
    await send_note(user_id, text, **kwargs)


async def __export__(chat_id):
    rules = await db.rules.find_one({"chat_id": chat_id})
    if rules:
        del rules["_id"]
        del rules["chat_id"]

        return {"rules": rules}


async def __import__(chat_id, data):
    rules = data
    for column in [i for i in data if i not in ALLOWED_COLUMNS]:
        del rules[column]

    rules["chat_id"] = chat_id
    await db.rules.replace_one({"chat_id": rules["chat_id"]}, rules, upsert=True)


__mod_name__ = "Rules"

__help__ = """
<b>Available Commands:</b>
- /setrules (rules): saves the rules (also works with reply)
- /rules: Shows the rules of chat if any!
- /resetrules: Resets group's rules
"""
