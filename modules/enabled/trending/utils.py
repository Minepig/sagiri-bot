import datetime
import random
import aiohttp
from loguru import logger
from bs4 import BeautifulSoup

from creart import create
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Forward, ForwardNode
from shared.models.config import GlobalConfig

config = create(GlobalConfig)
proxy = config.proxy if config.proxy != "proxy" else ""


async def get_weibo_trending() -> MessageChain:
    weibo_hot_url = "https://api.weibo.cn/2/guest/search/hot/word"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=weibo_hot_url) as resp:
            data = await resp.json()
    data = data["data"]
    now = datetime.datetime.now()
    time_count = -(len(data) + 10)
    forward_nodes = [
        ForwardNode(
            sender_id=config.default_account,
            time=now + datetime.timedelta(seconds=time_count),
            sender_name="纱雾酱",
            message_chain=MessageChain(f"随机数:{random.randint(0, 10000)}" + "\n微博实时热榜:"),
        )
    ]
    time_count += 1
    for index, item in enumerate(data, start=1):
        text = f"{index}. " + item["word"].replace("#", "").strip() + f" ({item['num']})"
        forward_nodes.append(
            ForwardNode(
                sender_id=config.default_account,
                time=now + datetime.timedelta(seconds=time_count),
                sender_name="纱雾酱",
                message_chain=MessageChain(text),
            )
        )
        time_count += 1

    return MessageChain(Forward(node_list=forward_nodes))


async def get_zhihu_trending() -> MessageChain:
    zhihu_hot_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=zhihu_hot_url) as resp:
            data = await resp.json()
    data = data["data"]
    now = datetime.datetime.now()
    time_count = -(len(data) + 10)
    forward_nodes = [
        ForwardNode(
            sender_id=config.default_account,
            time=now + datetime.timedelta(seconds=time_count),
            sender_name="纱雾酱",
            message_chain=MessageChain(f"随机数:{random.randint(0, 10000)}" + "\n知乎实时热榜:"),
        )
    ]
    time_count += 1
    for index, item in enumerate(data, start=1):
        text = f"{index}. " + item["target"]["title"].strip() + f" ({item['detail_text']})"
        forward_nodes.append(
            ForwardNode(
                sender_id=config.default_account,
                time=now + datetime.timedelta(seconds=time_count),
                sender_name="纱雾酱",
                message_chain=MessageChain(text),
            )
        )
        time_count += 1

    return MessageChain(Forward(node_list=forward_nodes))


async def get_github_trending() -> MessageChain:
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.141 Safari/537.36 "
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers, proxy=proxy) as resp:
            html = await resp.read()
    soup = BeautifulSoup(html, "html.parser")
    articles = list(soup.find_all("article", {"class": "Box-row"}))

    now = datetime.datetime.now()
    time_count = -(len(articles) + 10)
    forward_nodes = [
        ForwardNode(
            sender_id=config.default_account,
            time=now + datetime.timedelta(seconds=time_count),
            sender_name="纱雾酱",
            message_chain=MessageChain(f"随机数:{random.randint(0, 10000)}" + "\ngithub实时热榜:"),
        )
    ]
    time_count += 1

    for index, item in enumerate(articles, start=1):
        try:
            title = (
                item.find("h1")
                .get_text()
                .replace("\n", "")
                .replace(" ", "")
                .replace("\\", " \\ ")
            )
            desc = item.find('p').get_text().strip()
            text = f"{index}. {title}\n\n    {desc}"
            forward_nodes.append(
                ForwardNode(
                    sender_id=config.default_account,
                    time=now + datetime.timedelta(seconds=time_count),
                    sender_name="纱雾酱",
                    message_chain=MessageChain(text),
                )
            )
            time_count += 1
        except Exception as e:
            logger.error(e)

    return MessageChain(Forward(node_list=forward_nodes))
