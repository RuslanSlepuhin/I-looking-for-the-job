import re
from datetime import datetime

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from parsers.hh import HH

junior_link = 'https://jobs.devby.io/?filter[levels][]=intern&filter[levels][]=junior'
link_search = 'https://jobs.devby.io/?&filter[search]=project%20manager'

class Dev(HH):

    async def get_content(self, *args, **kwargs):
        self.base_url = "https://jobs.devby.io"
        self.additional = "/?&filter[search]=**word"
        self.source_title_name = "DEV"
        await super().get_content(*args, **kwargs)


    async def get_link_message(self, raw_content):
        self.links_x_path = "//*[@class='vacancies-list-item__position']/a"
        await super().get_link_message(raw_content)


    async def get_vacancy_data(self, vacancy_url):
        try:
            self.browser.get(vacancy_url)
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
        except Exception as ex:
            print(f"error in browser.get {ex}")

        # get vacancy ------------------------
        vacancy = ''
        try:
            vacancy = soup.find('div', class_='vacancy__header__name').get_text().replace('Вакансия ', '')
        except Exception as e:
            pass

        # get title --------------------------
        title = vacancy
        # get body --------------------------
        body = ''
        body_content = soup.find('div', class_='vacancy__body').find('div', class_='text')
        structure = await self.get_structure_advance(body_content)
        body_content_list_p = body_content.find_all('strong')
        body_content_list_ul = body_content.find_all('ul')
        for element in structure:
            if element == 'p':
                try:
                    temp = body_content_list_p[0].get_text()
                    body += f"\n{temp}\n"
                    body_content_list_p.pop(0)
                except:
                    break
            if element == 'ul':
                if body_content_list_ul:
                    temp = body_content_list_ul[0]
                    for li in temp:
                        if li.text != ' ' and li != '\n' and li.text:
                            try:
                                body += f"-{li.get_text().strip()}\n"
                            except:
                                break
                    body_content_list_ul.pop(0)

        # get tags --------------------------
        tags_list = []
        tags = ''
        try:
            tags_list = soup.find_all('div', class_="vacancy__tags__item")
            for i in tags_list:
                tags += f"#{i.get_text().replace(' ', '')} "
            tags = tags[0:-1]
        except:
            pass

        body = f"{body}\n{tags}"

        tags = ''
        try:
            tags_list = soup.find_all('div', class_='vacancy__info-block__item')
        except Exception as e:
            pass
        if tags_list and type(tags_list) is list:
            for element in tags_list:
                tags += f'{element.get_text()}, '
            tags = tags[:-2]

        level = re.findall(r'Уровень: [a-zA-Zа-яА-Я]+', tags)
        if level:
            level = level[0].replace('Уровень:', '').strip()
        else:
            level = ''
        body += f" #{level}"

        english = re.findall(r'Уровень английского: [a-zA-Zа-яА-Я0-9\s]+', tags)
        if english:
            english = english[0].replace('Уровень английского:', '').strip()
        else:
            english = ''

        # get city --------------------------

        try:
            city = self.browser.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div/div/div/div[1]/div[3]/div/div[2]/div[1]/strong')
            city = city.text
        except Exception as ex:
            city = ''

        # get company --------------------------
        try:
            company = soup.find('div', class_='vacancy__footer__company-name').get_text()
        except:
            company = ''

        # get salary --------------------------
        try:
            salary = soup.find('span', class_='bloko-header-section-2 bloko-header-section-2_lite').get_text()
        except:
            salary = ''

        # get experience --------------------------
        experience = ''
        try:
            experience = re.findall(r'Опыт: [a-zA-Zа-яА-Я0-9\s]+', tags)
        except Exception as e:
            pass
        if experience:
            experience = experience[0].replace('Опыт:', '').strip()
        else:
            experience = ''

        remote = ''
        try:
            remote = re.findall(r'Возможна удалённая работа: [a-zA-Z\sа-яА-Я0-9]+', tags)
        except Exception as e:
            pass
        if remote:
            remote = remote[0].replace('Возможна удалённая работа:', '').strip()
        else:
            remote = ''

        full_time = ''
        try:
            full_time = re.findall(r'Режим работы: [a-zA-Zа-яА-Я0-9\s]+', tags)
        except Exception as e:
            pass
        if full_time:
            full_time = full_time[0].replace('Режим работы:', '').strip()
        else:
            full_time = ''

        job_type = ''
        if remote:
            job_type += f"Удаленный формат: {remote}\n"
        if full_time:
            job_type += f"График работы: {full_time}"

        contacts = ''
        salary = ''

        date = datetime.now()

        # ------------------------- search relocation ----------------------------
        relocation = ''
        if re.findall(r'[Рр]елокация', body):
            relocation = 'релокация'


        #-------------------- compose one writting for ione vacancy ----------------
        results_dict = {
            'chat_name': 'https://dev.by',
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
            'experience':'',
            'time_of_public':date,
            'contacts':contacts,
        }
        await self.collect_vacancy_message(results_dict)

    def clean_company_name(self, text):
        text = re.sub('Прямой работодатель', '', text)
        text = re.sub(r'[(]{1} [a-zA-Z0-9\W\.]{1,30} [)]{1}', '', text)
        text = re.sub(r'Аккаунт зарегистрирован с (публичной почты|email) \*@[a-z.]*[, не email компании!]{0,1}', '', text)
        text = text.replace(f'\n', '')
        return text


    async def get_structure_advance(self, text):
        text = str(text)
        structure_list = []
        index_p = 1
        index_li = 1
        while index_p >0:
            index_li = text.find('<ul>')
            index_p = text.find('<strong>')
            if index_p < index_li and index_p != -1:
                structure_list.append('p')
                text = text[index_p + 2:]
            else:
                if index_li != -1:
                    structure_list.append('ul')
                    text = text[index_li + 2:]
                else:
                    structure_list.append('p')
                    text = text[index_p + 2:]
        while index_li > 0:
            index_li = text.find('<ul>')
            if index_li >0:
                structure_list.append('ul')
                text = text[index_li + 2:]
        return structure_list
