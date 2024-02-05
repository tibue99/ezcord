import ezcord

# It's recommended to use a JSON or YAML file for localizations
localizations = {
    "de": {
        "greet": {
            "name": "begrüßung",
            "description": "Begrüße einen User",
            "options": {
                "user": {
                    "description": "Der User, den du begrüßen möchtest.",
                }
            },
        },
        "example_group": {
            "group_greet": {
                "name": "gruppen_begrüßung",
                "description": "Begrüßung mit einer SlashCommandGroup",
            },
        },
    },
    "en-US": {
        "greet": {
            # The name can be omitted if it's the same as the default name
            "description": "Greet someone",
            "options": {
                "user": {
                    "name": "user",  # The line can be omitted, because "user" is the default name
                    "description": "The user you want to greet.",
                }
            },
        },
        "example_group": {
            "group_greet": {
                "description": "Greeting with a SlashCommandGroup",
            },
        },
    },
}


bot = ezcord.Bot()
bot.load_cogs()

bot.localize_commands(localizations)
bot.run()
