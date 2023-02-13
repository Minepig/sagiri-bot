from datetime import datetime, timedelta

from creart import create
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import At
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import Group, Member, GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, ElementMatch

from shared.models.config import GlobalConfig
from shared.utils.module_related import get_command
from shared.utils.control import Function, Permission, BlackListControl, UserCalledCountControl, Distribute

channel = Channel.current()

channel.name("MessageRevoke")
channel.author("SAGIRI-kawaii")
channel.description("一个可以自动撤回之前发送消息的插件，在群中对要撤回消息回复 '撤回' 即可")

config = create(GlobalConfig)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                ElementMatch(At, optional=True),
                get_command(__file__, channel.module)
            ])
        ],
        decorators=[
            Distribute.distribute(require_admin=True),
            Function.require(channel.module),
            BlackListControl.enable(),
            UserCalledCountControl.add(UserCalledCountControl.FUNCTIONS),
        ],
    )
)
async def message_revoke(app: Ariadne, group: Group, member: Member, event: GroupMessage):
    print(app.account)
    if event.quote:
        if msg := await app.get_message_from_id(event.quote.id, group):
            if event.quote.sender_id in config.bot_accounts:
                await Ariadne.current(event.quote.sender_id).recall_message(msg, group)
            else:
                if event.quote.sender_id == member.id:
                    if datetime.now().replace(tzinfo=None) - event.source.time.replace(tzinfo=None) < timedelta(minutes=2):
                        return await app.send_message(group, "你自己没有手是吧，没超过两分钟自己撤回！")
                elif not await Permission.check(group, member, 3):
                    return await app.send_message(group, "爪巴，你没有权限撤回其他人的消息！")
                try:
                    await app.recall_message(msg, group)
                except PermissionError:
                    await app.send_message(group, "俗话说官大一级压死人捏，我没有权限诶！")
        else:
            await app.send_message(group, "消息太过久远啦，找管理员处理吧！")
