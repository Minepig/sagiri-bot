import aiohttp
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne

from graia.ariadne.exception import MessageTooLong
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.element import Plain, Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import ArgumentMatch, RegexResult, RegexMatch, ArgResult

from sagiri_bot.internal_utils import get_command
from utils.text_engine.adapter import GraiaAdapter
from utils.text_engine.text_engine import TextEngine
from sagiri_bot.control import FrequencyLimit, Function, BlackListControl, UserCalledCountControl

saya = Saya.current()
channel = Channel.current()

channel.name("GithubInfo")
channel.author("SAGIRI-kawaii")
channel.description("可以搜索Github项目信息的插件，在群中发送 `/github [-i] {项目名}`")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ArgumentMatch("-i", "-image", action="store_true", optional=True) @ "image",
                RegexMatch(r"[^\s]+") @ "keyword"
            ])
        ],
        decorators=[
            FrequencyLimit.require("github_info", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS)
        ]
    )
)
async def github_info(app: Ariadne, group: Group, source: Source, image: ArgResult, keyword: RegexResult):
    image = image.matched
    keyword = keyword.result.display
    url = "https://api.github.com/search/repositories?q="
    img_url = "https://opengraph.githubassets.com/c9f4179f4d560950b2355c82aa2b7750bffd945744f9b8ea3f93cc24779745a0/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url + keyword) as resp:
            result = (await resp.json())["items"]
    if not result:
        await app.send_group_message(group, MessageChain("没有搜索到结果呢~"), quote=source)
    elif image:
        img_url += result[0]["full_name"]
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                content = await resp.read()
        await app.send_group_message(group, MessageChain([Image(data_bytes=content)]), quote=source)
    else:
        result = result[0]
        name = result["name"]
        owner = result["owner"]["login"]
        description = result["description"]
        repo_url = result["html_url"]
        stars = result["stargazers_count"]
        watchers = result["watchers"]
        language = result["language"]
        forks = result["forks"]
        issues = result["open_issues"]
        repo_license = result["license"]["key"] if result["license"] else "无"
        msg = MessageChain([
            Plain(text=f"名称：{name}\n"),
            Plain(text=f"作者：{owner}\n"),
            Plain(text=f"描述：{description}\n"),
            Plain(text=f"链接：{repo_url}\n"),
            Plain(text=f"stars：{stars}\n"),
            Plain(text=f"watchers：{watchers}\n"),
            Plain(text=f"forks：{forks}\n"),
            Plain(text=f"issues：{issues}\n"),
            Plain(text=f"language：{language}\n"),
            Plain(text=f"license：{repo_license}")
        ])
        try:
            await app.send_group_message(group, msg, quote=source)
        except MessageTooLong:
            await app.send_group_message(
                group,
                MessageChain([Image(data_bytes=TextEngine([GraiaAdapter(msg)]).draw())]),
                quote=source
            )