import configparser

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import variables.database_variables
from db.db_create import DbInsert, DBSelect, DBcheck, DBPutPatch
from parsers.careerjet import Сareerjet
from parsers.dev import Dev
from parsers.epam import Epam
from parsers.finder import Finder
from parsers.geekjob import Geek
from parsers.hh import HH
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from parsers.hhkz import KZHH

config = configparser.ConfigParser()
config.read("settings/config.ini")
form_router = Router()

class BotInterface:
    def __init__(self, **kwargs):
        self.token = kwargs['token'] if kwargs.get('token') else config['bot']['token']
        self.bot = Bot(token=self.token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp.include_router(form_router)
        self.words_pattern = ""
        self.message_list = {}
        self.message_counter = 0
        self.message = None

    class WordsPatternForm(StatesGroup):
        words_pattern = State()

    async def handlers(self):
        @form_router.message(self.WordsPatternForm.words_pattern)
        async def process_name(message: types.Message, state: FSMContext) -> None:
            await state.update_data(name=message.text)
            self.words_pattern = message.text
            await self.vacancies_from(message)

        @self.dp.message(CommandStart())
        async def start(message: types.Message, state: FSMContext):
            self.message = message
            if not DBSelect().select_from(table=variables.database_variables.users_table, fields=("id", "telegram_user_id"), condition=f"telegram_user_id={message.chat.id}"):
                DbInsert().insert_into(table=variables.database_variables.users_table, data={"telegram_user_id": message.chat.id})
            await self.words_pattern_request(message, state)

        @self.dp.callback_query()
        async def callbacks(callback: types.CallbackQuery):
            if callback.data.split("|")[0] in ['reject', 'applied']:
                message_counter = None
                data = {}
                if 'reject' in callback.data:
                    message_counter = int(callback.data.split("|")[1])
                    data = {"rejected": True}
                if 'applied' in callback.data:
                    message_counter = int(callback.data.split("|")[1])
                    data = {"applied": True}
                if DBPutPatch().patch(table=variables.database_variables.vacancy_links_table, data=data, id=int(callback.data.split("|")[2])):
                    try:
                        await self.message_list[message_counter].delete()
                        self.message_list.pop(message_counter)
                    except Exception as ex:
                        print(ex)

        await self.dp.start_polling(self.bot)

    async def words_pattern_request(self, message, state: FSMContext):
        await state.set_state(self.WordsPatternForm.words_pattern)
        await self.bot.send_message(message.chat.id, "Input the words for vacancy searching")

    async def vacancies_from(self, message):
        hh = HH(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await hh.get_content(words_pattern=self.words_pattern)
        geek = Geek(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await geek.get_content(words_pattern=self.words_pattern)

        finder = Finder(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await finder.get_content(words_pattern=self.words_pattern)
        epam = Epam(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await epam.get_content(words_pattern=self.words_pattern)
        dev = Dev(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await dev.get_content(words_pattern=self.words_pattern)
        career = Сareerjet(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await career.get_content(words_pattern=self.words_pattern)
        hhkz = KZHH(main_class=self, bot_dict = {'bot': self.bot, "chat_id": message.chat.id})
        await hhkz.get_content(words_pattern=self.words_pattern)
