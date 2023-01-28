import json
import random
from pathlib import Path
from random import randrange

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    UnionMatch,
    MatchResult,
)

from shared.utils.control import (
    Distribute,
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
)
from shared.utils.module_related import get_command

channel = Channel.current()
channel.name("RandomFood")
channel.author("nullqwertyuiop")
channel.author("SAGIRI-kawaii")
channel.description("随机餐点")

food = json.loads((Path(__file__).parent / "food.json").read_text(encoding="utf-8"))

translation = {
    "早餐": "早餐",
    "午餐": "午餐",
    "晚餐": "晚餐",
    "夜宵": "晚餐",
    "果茶": "果茶",
    "奶茶": "奶茶",
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "supper": "晚餐",
    "tea": "奶茶",
    "drink": "果茶",
}

@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([
            get_command(__file__, channel.module),
            RegexMatch(r"rand|[随隨][机機]"),
            UnionMatch("早餐", "午餐", "晚餐", "夜宵", "breakfast", "lunch", "dinner", "supper") @ "option"
        ])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("random_meal", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def random_meal(app: Ariadne, group: Group, source: Source, option: MatchResult):
    option = translation[option.result.display]
    main_amount = 1 if option == "早餐" else 2
    dish = []
    if randrange(101) < 5:
        return "没得吃！"
    if randrange(2) if option != "午餐" else 1:
        dish.append(random.choice(food[option]["drink"]))
    if randrange(2) if option != "午餐" else 1:
        dish.append(random.choice(food[option]["pre"]))
    if not dish:
        if randrange(2):
            dish.append(random.choice(food[option]["drink"]))
        else:
            dish.append(random.choice(food[option]["pre"]))
    for _ in range(0, main_amount):
        dish.append(random.choice(food[option]["main"]))
    result = f"你的随机{option}是：\n" + " ".join(dish)
    await app.send_group_message(group, MessageChain(result), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([
            get_command(__file__, channel.module),
            RegexMatch(r"[随隨][机機]"),
            UnionMatch("奶茶", "果茶", "tea", "drink") @ "option"
        ])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("random_tea", 1),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def random_tea(app: Ariadne, group: Group, source: Source, option: MatchResult):
    option = translation[option.result.display]
    if randrange(101) < 5:
        return "没得喝！"
    body = random.choice(food[option]["body"])
    addon = ""
    cream = ""
    temperature = random.choice(food[option]["temperature"])
    sugar = random.choice(food[option]["sugar"])
    divider = "加"
    for _ in range(randrange(1, 4)):
        addon = divider + str(random.choice(food[option]["addon"]))
    if randrange(2):
        cream = divider + str(random.choice(food[option]["cream"]))
    result = f"你的随机{option}是：\n" + temperature + sugar + addon + cream + body
    await app.send_group_message(group, MessageChain(result), quote=source)
