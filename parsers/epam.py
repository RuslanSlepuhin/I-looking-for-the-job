import asyncio
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from parsers.hh import HH

class Epam(HH):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://anywhere.epam.com/en/jobs"
        self.additional = "?page=**page&search=**word"
        self.source_title_name = "EPAM"

    async def get_content(self, *args, **kwargs):
        await super().get_content(*args, **kwargs)

    async def get_link_message(self, raw_content):
        self.links_x_path = "//div[@class='AccordionSection_title__kMJBz JobCard_accordionTitle__D1KeP']/a"
        return await super().get_link_message(raw_content)

    async def get_vacancy_data(self, vacancy_url):
        vacancy_x_path = "//h1[@class='JobDetailsBanner_title___vzt6']"
        body_x_path = "//*[@class='AccordionSection_container__k_27D Description_accordionContainer__9fLdz AccordionSection_medium__ftu1I Description_medium__vb35_ AccordionSection_opened__oDOF_ AccordionSection_withDataAttributes__oqWOC']"
        body_additional = "//div[@class='TabsWithDropdown_container__IePag TabsWithDropdown_transparent__sPD5Q JobDetails_benefitsTabs__sLTjL']"
        stack_and_city_x_path = "//div[@class='IconBullet_list__XJREv UpperBar_list__h8X9X']/span"

        try:
            self.browser.get(vacancy_url)
            await asyncio.sleep(1)
        except Exception as ex:
            found_vacancy = False
            print(f"error in browser.get {ex}\nvacancy_url: {vacancy_url}")
        try:
            vacancy = self.browser.find_element(By.XPATH, vacancy_x_path).text.capitalize()
        except AttributeError as ex:
            vacancy = None
            print(f"Exception occurred: {ex}")

        if vacancy:
            title = vacancy
            body = ""
            try:
                body_list = self.browser.find_elements(By.XPATH, body_x_path)
                for i in body_list:
                    body += f"{i.text}\n\n"
            except AttributeError as ex:
                body = None
                print(f"Exception occurred: {ex}")

            try:
                body_list = self.browser.find_element(By.XPATH, body_additional).text
                body += body_list
            except:
                pass

            body_stack = "Stack: "
            city = ""
            try:
                body_list = self.browser.find_elements(By.XPATH, stack_and_city_x_path)
                for i in body_list:
                    if body_list.index(i)<len(body_list)-1:
                        body_stack += f"{i.text} "
                    else:
                        city = i.text
                body = f"{body_stack}\n{body}"
            except:
                pass

            english = ''
            experience = ''
            try:
                english_levels = ['A1+', 'A2+', 'B2+', 'B1+', 'C1+', 'C2+', 'Native', 'English']
                requirements = self.browser.find_elements(By.CLASS_NAME,
                                                    'AccordionSection_container__Lg5Z_.Description_accordionContainer__gHK8_.AccordionSection_medium___u5_2.Description_medium__sj6N2.AccordionSection_opened__eE0Qc')
                requirements = requirements[1].find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                for li in requirements:
                    if 'year' in li.text or 'years' in li.text:
                        experience = li.text
                    for level in english_levels:
                        if 'German' in li.text:
                            english = li.text
                        elif level in li.text:
                            english = level
                            break
            except:
                english = None

            # -------------------- compose one writting for ione vacancy ----------------
            results_dict = {
                    'chat_name': 'https://anywhere.epam.com',
                    'title': title,
                    'body': body,
                    'vacancy': vacancy,
                    'vacancy_url': vacancy_url,
                    'company': 'Epam',
                    'company_link': '',
                    'english': english,
                    'relocation': '',
                    'job_type': '',
                    'city': city,
                    'salary': '',
                    'experience': experience,
                    'time_of_public': '',
                    'contacts': '',
            }
            await self.collect_vacancy_message(results_dict)

    def normalize_date(self, date):
        convert = {
            'янв': '01',
            'фев': '02',
            'мар': '03',
            'апр': '04',
            'май': '05',
            'июн': '06',
            'июл': '07',
            'авг': '08',
            'сен': '09',
            'окт': '10',
            'ноя': '11',
            'дек': '12',
        }
        date = date.split(f' ')
        month = date[1]
        day = date[0]
        year = datetime.now().strftime('%Y')
        date = datetime(int(year), int(convert[month]), int(day), 12, 00, 00)
        return date

    def clean_company_name(self, text):
        text = re.sub('Прямой работодатель', '', text)
        text = re.sub(r'[(]{1} [a-zA-Z0-9\W\.]{1,30} [)]{1}', '', text)
        text = re.sub(r'Аккаунт зарегистрирован с (публичной почты|email) \*@[a-z.]*[, не email компании!]{0,1}', '',
                      text)
        text = text.replace(f'\n', '')
        return text
