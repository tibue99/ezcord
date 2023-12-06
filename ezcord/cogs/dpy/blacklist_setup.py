from ..blacklist import Blacklist


async def setup(bot):
    await bot.add_cog(Blacklist(bot))
