import asyncio
from bot_view.bot_handlers import BotInterface
from db.db_create import DbCreate

if __name__ == "__main__":
    print(DbCreate().create_db_architecture())
    bot = BotInterface()
    asyncio.run(bot.handlers())