#    Copyright (C) 2020-2021 by @bad_style
#    This programme is a part of badstyle bot project
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import time

from pyrogram import filters
from pyrogram.errors import RPCError
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelPrivate,
    ChatAdminRequired,
    PeerIdInvalid,
    UsernameNotOccupied,
    UserNotParticipant,
)
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup

from BadStyle import BOT_ID

# from BadStyle import OWNER_ID as SUDO_USERS
from BadStyle.services.pyrogram import pbot
from BadStyle.services.sql import forceSubscribe_sql as sql

logging.basicConfig(level=logging.INFO)

static_data_filter = filters.create(
    lambda _, __, query: query.data == "onUnMuteRequest"
)


@pbot.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
    try:
        user_id = cb.from_user.id
        chat_id = cb.message.chat.id
    except:
        return
    chat_db = sql.fs_settings(chat_id)
    if chat_db:
        channel = chat_db.channel
        try:
            chat_member = client.get_chat_member(chat_id, user_id)
        except:
            return
        if chat_member.restricted_by:
            if chat_member.restricted_by.id == BOT_ID:
                try:
                    client.get_chat_member(channel, user_id)
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()
                    # if cb.message.reply_to_message.from_user.id == user_id:
                    # cb.message.delete()
                except UserNotParticipant:
                    client.answer_callback_query(
                        cb.id,
                        text=f"❗ به کانال @{channel} ما بپیوند ودکمه 'لغو بیصداکردن من' را فشاردهید.",
                        show_alert=True,
                    )
                except ChannelPrivate:
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()

            else:
                client.answer_callback_query(
                    cb.id,
                    text="❗ شما توسط ادمین ها بنابر دلایلی بی صدا شده اید.",
                    show_alert=True,
                )
        else:
            if not client.get_chat_member(chat_id, BOT_ID).status == "administrator":
                client.send_message(
                    chat_id,
                    f"❗ **{cb.from_user.mention} درحال تلاش برای لغو بیصدا کردن خود است اما من نمیتوانم بی صدا بودن اورا لغو کنم زیرا من مدیر این چت نیستم دوباره مرا مدیرکنید .**\n__#ترک این چت...__",
                )

            else:
                client.answer_callback_query(
                    cb.id,
                    text="❗ هنوز عضو کانال یا گروه اجباری نشده برای لغو عضویت از دستورات استفاده کنید.",
                    show_alert=True,
                )


@pbot.on_message(filters.text & ~filters.private & ~filters.edited, group=1)
def _check_member(client, message):
    chat_id = message.chat.id
    chat_db = sql.fs_settings(chat_id)
    if chat_db:
        try:
            user_id = message.from_user.id
        except:
            return
        try:
            if (
                not client.get_chat_member(chat_id, user_id).status
                in ("administrator", "creator")
                and not user_id == 1141839926
            ):
                channel = chat_db.channel
                try:
                    client.get_chat_member(channel, user_id)
                except UserNotParticipant:
                    try:
                        sent_message = message.reply_text(
                            "خوش آمدید {} 🙏 هنوز عضو نشدی به @{}  کانال ما  🥲 \n\ nلطفا عضو [کانال یا گروه](https://t.me/{}) ما بشو و بعد روی دکمه لغو بیصداکردن من بزن. \n\ n ".format(
                                message.from_user.mention, channel, channel
                            ),
                            disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "عضو شو🙃",
                                            url="https://t.me/{}".format(channel),
                                        )
                                    ],
                                    [
                                        InlineKeyboardButton(
                                            "👾لغو بیصدا کردن من", callback_data="onUnMuteRequest"
                                        )
                                    ],
                                ]
                            ),
                        )
                        client.restrict_chat_member(
                            chat_id, user_id, ChatPermissions(can_send_messages=False)
                        )
                    except ChatAdminRequired:
                        sent_message.edit(
                            "❗ سبک بد اینجا مدیر نیست..\n__مجوزهای ممنوعیت رو به من بدهید ودوباره امتحان کنید.. \n#پایان عضویت اجباری ...__"
                        )
                    except RPCError:
                        return

                except ChatAdminRequired:
                    client.send_message(
                        chat_id,
                        text=f"❗ **من ادمین کانال @{channel} نیستم.**\n__من رو ادمین کن و دوباره امتحان کن.\n#پایان عضویت اجباری...__",
                    )
                except ChannelPrivate:
                    return
        except:
            return


