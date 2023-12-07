from ..status_changer import Activity


async def setup(bot):
    await bot.add_cog(Activity(bot))
