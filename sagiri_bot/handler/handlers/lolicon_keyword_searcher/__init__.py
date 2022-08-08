import os
import aiohttp
import asyncio
import PIL.Image
import contextlib
from io import BytesIO
from datetime import datetime
from aiohttp import TCPConnector

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Source
from graia.ariadne.message.parser.twilight import FullMatch, RegexMatch, RegexResult
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from sagiri_bot.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)
from sagiri_bot.orm.async_orm import orm
from sagiri_bot.internal_utils import group_setting
from sagiri_bot.config import GlobalConfig
from sagiri_bot.orm.async_orm import Setting, LoliconData

saya = Saya.current()
channel = Channel.current()

channel.name("LoliconKeywordSearcher")
channel.author("SAGIRI-kawaii")
channel.description("一个接入lolicon api的插件，在群中发送 `来点{keyword}[色涩瑟]图` 即可")

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""
image_cache = config.data_related.get("lolicon_image_cache")
data_cache = config.data_related.get("lolicon_data_cache")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("来点"),
                    RegexMatch(r"[^\s]+") @ "keyword",
                    RegexMatch(r"[色涩瑟]图$"),
                ]
            )
        ],
        decorators=[
            FrequencyLimit.require("lolicon_keyword_searcher", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SETU),
        ],
    )
)
async def lolicon_keyword_searcher(
    app: Ariadne, group: Group, source: Source, keyword: RegexResult
):
    keyword = keyword.result.display
    if not await group_setting.get_setting(group, Setting.setu):
        return await app.send_group_message(group, MessageChain("这是正规群哦~没有那种东西的呢！lsp爬！"))
    msg_chain = await get_image(group, keyword)
    if msg_chain.only(Plain):
        return await app.send_group_message(group, msg_chain, quote=source)
    mode = await group_setting.get_setting(group, Setting.r18_process)
    r18 = await group_setting.get_setting(group, Setting.r18)
    if mode == "revoke" and r18:
        msg = await app.send_group_message(group, msg_chain, quote=source)
        await asyncio.sleep(20)
        with contextlib.suppress(UnknownTarget):
            await app.recall_message(msg)
    elif mode == "flashImage" and r18:
        await app.send_group_message(
            group, msg_chain.exclude(Image), quote=source
        )
        await app.send_group_message(
            group, MessageChain([msg_chain.get_first(Image).to_flash_image()])
        )
    else:
        await app.send_group_message(group, msg_chain, quote=source)


async def get_image(group: Group, keyword: str) -> MessageChain:
    word_filter = ("&", "r18", "&r18", "%26r18")
    r18 = await group_setting.get_setting(group.id, Setting.r18)
    if any(i in keyword for i in word_filter):
        return MessageChain("你注个寄吧")
    url = f"https://api.lolicon.app/setu/v2?r18={1 if r18 else 0}&keyword={keyword}"
    async with aiohttp.ClientSession(
        connector=TCPConnector(verify_ssl=False)
    ) as session:
        async with session.get(url=url, proxy=proxy) as resp:
            result = await resp.json()
    logger.info(result)
    if result["error"]:
        return MessageChain(result["error"])
    if result["data"]:
        result = result["data"][0]
    else:
        return MessageChain(f"没有搜到有关{keyword}的图哦～有没有一种可能，你的xp太怪了？")

    if data_cache:
        await orm.insert_or_update(
            LoliconData,
            [LoliconData.pid == result["pid"], LoliconData.p == result["p"]],
            {
                "pid": result["pid"],
                "p": result["p"],
                "uid": result["uid"],
                "title": result["title"],
                "author": result["author"],
                "r18": result["r18"],
                "width": result["width"],
                "height": result["height"],
                "tags": "|".join(result["tags"]),
                "ext": result["ext"],
                "upload_date": datetime.utcfromtimestamp(
                    int(result["uploadDate"]) / 1000
                ),
                "original_url": result["urls"]["original"],
            },
        )

    info = f"title: {result['title']}\nauthor: {result['author']}\nurl: {result['urls']['original']}"
    file_name = result["urls"]["original"].split("/").pop()
    local_path = (
        config.image_path.get("setu18") if r18 else config.image_path.get("setu")
    )
    file_path = os.path.join(local_path, file_name)

    if os.path.exists(file_path):
        return MessageChain(
            [
                Plain(text=f"你要的{keyword}涩图来辣！\n"),
                Image(path=file_path),
                Plain(text=f"\n{info}"),
            ]
        )
    async with aiohttp.ClientSession(
        connector=TCPConnector(verify_ssl=False)
    ) as session:
        async with session.get(url=result["urls"]["original"], proxy=proxy) as resp:
            img_content = await resp.read()
    if image_cache:
        image = PIL.Image.open(BytesIO(img_content))
        image.save(file_path)
    return MessageChain(
        [
            Plain(text=f"你要的{keyword}涩图来辣！\n"),
            Image(data_bytes=img_content),
            Plain(text=f"\n{info}"),
        ]
    )