from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from parsers.hh import HH

class Сareerjet(HH):

    async def get_content(self, *args, **kwargs):
        self.base_url = "https://www.careerjet.by"
        self.additional = "/search/jobs?s=**word&l=Беларусь&radius=25"
        self.source_title_name = "CAREERJET"
        await super().get_content(*args, **kwargs)

    async def get_link_message(self, raw_content):
        self.links_x_path = "//*[@class='job clicky']/header/h2/a"
        await super().get_link_message(raw_content)

    async def get_content_from_link(self, return_raw_dictionary=False):

        links = []
        soup = None
        self.found_by_link = 0
        for vacancy_url in self.list_links:
            if vacancy_url not in self.links_in_past:
                self.links_in_past.append(vacancy_url)
                links.append(vacancy_url)
                try:
                    self.browser.get(vacancy_url)
                    soup = BeautifulSoup(self.browser.page_source, 'lxml')
                except Exception as ex:
                    found_vacancy = False
                    print(f"error in browser.get {ex}")

                try:
                    vacancy = soup.find("h1").text.strip()
                except AttributeError as ex:
                    vacancy = None
                    print(f"Exception occurred: {ex}")

                # get title --------------------------
                try:
                    title = soup.find("h1").text.strip()
                except (AttributeError, TypeError) as ex:
                    title = None
                    print(f"Exception occurred: {ex}")

                # get body --------------------------
                try:
                    body = soup.find("section", class_="content").text.strip()
                except AttributeError as ex:
                    body = None
                    print(f"Exception occurred: {ex}")

                # get city and job_format --------------
                try:
                    job_info = []
                    inner_div = soup.find('ul', class_='details')  # Находим блокf <div class="j-d-h__inner">

                    for li in inner_div.find_all('li'):
                        job_info.append(li.text.strip())
                    city =job_info[0]

                    try:
                        if job_info[1] == 'Полная занятость':
                            job_format = 'Полная занятость'
                        else:
                            job_format = ['Гибрид', 'Удалённо']
                    except:
                        if job_info[1] == 'Полная занятость':
                            job_format = 'Полная занятость'
                        else:
                            job_format = ['Гибрид', 'Удалённо']

                except AttributeError as ex:
                    job_format = None
                    city = None
                    print(f"AttributeError occurred: {ex}")
                if job_format:
                    if type(job_format) is list:
                        job_format = ", ".join(job_format)
                # get company -------------------------
                try:
                    company = soup.find("p", class_="company").text.strip()
                except AttributeError as ex:
                    company = None
                    print(f"Exception occurred: {ex}")

                # get salary --------------------------
                try:
                    salary = soup.find("span", class_="price").text.strip()
                except AttributeError as ex:
                    salary = None
                    print(f"AttributeError occurred: {ex}")

                # -------------------------public time ----------------------------

                time_of_public = None
                tags_ul = soup.find('ul', class_='tags')  # Находим блок <ul class="tags">

                if tags_ul:
                    span = tags_ul.find('span', class_='badge')
                    if span:
                        time_of_public = span.text.strip()
                if time_of_public:
                    time_of_public = self.normalize_date(time_of_public)
                print(time_of_public)

                # -------------------- compose one writting for ione vacancy ----------------

                results_dict = {
                    'chat_name': 'https://www.careerjet.by/',
                    'title': title,
                    'body': body,
                    'vacancy': vacancy,
                    'vacancy_url': vacancy_url,
                    'company': company,
                    'company_link': '',
                    'english': '',
                    'relocation': '',
                    'job_type': job_format,
                    'city': city,
                    'salary': salary,
                    'experience': '',
                    'time_of_public': time_of_public,
                    'contacts': '',
                }
                await self.collect_vacancy_message(results_dict)
            else:
                print("link in past")

    def normalize_date(self, date):
        date = date.split('.')[0]
        date = date.split(' ')
        number = date[0]
        period = date[1]
        time_of_public = None
        if period == 'д':
            time_of_public = datetime.now() - timedelta(days=int(number))
        elif period == 'ч':
            time_of_public = datetime.now() - timedelta(hours=int(number))
        elif period == 'мес':
            time_of_public = datetime.now() - timedelta(days=int(number)*30)
        else:
            print('date: ', date)
            pass
        return time_of_public
