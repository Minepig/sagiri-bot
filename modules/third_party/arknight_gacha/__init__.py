import csv
import random
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple

import aiohttp
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.message.parser.twilight import MatchResult, ParamMatch, Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    Interval, UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("Arknight Gacha Simulator")
channel.author("Minepig")
channel.description("经过一些轻度魔改的明日方舟寻访模拟器")

GACHA_DATA_PATH = Path(__file__).parent / "gacha_data.csv"
CUSTOM_CHARACTER_PATH = Path(__file__).parent / "custom_character.csv"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                ParamMatch(optional=True) @ "num"
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("sudo", 1),
            Interval.require(suspend_time=15, silent=True),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def gacha(app: Ariadne, group: Group, source: Source, num: MatchResult):
    count = 10
    if num.matched:
        _num = num.result.display
        if _num.isdigit():
            count = int(_num)
    if count <= 0 or count >= 21:
        await app.send_group_message(group, MessageChain("寻访次数只能为1~20的整数"), quote=source)
        return

    if gacha_list is None or limited_list is None:
        await load_gacha_data()

    data = group_data[group.id]
    result = []
    for i in range(count):
        r = random.randrange(1000)
        prob_6 = 20 + max(data.bonus6 - 49, 0) * 20
        prob_5 = 80 + max(data.bonus5 - 14, 0) * 20

        if data.chaos > 0:  # THRM-EX things
            l = gacha_list[1] + gacha_list[2] + gacha_list[3] + gacha_list[4] + gacha_list[5] + gacha_list[6]
            result.append(random.choice(l))
            data.chaos -= 1
        elif r < 2:  # Custom Operators
            result.append(random.choice(gacha_list[6]))
            data.bonus6 = 0
            data.bonus5 = 0
        elif r < min(980, prob_6):
            if data.limit > 0:  # Lancet-2 things
                result.append(random.choice(limited_list))
                data.limit -= 1
            else:
                result.append(random.choice(gacha_list[5]))
            data.bonus6 = 0
            data.bonus5 = 0
        elif r < min(980, prob_6 + prob_5):
            result.append(random.choice(gacha_list[4]))
            data.bonus6 += 1
            data.bonus5 = 0
        elif r < min(980, prob_6 + prob_5 + 500):
            result.append(random.choice(gacha_list[3]))
            data.bonus6 += 1
            data.bonus5 += 1
        elif r < 980:
            if data.custom > 0:  # Justice Knight things
                result.append(random.choice(gacha_list[6]))
                data.custom -= 1
            else:
                result.append(random.choice(gacha_list[2]))
            data.bonus6 += 1
            data.bonus5 += 1
        elif r < 995:
            result.append(random.choice(gacha_list[1]))
            data.bonus6 += 1
            data.bonus5 += 1
        else:
            op = random.choice(gacha_list[0])
            result.append(op)
            data.bonus6 += 1
            data.bonus5 += 1
            if op.name == "Castle-3":
                data.bonus6 += 40
            elif op.name == "Lancet-2":
                data.limit += 1
            elif op.name == "正义骑士号":
                data.custom += 1
            elif op.name == "THRM-EX":
                data.chaos += 1 + data.bonus6//10

    reply = "本次寻访结果：\n" + "、".join(str(op.rarity) + "★" + op.name for op in result)
    await app.send_group_message(group, MessageChain(reply), quote=source)


class Operator(NamedTuple):
    name: str
    rarity: int


class GachaData(object):
    __slots__ = ("bonus6", "bonus5", "limit", "custom", "chaos")

    def __init__(self):
        self.bonus6 = 0
        self.bonus5 = 0
        self.limit = 0
        self.custom = 0
        self.chaos = 0


gacha_list: tuple[list[Operator], ...] | None = None
limited_list: list[Operator] | None = None
group_data: defaultdict[int, GachaData] = defaultdict(GachaData)


async def load_gacha_data():
    global gacha_list, limited_list
    gacha_list = ([], [], [], [], [], [], [])
    limited_list = []

    if not GACHA_DATA_PATH.exists():
        await fetch_gacha_data()

    with GACHA_DATA_PATH.open("r", encoding="u8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rarity = int(row["rarity"])
            if int(row["sortId"]) < 0 and rarity < 4:
                continue
            if row["name"] == "阿米娅(近卫)":
                continue
            op = Operator(row["name"], rarity+1)
            gacha_list[rarity].append(op)
            if row["approach"] == "限定寻访" and rarity >= 5:
                limited_list.append(op)

    with CUSTOM_CHARACTER_PATH.open("r", encoding="u8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            op = Operator(row["name"], int(row["rarity"]))
            gacha_list[6].append(op)


class MyHTMLParser(HTMLParser):
    def handle_data(self, data):
        if data.startswith("sortId,name,rarity,approach,date"):
            with GACHA_DATA_PATH.open("w", encoding="utf-8") as f:
                f.write(data)


parser = MyHTMLParser()


async def fetch_gacha_data():
    url = "https://prts.wiki/w/%E5%B9%B2%E5%91%98%E4%B8%80%E8%A7%88/%E5%B9%B2%E5%91%98id"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as resp:
            parser.feed(await resp.text())
    await load_gacha_data()


@channel.use(SchedulerSchema(timer=timers.every_custom_hours(3)))
async def arknight_schedule():
    await fetch_gacha_data()