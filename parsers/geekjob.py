import re
from selenium.webdriver.common.by import By
from parsers.hh import HH

class Geek(HH):

    g_link = "https://geekjob.ru/vacancies?qs=python%20developer"

    async def get_content(self, *args, **kwargs):
        self.base_url = "https://geekjob.ru"
        self.additional = "/vacancies?sort=1&qs=**word"
        self.source_title_name = "GEEK"
        self.searching_text_separator = "%20"
        await super().get_content(*args, **kwargs)

    async def get_link_message(self, raw_content):
        self.links_x_path = "//li[@class='collection-item avatar']/a"
        await super().get_link_message(raw_content)

    async def get_vacancy_data(self, vacancy_url):
        vacancy_x_path = "//*[@id='body']/section/article[1]/section/header/h1"
        body_x_path = "//div[@id='vacancy-description']"
        company_x_path = "//h5[@class='company-name']/a"
        time_job_x_path = "//div[@class='time']"
        salary_x_path = "//span[@class='salary']"
        experience_x_path = ""
        job_type_x_path = "//span[@class='jobformat']"
        level_x_path = "//div[@class='category']"
        tags_x_path = "//div[@class='tags']"
        city_x_path = "//div[@class='location']"
        try:
            vacancy = self.browser.find_element(By.XPATH, vacancy_x_path).text
        except:
            vacancy = ''

        if vacancy:
            title = vacancy

            try:
                body = self.browser.find_element(By.XPATH, body_x_path).text
            except:
                body = ''
            # get tags --------------------------
            try:
                level = self.browser.find_element(By.XPATH, level_x_path).text
                if level:
                    body = f"Grade: {level}\n{body}"
            except:
                level = ''

            tags = ''
            try:
                tags = self.browser.find_element(By.XPATH, tags_x_path).text
                body = tags + "\n" + body
            except:
                pass
            english = ''
            if re.findall(r'[Аа]нглийский', tags) or re.findall(r'[Ee]nglish', tags):
                english = 'English'

            # get city --------------------------
            try:
                city = self.browser.find_element(By.XPATH, city_x_path).text
            except:
                city = ''
            # get company --------------------------
            try:
                company = self.browser.find_element(By.XPATH, company_x_path).text
            except:
                company = ''

            # get salary --------------------------
            try:
                salary = self.browser.find_element(By.XPATH, salary_x_path).text
            except:
                salary = ''

            # get experience --------------------------
            try:
                job_format = self.browser.find_element(By.XPATH, job_type_x_path).text
            except:
                job_format = ''

            contacts = ''

            try:
                date = self.browser.find_element(By.XPATH, time_job_x_path).text
            except:
                date = ''
            # if date:
            #     date = self.normalize_date(date)

            # ------------------------- search relocation ----------------------------
            relocation = ''
            if re.findall(r'[Рр]елокация', body):
                relocation = 'релокация'

            #-------------------- compose one writting for ione vacancy ----------------

            results_dict = {
                'chat_name': 'https://geekjob.ru/',
                'title': title,
                'body': body,
                'vacancy': vacancy,
                'vacancy_url': vacancy_url,
                'company': company,
                'company_link': '',
                'english': english,
                'relocation': relocation,
                'job_type': job_format,
                'city':city,
                'salary':salary,
                'experience': '',
                'time_of_public':date,
                'contacts':contacts,
            }
            await self.collect_vacancy_message(results_dict)
