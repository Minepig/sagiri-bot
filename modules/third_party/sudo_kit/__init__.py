import asyncio
from pathlib import Path
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.ariadne.message.parser.twilight import FullMatch, Twilight, UnionMatch
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
channel.name("Sudo Kit")
channel.author("Minepig")
channel.description("群管理员执法工具")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                get_command(__file__, channel.module),
                UnionMatch("remove", "rm", "r"),
                FullMatch("-rf /*")
            ])
        ],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("sudo", 1),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def tarot(app: Ariadne, group: Group, source: Source):
    file_path = Path("resources") / "image" / "mother_removed.png"
    await app.send_group_message(group, MessageChain("执行命令中，正在删除文件……"), quote=source)
    await asyncio.sleep(1)
    await app.send_group_message(group, MessageChain(Image(path=file_path)))



