import asyncio
import random
import re
from datetime import datetime
import requests
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import variables
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from db.db_create import DbInsert, DBSelect, DBcheck
from settings.browser_settings import options
from variables import database_variables
from variables.parser_variables import chrome_driver_path
from variables.database_variables import users_table, vacancy_links_table


class HH:

    def __init__(self, **kwargs):
        self.post_vacancy = kwargs['post_vacancy'] if kwargs.get('post_vacancy') else None
        self.bot_dict = kwargs['bot_dict'] if 'bot_dict' in kwargs else None
        self.words_pattern = ""
        self.options = None
        self.page = None
        self.page_number = 1
        self.current_message = None
        self.msg = None
        if self.bot_dict:
            self.bot = self.bot_dict['bot']
            self.chat_id = self.bot_dict['chat_id']
        else:
            self.bot = None
        self.browser = None
        self.count_message_in_one_channel = 1
        self.found_by_link = 0
        self.response = {}
        self.list_links = []
        self.vacancies = []
        self.main_class = kwargs['main_class']
        self.vacancies_counter = 0
        self.base_url = "https://hh.ru"
        self.additional = "/search/vacancy?search_field=name&enable_snippets=true&ored_clusters=true&search_period=3&text=**word&page=**page"
        self.debug = False
        self.links_x_path = "//*[@data-page-analytics-event='vacancy_search_suitable_item']/a"
        self.source_title_name = "HH"
        self.searching_text_separator = None
        self.links_in_past = []

    async def get_content(self, *args, **kwargs):
        self.words_pattern = kwargs['words_pattern']
        self.db_tables = kwargs['db_tables'] if kwargs.get('db_tables') else database_variables.vacancies_table
        try:

            await self.get_info()
        except Exception as ex:
            print(f"Error: {ex}")
            if self.bot:
                await self.bot.send_message(self.chat_id, f"Error: {ex}")

        self.browser.quit()

    async def get_browser(self):
        try:
            self.browser = webdriver.Chrome(
                executable_path=chrome_driver_path,
                options=options
            )
        except:
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    async def get_info(self, how_much_pages=10, separator="+"):
        separator = separator if not self.searching_text_separator else self.searching_text_separator
        await self.get_browser()

        self.words_pattern = [self.words_pattern] if type(self.words_pattern) is str else self.words_pattern
        for word in self.words_pattern:
            self.word = separator.join(word.split(" "))

            # not remote
            for self.page_number in range(0, how_much_pages - 1):
                url = f'{self.base_url}{self.additional.replace("**word", self.word).replace("**page", str(self.page_number))}'
                if self.debug:
                    await self.main_class.bot.send_message(self.chat_id, f"Url: {url}", disable_web_page_preview=True)
                self.browser.get(url)
                await asyncio.sleep(2)
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                vacancy_exists_on_page = await self.get_link_message(self.browser.page_source)
                if not vacancy_exists_on_page:
                    break
        if self.bot_dict:
            await self.bot.send_message(self.chat_id, f'{self.source_title_name} parsing: Done!', disable_web_page_preview=True)

    async def get_link_message(self, raw_content):
        links = self.browser.find_elements(By.XPATH, self.links_x_path)
        pass
        if not links:
            return False
        for link in links:
            self.list_links.append(link.get_attribute('href'))
        if self.list_links:
            await self.get_content_from_link()
            return True
        else:
            return False

    async def get_content_from_link(self):
        self.found_by_link = 0
        for link in self.list_links:
            try:
                vacancy_url = link.get('href')
            except:
                vacancy_url = link
            print('url', vacancy_url)
            if not DBcheck().exists(table=vacancy_links_table, link=link) and link not in self.links_in_past:
                self.links_in_past.append(vacancy_url)
                await self.get_vacancy_data(vacancy_url)
            else:
                print("Link exists")

    async def get_vacancy_data(self, vacancy_url):
        self.browser.get(vacancy_url)
        soup = BeautifulSoup(self.browser.page_source, 'lxml')
        vacancy = ''
        try:
            vacancy = self.browser.find_elements(By.XPATH, "//div[@class='vacancy-title']")[0]
            vacancy = vacancy.text.split("\n")[0]
        except Exception as e:
            print(f"error vacancy: {e}")

        if vacancy:
            title = ''
            try:
                title = vacancy
            except Exception as e:
                print(f"error title: {e}")

            body = ''
            try:
                body = soup.find('div', class_='vacancy-section').get_text()
                body = body.replace('\n\n', '\n')
                body = re.sub(r'\<[A-Za-z\/=\"\-\>\s\._\<]{1,}\>', " ", body)
            except Exception as e:
                print(f"error body: {e}")

            tags = ''
            try:
                tags_list = soup.find('div', class_="bloko-tag-list")
                for i in tags_list:
                    tags += f'{i.get_text()}, '
                tags = tags[0:-2]
            except Exception as e:
                print(f"error tags: {e}")

            english = ''
            if re.findall(r'[Аа]нглийский', tags) or re.findall(r'[Ee]nglish', tags):
                english = 'English'

            try:
                company = soup.find('span', class_='vacancy-company-name').get_text()
                company = company.replace('\xa0', ' ')
            except Exception as e:
                print(f"error company: {e}")
                company = ''

            try:
                salary = soup.find('div', attrs={'data-qa': 'vacancy-salary'}).get_text()
            except Exception as e:
                print(f"error salary: {e}")
                salary = ''

            try:
                experience = soup.find('p', class_='vacancy-description-list-item').find('span').get_text()
            except Exception as e:
                print(f"error experience: {e}")
                experience = ''

            raw_content_2 = soup.findAll('p', class_='vacancy-description-list-item')
            counter = 1
            job_type = ''
            for value in raw_content_2:
                match counter:
                    case 1:
                        experience = value.find('span').get_text()
                    case 2:
                        job_type = str(value.get_text())
                    case 3:
                        job_type += f'\n{value.get_text}'
                counter += 1
            job_type = re.sub(r'\<[a-zA-Z\s\.\-\'"=!\<_\/]+\>', " ", job_type)

            contacts = ''

            try:
                date = soup.find('p', class_="vacancy-creation-time-redesigned").get_text()
            except Exception as e:
                print(f"error date: {e}")
                date = ''
            if date:
                date = re.findall(r'[0-9]{1,2}\W[а-я]{3,}\W[0-9]{4}', date)
                date = date[0]
                date = self.normalize_date(date)

            # ------------------------- search relocation ----------------------------
            relocation = ''
            if re.findall(r'[Рр]елокация', body):
                relocation = 'релокация'

            # ------------------------- search city ----------------------------
            try:
                city = soup.find('a', class_='bloko-link bloko-link_kind-tertiary bloko-link_disable-visited').text
            except:
                try:
                    city = self.browser.find_elements(By.XPATH, "//p[@data-qa='vacancy-view-location']")[0].text
                except:
                    city = ''

            results_dict = {
                'chat_name': 'https://hh.ru/',
                'title': title,
                'body': body,
                'vacancy': vacancy,
                'vacancy_url': vacancy_url,
                'company': company,
                'company_link': '',
                'english': english,
                'relocation': relocation,
                'job_type': job_type,
                'city':city,
                'salary':salary,
                'experience':experience,
                'time_of_public':date,
                'contacts':contacts,
            }
            await self.collect_vacancy_message(results_dict)
        else:
            print("vacancy not found")

    async def collect_vacancy_message(self, results_dict):
        vacancy_text = f"{self.source_title_name}\n"
        for key in ['vacancy', 'time_of_public', 'salary', 'company', 'experience', 'city', 'job_type', 'english', 'relocation', 'contacts']:
            match key:
                case 'body': results_dict[key] = await self.clear(results_dict[key])
                case 'vacancy':
                    self.vacancies_counter += 1
                    results_dict[key] = f"{self.vacancies_counter}. {results_dict[key]}"
            if results_dict[key]:
                vacancy_text += f"{key} {results_dict[key]}\n" if key not in ['vacancy', 'body', 'job_type', 'time_of_public'] else  f"{results_dict[key]}\n"

        await self.send_vacancy(vacancy_text[:4096], results_dict)

    async def send_vacancy(self, vacancy_text, results_dict):
        data = {
            "link": results_dict['vacancy_url'],
            "seen": True,
            "telegram_user_id": self.main_class.message.chat.id,
            "source_from": self.source_title_name,
        }
        db = DbInsert()
        link_id = db.insert_into(table=database_variables.vacancy_links_table, data=data)
        url = results_dict['vacancy_url']
        if self.post_vacancy:
            response = requests.post(self.post_vacancy, json=results_dict)
        if self.main_class.bot:
            self.main_class.message_counter += 1
            markup = InlineKeyboardBuilder()
            view = InlineKeyboardButton(text="view", url=url)
            reject = InlineKeyboardButton(text="reject", callback_data=f'reject|{self.main_class.message_counter}|{link_id}')
            applied = InlineKeyboardButton(text="I applied", callback_data=f'applied|{self.main_class.message_counter}|{link_id}')
            markup.row(view, reject, applied)
            inline_keyboard = [[button] for button in markup.buttons]
            markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
            self.main_class.message_list[self.main_class.message_counter] = (await self.bot.send_message(chat_id=self.chat_id, text=vacancy_text, reply_markup=markup, disable_web_page_preview=True))
            # data = {"message_id": self.main_class.message_counter, "message": self.main_class.message_list[self.main_class.message_counter]}
            # response = DbInsert().insert_into(table=database_variables.message_list_cash_table, data=data, blob="message")
            # pass
            await asyncio.sleep(random.randrange(1, 4))

    async def clear(self, text):
        return re.sub(r"[\n\n]{2,}", "", text)

    def normalize_date(self, date):
        convert = {
            'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12',
        }

        date = date.split(f'\xa0')
        month = date[1]
        day = date[0]
        year = date[2]
        date = datetime(int(year), int(convert[month]), int(day), 12, 00, 00)
        return date




