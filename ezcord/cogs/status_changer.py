import inspect
import random
from dataclasses import asdict
from itertools import cycle

from ..bot import Bot, Cog
from ..internal.dc import discord


def watching(name):
    return discord.Activity(type=discord.ActivityType.watching, name=name)


def listening(name):
    return discord.Activity(type=discord.ActivityType.listening, name=name)


ACTIVITY_TYPES = {
    "custom": discord.CustomActivity,
    "watching": watching,
    "listening": listening,
    "playing": discord.Game,
}


class Activity(Cog, hidden=True):
    def __init__(self, bot: Bot):
        super().__init__(bot)

        activities: list[discord.Activity] = []
        for key, value in asdict(self.bot.status_changer).items():
            if key == "streaming":
                for act in value:
                    activities.append(act)
                continue
            if key not in ACTIVITY_TYPES or value is None:
                continue
            for act_name in value:
                # convert string name to discord.Activity
                activities.append(ACTIVITY_TYPES[key](act_name))

        random.shuffle(activities)

        self.activities = cycle(activities)

    @discord.ext.commands.Cog.listener()
    async def on_ready(self):
        if not self.change_activity.is_running():
            self.change_activity.change_interval(seconds=self.bot.status_changer.interval)
            self.change_activity.start()

    @discord.ext.tasks.loop()
    async def change_activity(self):
        replace_values = {
            "guild_count": f"{len(self.bot.guilds):,}",
            "user_count": f"{len(self.bot.users):,}",
        }

        act = next(self.activities)

        for key, value in replace_values.items():
            act.name = act.name.replace("{" + key + "}", value)

        if self.bot.status_changer.kwargs:
            for key, value in self.bot.status_changer.kwargs.items():
                if inspect.iscoroutinefunction(value):
                    act_name = await value()
                elif callable(value):
                    act_name = value()
                else:
                    act_name = value

                act.name = act.name.replace("{" + str(key) + "}", str(act_name))

        await self.bot.change_presence(activity=act, status=self.bot.status_changer.status)


def setup(bot: Bot):
    bot.add_cog(Activity(bot))
