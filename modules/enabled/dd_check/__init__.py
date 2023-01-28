from graia.scheduler import timers
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.saya import SchedulerSchema
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, Image
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.event.message import Group, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexResult, WildcardMatch

from .utils import get_reply, update_vtb_list
from shared.utils.module_related import get_command
from shared.utils.control import (
    FrequencyLimit,
    Function,
    BlackListControl,
    UserCalledCountControl,
    Distribute
)

saya = Saya.current()
channel = Channel.current()

channel.name("DDCheck")
channel.author("SAGIRI-kawaii")
channel.description("一个查成分的插件，在群中发送 /查成分 {B站UID} 即可")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([get_command(__file__, channel.module), WildcardMatch() @ "username"])],
        decorators=[
            Distribute.distribute(),
            FrequencyLimit.require("dd_check", 2),
            Function.require(channel.module, notice=True),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.SEARCH),
        ],
    )
)
async def dd_check(app: Ariadne, group: Group, source: Source, username: RegexResult):
    user = username.result.display.strip()
    if not user:
        return await app.send_group_message(
            group, MessageChain("空白名怎么查啊kora！"), quote=source
        )
    if not user.isdigit():
        return await app.send_group_message(
            group, MessageChain("暂时查不了用户名orz，请输入B站UID"), quote=source
        )
    res = await get_reply(user)
    await app.send_group_message(
        group,
        MessageChain(res if isinstance(res, str) else [Image(data_bytes=res)]),
        quote=source,
    )


@channel.use(SchedulerSchema(timer=timers.every_custom_hours(3)))
async def dd_check_schedule():
    await update_vtb_list()
