import platform
import json
import os
import HandleResult as uts
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class Tokopedia:
    id = 'tokopedia'
    operating_system = platform.system()

    timeout_limit = 10  # Slower internet connection should have a higher value
    scraped_count = 0

    def __init__(self, urls=None, args=None, completed_url=None, continue_args=None):
        if urls is None:
            if completed_url is None:
                self.keyword = args.query
                self.page_limit = args.page
                self.result = args.result
                self.file_name = None
                self.completed_url = []
            else:
                self.page_limit = 99999
                self.keyword = continue_args['keyword']
                self.completed_url = completed_url
                self.result = continue_args['result']
                self.file_name = continue_args['filename'].replace('.csv', '_continued.csv').replace('.json', '_continued.json')
        else:
            self.url = urls

        self.data = []
        self.errors = []
        self.current_dir = str(os.path.dirname(os.path.realpath(__file__)))

        if str(self.operating_system) == 'Linux':
            self.output_dir = self.current_dir.replace('/Tokopedia', '/Output/')
            self.current_dir = self.current_dir.replace('/Tokopedia', '/Files/chromedriver-linux')
        elif str(self.operating_system) == 'Windows':
            self.output_dir = self.current_dir.replace('\\Tokopedia', '\\Output\\')
            self.current_dir = self.current_dir.replace('\\Tokopedia', '\\Files\\chromedriver-win.exe')

    def clear_console(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def start_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = True
        chrome_options.add_argument('--log-level=3')
        # chrome_options.add_argument('--window-size=800,1600')
        chrome_options.add_argument('--window-size=1080,3840')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0')
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })  # Prevents annoying "Show notifications" request
        driver = webdriver.Chrome(self.current_dir, options=chrome_options)

        self.wait = WebDriverWait(driver, self.timeout_limit)

        return driver

    def scrape_search_results(self):
        self.clear_console()
        print("Start")

        start_time = datetime.now()

        final_url = "https://www.tokopedia.com/search?page=1&q=" + self.keyword

        driver = self.start_driver()

        driver.get(final_url)

        if self.page_limit == 0:
            self.page_limit = 99999

        page = 1

        while page <= self.page_limit:
            print(f"Page {page}")
            search_results = driver.find_element_by_css_selector('div[data-testid="divSRPContentProducts"]')
            elems = search_results.find_elements_by_class_name('pcv3__info-content')

            for items in elems:
                try:
                    new_link = items.get_attribute("href")

                    self.open_new_tab(new_link, driver)

                except Exception as err:
                    print(err)
                    continue

            page += 1

            try:
                driver.implicitly_wait(3)
                # driver.find_element_by_xpath('//button[@aria-label="Halaman berikutnya"]').click()
                nxtbtn = driver.find_element_by_css_selector('button[aria-label="Halaman berikutnya"]')
                if nxtbtn.is_enabled():
                    nxtbtn.click()
                    self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'pcv3__info-content')),
                               'Items not found in page {}'.format(page))

                else:
                    break

            except TimeoutException as err:
                print(err)
                break

            except NoSuchElementException:
                break

        driver.quit()

        self.handle_data(start_time)

    def open_new_tab(self, new_url, driver):
        # Opens a new tab
        driver.execute_script("window.open('');")

        # Gets a list of open tabs
        handle = driver.window_handles

        # Change focus to new tab
        driver.switch_to.window(handle[-1])
        driver.get(new_url)

        # Waits for redirects
        try:
            self.wait.until_not(ec.url_contains("ta.tokopedia"))
            if any(completed in driver.current_url for completed in self.completed_url):
                print("Item skipped")
                driver.execute_script("window.close();")
                handle = driver.window_handles
                driver.switch_to.window(handle[0])
                return
        except:
            # Closes and switch focus to the main tab
            driver.execute_script("window.close();")
            handle = driver.window_handles
            driver.switch_to.window(handle[0])

            print("redir timeout")
            return

        else:
            self.scrape_page(driver)

        finally:
            # Closes and switch focus to the main tab
            driver.execute_script("window.close();")
            handle = driver.window_handles
            driver.switch_to.window(handle[0])

    def scrape_page(self, driver):
        try:
            self.wait.until(
                # ec.text_to_be_present_in_element((By.XPATH, '//div[@data-testid="pdpDescriptionContainer"]'), ""),
                # "pdpDescriptionContainer not found")
                ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div[data-testid="pdpDescriptionContainer"]'), ""),
                "pdpDescriptionContainer not found")
        except Exception as err:
            print(err)
            print("timed out, skipping")
            self.errors.append(driver.current_url)
        else:
            valid = driver.find_elements_by_css_selector(
                'h1[class="css-6hac5w-unf-heading e1qvo2ff1"]')  # Required to check if product page is valid

            if len(valid) == 0:
                try:
                    driver.implicitly_wait(0)
                    d = dict()

                    d['KEYWORD'] = self.keyword


                    d['PRODUK'] = ""
                    d['FARMASI'] = ""
                    d['E-COMMERCE'] = 'TOKOPEDIA'

                    self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'a[data-testid="llbPDPFooterShopName"]'), ""))
                    d['TOKO'] = driver.find_element_by_css_selector('a[data-testid="llbPDPFooterShopName"]').text
                    driver.implicitly_wait(0)

                    d['ALAMAT'] = ""

                    location = driver.find_element_by_css_selector('span[data-testid="lblPDPFooterLastOnline"]').text
                    d['KOTA'] = location.split('•')[0]

                    d['BOX'] = ""

                    sold_count_valid = driver.find_elements_by_css_selector(
                        'span[data-testid="lblPDPDetailProductSuccessRate"]')
                    sold_count = sold_count_valid[0].text if len(sold_count_valid) > 0 else ""
                    sold_count = sold_count[8:len(sold_count) - 7:].replace(',','').replace('.', '')
                    if "rb" in sold_count:
                        sold_count = sold_count.replace('rb', '')
                        sold_count = int(sold_count) * 100
                    d['JUAL (UNIT TERKECIL)'] = int(sold_count) if len(sold_count_valid) > 0 else ""

                    price = driver.find_element_by_css_selector('h3[data-testid="lblPDPDetailProductPrice"]').text
                    d['HARGA UNIT TERKECIL'] = int((price[2::]).replace(".", ""))

                    d['VALUE'] = ""

                    discount = driver.find_elements_by_css_selector('div[lblPDPDetailDiscountPercentage]')
                    d['% DISC'] = float(discount[0].text)/100 if len(discount) > 0 else ""

                    shop_category = driver.find_elements_by_css_selector('p[data-testid="imgPDPDetailShopBadge"]')
                    d['KATEGORI'] = shop_category[0].text if len(shop_category) > 0 else ""

                    d['SOURCE'] = driver.current_url

                    d['NAMA PRODUK E-COMMERCE'] = driver.find_element_by_css_selector('h1[data-testid="lblPDPDetailProductName"]').text

                    rating = driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailProductRatingNumber"]')
                    d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating[0].text)*20 if len(rating) > 0 else ""

                    rating_total = driver.find_elements_by_css_selector(
                        'span[data-testid="lblPDPDetailProductRatingCounter"]')
                    rating_total = rating_total[0].text.replace('(','').replace(')', '').replace(',','').replace('.', '') if len(rating_total) > 0 else ""
                    if "rb" in rating_total:
                        rating_total = rating_total.replace('rb','')
                        rating_total = int(rating_total) * 100

                    d['JML ULASAN'] = int(rating_total) if len(rating_total) > 0 else ""

                    seen_by = (
                        driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailProductSeenCounter"]'))
                    seen_by = seen_by[0].text[:seen_by[0].text.index("x"):].replace('(','').replace(')', '').replace(',','').replace('.', '')
                    if "rb" in seen_by:
                        seen_by = seen_by.replace('rb', '')
                        seen_by = int(seen_by) * 100

                    d['DILIHAT'] = int(seen_by)

                    d['DESKRIPSI'] = driver.find_element_by_css_selector(
                        'div[data-testid="pdpDescriptionContainer"]').text

                    d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                except WebDriverException as err:
                    print(err)
                    self.errors.append(driver.current_url)

                except Exception as err:
                    print(err)
                    self.errors.append(driver.current_url)

                else:
                    self.data.append(d)
                    self.scraped_count += 1
                    print(f"    Item #{self.scraped_count} completed")

            else:
                self.errors.append(driver.current_url)

    def handle_data(self, start_time):
        print("Time taken: " + str(datetime.now() - start_time))

        if self.file_name is None:
            self.file_name = f"{self.output_dir}tokopedia_{str(datetime.now()).replace(':', '꞉')}.json"

        else:
            self.file_name = f"{self.output_dir}{self.file_name}"

        handle_data = uts.HandleResult(data=self.data, launched_from_start=False, file_name=self.file_name, choice=self.result)
        handle_data.update()

        if len(self.errors) > 0:
            with open(self.file_name.replace('.json', '_errors.json'), 'w') as errorFile:
                json.dump(self.errors, errorFile)

    def scrape_errors(self):
        driver = self.start_driver()

        start_time = datetime.now()

        for u in self.url:
            driver.get(u)
            self.scrape_page(driver)

        driver.quit()

        self.handle_data(start_time)
