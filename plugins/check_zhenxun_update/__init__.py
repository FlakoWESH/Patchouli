import os
import platform
from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import ArgStr
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from configs.config import NICKNAME, Config
from services.log import logger
from utils.utils import get_bot, scheduler

from .data_source import check_update, get_latest_version_data

__zx_plugin_name__ = "自动更新 [Superuser]"
__plugin_usage__ = """
usage：
    检查更新帕秋莉最新版本，包括了自动更新
    指令：
        检查更新帕秋莉
        重启
""".strip()
__plugin_des__ = "就算是帕秋莉也会成长的"
__plugin_cmd__ = ["检查更新帕秋莉", "重启"]
__plugin_version__ = 0.1
__plugin_author__ = "HibiKier"
__plugin_configs__ = {
    "UPDATE_REMIND": {
        "value": True,
        "help": "帕秋莉是否检测版本状态",
        "default": True,
        "type": bool,
    },
    "AUTO_UPDATE_ZHENXUN": {
        "value": False,
        "help": "帕秋莉是否自动检查更新",
        "default": False,
        "type": bool,
    },
}

update_zhenxun = on_command("检查更新帕秋莉", permission=SUPERUSER, priority=1, block=True)

restart = on_command(
    "重启",
    aliases={"restart"},
    permission=SUPERUSER,
    rule=to_me(),
    priority=1,
    block=True,
)


@update_zhenxun.handle()
async def _(bot: Bot, event: MessageEvent):
    try:
        code, error = await check_update(bot)
        if error:
            logger.error(f"错误: {error}", "检查更新帕秋莉")
            await bot.send_private_msg(
                user_id=event.user_id, message=f"更新帕秋莉未知错误 {error}"
            )
    except Exception as e:
        logger.error(f"更新帕秋莉未知错误", "检查更新帕秋莉", e=e)
        await bot.send_private_msg(
            user_id=event.user_id,
            message=f"更新帕秋莉未知错误 {type(e)}: {e}",
        )
    else:
        if code == 200:
            await bot.send_private_msg(user_id=event.user_id, message=f"更新完毕，请重启帕秋莉....")


@restart.got("flag", prompt=f"确定是否重启{NICKNAME}？确定请回复[是|好|确定]（重启失败咱们将失去联系，请谨慎！）")
async def _(flag: str = ArgStr("flag")):
    if flag.lower() in ["true", "是", "好", "确定", "确定是"]:
        await restart.send(f"开始重启{NICKNAME}..请稍等...")
        open("is_restart", "w")
        if str(platform.system()).lower() == "windows":
            import sys

            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            os.system("./restart.sh")
    else:
        await restart.send("已取消操作...")


@scheduler.scheduled_job(
    "cron",
    hour=12,
    minute=0,
)
async def _():
    if Config.get_config("check_zhenxun_update", "UPDATE_REMIND"):
        _version = "v0.0.0"
        _version_file = Path() / "__version__"
        if _version_file.exists():
            _version = (
                open(_version_file, "r", encoding="utf8")
                .readline()
                .split(":")[-1]
                .strip()
            )
        data = await get_latest_version_data()
        if data:
            latest_version = data["name"]
            if _version.lower() != latest_version.lower():
                bot = get_bot()
                await bot.send_private_msg(
                    user_id=int(list(bot.config.superusers)[0]),
                    message=f"检测到帕秋莉版本更新\n" f"当前版本：{_version}，最新版本：{latest_version}",
                )
                if Config.get_config("check_zhenxun_update", "AUTO_UPDATE_ZHENXUN"):
                    try:
                        code = await check_update(bot)
                    except Exception as e:
                        logger.error(f"更新帕秋莉未知错误 {type(e)}：{e}")
                        await bot.send_private_msg(
                            user_id=int(list(bot.config.superusers)[0]),
                            message=f"更新帕秋莉未知错误 {type(e)}：{e}\n",
                        )
                    else:
                        if code == 200:
                            await bot.send_private_msg(
                                user_id=int(list(bot.config.superusers)[0]),
                                message=f"更新完毕，请重启{NICKNAME}....",
                            )