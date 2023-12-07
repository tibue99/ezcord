from ..status_changer import Activity


def setup(bot):
    bot.add_cog(Activity(bot))