@pbot.on_message(filters.command(["عضواجباری", "اجباری"]) & ~filters.private)
def config(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status is "creator" or user.user.id == 1141839926:
        chat_id = message.chat.id
        if len(message.command) > 1:
            input_str = message.command[1]
            input_str = input_str.replace("@", "")
            if input_str.lower() in ("خاموش", "غیرفعال"):
                sql.disapprove(chat_id)
                message.reply_text("❌ **عضویت اجباری با موفقیت غیرفعال شد.**")
            elif input_str.lower() in ("پاکسازی"):
                sent_message = message.reply_text(
                    "**نادیده گرفتن همه اعضایی که توسط من بی صدا شده اند ...**"
                )
                try:
                    for chat_member in client.get_chat_members(
                        message.chat.id, filter="restricted"
                    ):
                        if chat_member.restricted_by.id == BOT_ID:
                            client.unban_chat_member(chat_id, chat_member.user.id)
                            time.sleep(1)
                    sent_message.edit("✅ پاکسازی انجام شد ولی بعد از یک پیام کاربر فعال میشود اگه میخواهید اجازه چت کردن به انها بدهید بعد از پاکسازی دستور ( /عضواجباری غیرفعال ) رو اجرا کن .")
                except ChatAdminRequired:
                    sent_message.edit(
                        "❗ من در این چت ادمین نیستم.\n__من نمی توانم بیصدا بودن اعضا رو لغوکنم.__"
                    )
            else:
                try:
                    client.get_chat_member(input_str, "me")
                    sql.add_channel(chat_id, input_str)
                    message.reply_text(
                        f"✅ **عضویت اجباری فعال است**\n__عضویت اجباری فعال است ، همه اعضای گروه برای ارسال پیام باید در این  [کانال یا گروه](https://t.me/{input_str}) عضو بشن.__", 
                        disable_web_page_preview=True,
                    )
                except UserNotParticipant:
                    message.reply_text(
                        f"❗ **من ادمین کانال نیستم**\n__من ادمین نیستم در  [کانال یا گروه](https://t.me/{input_str}). برای فعال کردن عضویت اجباری من را ادمین کنید.__",
                        disable_web_page_preview=True,
                    )
                except (UsernameNotOccupied, PeerIdInvalid):
                    message.reply_text(f"❗ **نام کاربری کانال یا گروه نامعتبر .**")
                except Exception as err:
                    message.reply_text(f"❗ **خطا:** ```{err}```")
        else:
            if sql.fs_settings(chat_id):
                message.reply_text(
                    f"✅ **عضویت اجباری فعال است.**\n__برای این [Channel](https://t.me/{sql.fs_settings(chat_id).channel})__",
                    disable_web_page_preview=True,
                )
            else:
                message.reply_text("❌ **عضویت اجباری در این چت غیرفعال است.**")
    else:
        message.reply_text(
            "❗ **به مالک گروه نیاز است**\n__شما برای انجام این کار باید مالک گروه باشید.__"
        )


__help__ = """
🥇در صورت فعال بودن عضویت اجباری، افرادی که در گروه یا کانالی که برای عضویت اجباری گذاشتید نباشن از چت کردن بیصدا میکنیم و یک دکمه باصداکردن به آنها نشان می دهم.  وقتی آنها عضو ان کانال یا گروه شدن دکمه را فشار می دهند ، من به آنها اجازه چت کردن میدهم ✅

روش اســتفــاده 👇
🔅اول از همه من را در گروه و در کانال به عنوان مدیر اضافه کنید 🔅
💮 به زبان ساده هم تو گروه اصلی من رو مدیر کنید هم تو گروه یا کانالی که میخواید افراد عضو اون بشن تامام❎

❗️فقط مالک گروه میتونه از من استفاده کنه ❕

دستــورات 👇 لطفا به فاصله بین کلمات دقت کنید

/عضواجباری     یــا      /اجباری
برای نمایش دادن فعال یا غیرفعال بودن 

🧩برای روشن کردن (فعال کردن) عضویت اجباری و راه اندازی از دستور زیر استفاده کنید 👇
/عضواجباری @نام آیدی کانال یا گروه
دستور+ خط فاصله+ @ایدی کانال یا گروه

♟برای غیر فعال کردن عضویت اجباری 👇

/عضواجباری غیرفعال

⭐🔥توجه کنید بعد از غیر فعال سازی برای این که همه کاربرانی که عضویت اجباری رو انجام ندادن بتونن چت کنن دستور پاکسازی رو اجراکنید 👇

♻️پاکسازی تمام کسانی که بیصدا شدن 
/عضواجباری پاکسازی

🔆توجه کنید که میتونید از /اجباری به جای
 /عضواجباری استفاده کنید🔆
 
"""
__mod_name__ = "عضویت اجباری"
