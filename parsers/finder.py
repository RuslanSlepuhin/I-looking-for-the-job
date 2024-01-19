import re
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By

from parsers.hh import HH


class Finder(HH):

    async def get_content(self, *args, **kwargs):
        self.base_url = "https://finder.work"
        self.additional = "/vacancies/**word?page=**page"
        self.source_title_name = "FINDER"
        self.searching_text_separator = "%20"
        await super().get_content(*args, **kwargs)

    async def get_link_message(self, raw_content):
        self.links_x_path = "//div[@class='vacancy-card__header']/a[1]"
        return await super().get_link_message(raw_content)

    async def get_vacancy_data(self, vacancy_url):
        vacancy_x_path = "//div[@class='vacancy-info-header']/h1"
        body_x_path = "//div[@class='vacancy-info-body__info']"
        company_x_path = "//div[@class='company__title']/a"
        time_job_x_path = "//div[@class='vacancy-info-header__publication-date']"
        salary_x_path = "//div[@class='row-wrapper vacancy-info-header__row']"
        experience_x_path = "//div[@class='vacancy-info-header__row']"

        try:
            vacancy = self.browser.find_element(By.XPATH, vacancy_x_path).text
        except:
            vacancy = ''
        if vacancy:
            title = vacancy
            body = ""
            try:
                body_list = self.browser.find_elements(By.XPATH, body_x_path)
                for i in body_list:
                    body += f"{i.text}\n"
            except:
                body = ''

            try:
                company = self.browser.find_element(By.XPATH, company_x_path).text
            except:
                company = ''

            try:
                time_job = self.browser.find_element(By.XPATH, time_job_x_path).text
            except:
                time_job = ''

            try:
                salary = self.browser.find_element(By.XPATH, salary_x_path).text
            except:
                salary = ''

            try:
                experience = self.browser.find_element(By.XPATH, experience_x_path).text
            except:
                experience = ''

            time_of_public = self.convert_date(time_job)

            results_dict = {
                'chat_name': 'https://hh.ru/',
                'title': title,
                'body': body,
                'vacancy': vacancy,
                'vacancy_url': vacancy_url,
                'company': company,
                'company_link': '',
                'english': "",
                'relocation': "",
                'job_type': "",
                'city': "",
                'salary':salary,
                'experience':experience,
                'time_of_public': time_of_public,
                'contacts': "",
            }
            await self.collect_vacancy_message(results_dict)

    def convert_date(self, date):
        date = date.split(' ')
        if date[1] == 'сегодня':
            date = datetime.now()
        elif date[1] == 'вчера':
            date  = datetime.now()-timedelta(days=1)
        elif date[1] == 'неделю':
            date = datetime.now()-timedelta(days=7)
        elif re.findall(r'д[е]{0,1}н[ьейя]{1,2}', date[2]):
            date = datetime.now()-timedelta(days=int(date[1]))
        elif re.findall(r'месяц[ева]{0,2}', date[2]):
            date = datetime.now() - timedelta(days=int(date[1]*30))
        return date


