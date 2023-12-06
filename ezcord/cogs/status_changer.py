import inspect
import random
from itertools import cycle

from ..bot import Bot, Cog
from ..internal.dc import discord, tasks


class Activity(Cog, hidden=True):
    def __init__(self, bot: Bot):
        super().__init__(bot)

        activities = [
            discord.CustomActivity(name=act) if isinstance(act, str) else act
            for act in self.bot.status_changer.activities
        ]

        if self.bot.status_changer.shuffle:
            random.shuffle(activities)

        self.activities = cycle(activities)

    @discord.ext.commands.Cog.listener()
    async def on_ready(self):
        if not self.change_activity.is_running():
            self.change_activity.change_interval(seconds=self.bot.status_changer.interval)
            self.change_activity.start()

    @tasks.loop()
    async def change_activity(self):
        """Replaces default variables and user variables in the activity name."""
        replace_values = {
            "guild_count": f"{len(self.bot.guilds):,}",
            "user_count": f"{len(self.bot.users):,}",
        }

        act = next(self.activities)

        for var, replace_value in replace_values.items():
            act.name = act.name.replace("{" + var + "}", str(replace_value))

        for key, value in self.bot.status_changer.kwargs.items():
            if inspect.iscoroutinefunction(value):
                replace_value = await value()
            elif callable(value):
                replace_value = value()
            else:
                replace_value = value

            act.name = act.name.replace("{" + str(key) + "}", str(replace_value))

        # Not sure why this is needed, but it is.
        if act.type == discord.ActivityType.custom:
            act = discord.CustomActivity(name=act.name)

        await self.bot.change_presence(activity=act, status=self.bot.status_changer.status)
