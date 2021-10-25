# Copyright (C) 2018 - 2020 yousef saeedi. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2021 BadStyle

# This file is part of Badstylebot (Telegram Bot)

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

import html

import bs4
import jikanpy
import requests
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters

from BadStyle.decorator import register
from BadStyle.services.pyrogram import pbot

from .utils.anime import (
    airing_query,
    anime_query,
    character_query,
    manga_query,
    shorten,
    t,
)
from .utils.disable import disableable_dec

url = "https://graphql.anilist.co"


@register(cmds="انیم")
@disableable_dec("airing")
async def anime_airing(message):
    search_str = message.text.split(" ", 1)
    if len(search_str) == 1:
        await message.reply("نام انیمه را وارد کنید!")
        return

    variables = {"search": search_str[1]}
    response = requests.post(
        url, json={"query": airing_query, "variables": variables}
    ).json()["data"]["Media"]
    ms_g = f"<b>نام</b>: <b>{response['title']['romaji']}</b>(<code>{response['title']['native']}</code>)\n<b>ID</b>: <code>{response['id']}</code>"
    if response["nextAiringEpisode"]:
        airing_time = response["nextAiringEpisode"]["timeUntilAiring"] * 1000
        airing_time_final = t(airing_time)
        ms_g += f"\n<b>قسمت</b>: <code>{response['nextAiringEpisode']['episode']}</code>\n<b>زمان باقی مانده</b>: <code>{airing_time_final}</code>"
    else:
        ms_g += f"\n<b>قسمت</b>: <code>{response['episodes']}</code>\n<b>وضعیت</b>: <code>N/A</code>"
    await message.reply(ms_g)


@register(cmds="انیمه")
@disableable_dec("anime")
async def anime_search(message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await message.reply("نام انیمه را وارد کنید!")
        return
    else:
        search = search[1]
    variables = {"search": search}
    json = (
        requests.post(url, json={"query": anime_query, "variables": variables})
        .json()["data"]
        .get("Media", None)
    )
    if json:
        msg = f"<b>{json['title']['romaji']}</b>(<code>{json['title']['native']}</code>)\n<b>نوع</b>: {json['format']}\n<b>وضعیت</b>: {json['status']}\n<b>قسمت ها</b>: {json.get('episodes', 'N/A')}\n<b>مدت زمان</b>: {json.get('duration', 'N/A')} در هر قسمت.\n<b>نمره</b>: {json['averageScore']}\n<b>ژانرها</b>: <code>"
        for x in json["genres"]:
            msg += f"{x}, "
        msg = msg[:-2] + "</code>\n"
        msg += "<b>استودیوها</b>: <code>"
        for x in json["studios"]["nodes"]:
            msg += f"{x['name']}, "
        msg = msg[:-2] + "</code>\n"
        info = json.get("siteUrl")
        trailer = json.get("trailer", None)
        if trailer:
            trailer_id = trailer.get("id", None)
            site = trailer.get("site", None)
            if site == "youtube":
                trailer = "https://youtu.be/" + trailer_id
        description = (
            json.get("توضیحات", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        msg += shorten(description, info)
        image = info.replace("anilist.co/anime/", "img.anili.st/media/")
        if trailer:
            buttons = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="اطلاعات بیشتر", url=info),
                InlineKeyboardButton(text="تریلر 🎬", url=trailer),
            )
        else:
            buttons = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="اطلاعات بیشتر", url=info)
            )

        if image:
            try:
                await message.reply_photo(image, caption=msg, reply_markup=buttons)
            except:
                msg += f" [〽️]({image})"
                await message.reply(msg)
        else:
            await message.reply(msg)


