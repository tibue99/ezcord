from ..blacklist import Blacklist


def setup(bot):
    bot.add_cog(Blacklist(bot))
