import asyncio
from pathlib import Path
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import ResultValue, Twilight, WildcardMatch
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema

from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

channel = Channel.current()
channel.name("Text Escape")
channel.author("Minepig")
channel.description("插入零宽空格")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                WildcardMatch() @ "msg",
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("escape", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def escape(app: Ariadne, group: Group, source: Source, msg: MessageChain = ResultValue()):
    text = msg.display
    reply = MessageChain("\ufeff".join(text.split()))
    await app.send_group_message(group, reply, quote=source)