@register(cmds="شخصیت")
@disableable_dec("character")
async def character_search(message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await message.reply("نام شخصیت مورد نظر را وارد کنید!")
        return
    search = search[1]
    variables = {"query": search}
    json = (
        requests.post(url, json={"query": character_query, "variables": variables})
        .json()["data"]
        .get("Character", None)
    )
    if json:
        ms_g = f"<b>{json.get('name').get('full')}</b>(<code>{json.get('name').get('native')}</code>)\n"
        description = (f"{json['description']}").replace("توضیحات", "")
        site_url = json.get("siteUrl")
        ms_g += shorten(description, site_url)
        image = json.get("image", None)
        if image:
            image = image.get("large")
            await message.reply_photo(image, caption=ms_g)
        else:
            await message.reply(ms_g)


@register(cmds="م")
@disableable_dec("manga")
async def manga_search(message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await message.reply("لطفا نام مانگا را بنویسید!")
        return
    search = search[1]
    variables = {"search": search}
    json = (
        requests.post(url, json={"query": manga_query, "variables": variables})
        .json()["data"]
        .get("Media", None)
    )
    ms_g = ""
    if json:
        title, title_native = json["title"].get("romaji", False), json["title"].get(
            "native", False
        )
        start_date, status, score = (
            json["startDate"].get("year", False),
            json.get("status", False),
            json.get("averageScore", False),
        )
        if title:
            ms_g += f"<b>{title}</b>"
            if title_native:
                ms_g += f"(<code>{title_native}</code>)"
        if start_date:
            ms_g += f"\n<b>تاریخ شروع</b> - <code>{start_date}</code>"
        if status:
            ms_g += f"\n<b>وضعیت</b> - <code>{status}</code>"
        if score:
            ms_g += f"\n<b>رتبه</b> - <code>{score}</code>"
        ms_g += "\n<b>ژانرها</b> - "
        for x in json.get("genres", []):
            ms_g += f"{x}, "
        ms_g = ms_g[:-2]

        image = json.get("bannerImage", False)
        ms_g += (
            (f"\n<i>{json.get('description', None)}</i>")
            .replace("<br>", "")
            .replace("</br>", "")
        )
        if image:
            try:
                await message.reply_photo(image, caption=ms_g)
            except:
                ms_g += f" [〽️]({image})"
                await message.reply(ms_g)
        else:
            await message.reply(ms_g)


@register(cmds="بزودی")
@disableable_dec("upcoming")
async def upcoming(message):
    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top("anime", page=1, subtype="upcoming")

    upcoming_list = [entry["title"] for entry in upcoming["top"]]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 20:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    await message.reply(upcoming_message)


async def site_search(message, site: str):
    args = message.text.split(" ", 1)
    more_results = True

    try:
        search_query = args[1]
    except IndexError:
        await message.reply("چه چیزی جستجو کنم")
        return

    if site == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "post-title"})

        if search_result:
            result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>: \n"
            for entry in search_result:
                post_link = entry.a["href"]
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
        else:
            more_results = False
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>"

    elif site == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "title"})

        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>: \n"
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>"
                more_results = False
                break

            post_link = entry.a["href"]
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    elif site == "ganime":
        search_url = f"https://gogoanime2.org/search/{search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "title"})

        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>gogoanime</code>: \n"
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>gogoanime</code>"
                more_results = False
                break

            post_link = entry.a["href"]
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="See all results", url=search_url)
    )

    if more_results:
        await message.reply(result, reply_markup=buttons, disable_web_page_preview=True)
    else:
        await message.reply(result)


@register(cmds="kaizoku")
@disableable_dec("kaizoku")
async def kaizoku(message):
    await site_search(message, "kaizoku")


@register(cmds="kayo")
@disableable_dec("kayo")
async def kayo(message):
    await site_search(message, "kayo")


@register(cmds="ganime")
@disableable_dec("ganime")
async def kayo(message):
    await site_search(message, "ganime")


@pbot.on_message(filters.command("aq"))
def quote(_, message):
    quote = requests.get("https://animechan.vercel.app/api/random").json()
    quote = truth.get("quote")
    message.reply_text(quote)


# added ganime search based on gogoanime2.org

__mod_name__ = "انیـمـــه"

__help__ = """
🤹‍♂اطلاعاتی درباره انیمه یا مانگا یا شخصیت های آنها دریافت میکنید🤹‍♀ متاسفانه سایت ایرانی برای دریافت اطلاعات وجود نداشت و ازسایت هایی با زبان خارجی استفاده شد 🤕
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ
دستــورات 🏵
ـــــــــــــــــــــــــــــ
/انیم 
مثال👈 /انیم one piece
مدت زمان باقی مانده تا شروع انیمه
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ
/انیمه
مثال👈 /انیمه one piece
 اطلاعات مربوط به انیمه 
ـــــــــــــــــــــــــــــــــــــــــــــــــــــ
/شخصیت
مثال👈 /شخصیت luffi
اطلاعات مربوط به شخصیت ها
ــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ
/مانگا
مثال👈 /مانگا one piece
اطلاعات مربوط به مانگا
ـــــــــــــــــــــــــــــــــــــــــــــــــ
/بزودی
لیست جدید فصل بعد انیمها
ــــــــــــــــــــــــــــــــــــــــــــــــــــــــ
"""
