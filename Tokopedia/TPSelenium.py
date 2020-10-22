import platform
import json
import os
import HandleResult as uts
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Tokopedia:
    id = 'tokopedia'
    operating_system = platform.system()

    timeout_limit = 10  # Slower internet connection should have a higher value
    scraped_count = 0

    def __init__(self, keyword_in=None, page_lim=None, urls=None):
        if urls is None:
            self.keyword = keyword_in
            self.page_limit = page_lim
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

        page = 1

        while page <= self.page_limit:
            print(f"Page {page}")
            search_results = driver.find_element_by_css_selector('div[data-testid="divSRPContentProducts"]')
            elems = search_results.find_elements_by_class_name('pcv3__info-content')

            for items in elems:
                try:
                    new_link = items.get_attribute("href")
                    self.open_new_tab(new_link, driver)

                except:
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

                    d['PRODUK'] = ""
                    d['FARMASI'] = ""
                    d['E-COMMERCE'] = 'TOKOPEDIA'

                    self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'a[data-testid="llbPDPFooterShopName"]'), ""))
                    d['TOKO'] = driver.find_element_by_css_selector('a[data-testid="llbPDPFooterShopName"]').text
                    driver.implicitly_wait(0)

                    location = driver.find_element_by_css_selector('span[data-testid="lblPDPFooterLastOnline"]').text
                    d['ALAMAT'] = location.split('•')[0]

                    d['KOTA'] = ""

                    d['BOX'] = ""

                    sold_count_valid = driver.find_elements_by_css_selector(
                        'span[data-testid="lblPDPDetailProductSuccessRate"]')
                    sold_count = sold_count_valid[0].text if len(sold_count_valid) > 0 else ""
                    sold_count = sold_count[8:len(sold_count) - 7:].replace(".", "")
                    d['JUAL (UNIT TERKECIL)'] = int(sold_count) if (len(sold_count) > 0) else ""

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
                    d['JML ULASAN'] = int(rating_total[0].text[1:len(rating_total[0].text) - 1:]) if len(
                        rating_total) > 0 else ""

                    seen_by = (
                        driver.find_element_by_css_selector('span[data-testid="lblPDPDetailProductSeenCounter"]').text)
                    seen_by = seen_by[:seen_by.index("x"):]
                    if 'rb' in seen_by:
                        if ',' in seen_by:
                            seen_by = int(seen_by.replace(',', '').replace('rb', '')) * 100
                        else:
                            seen_by = int(seen_by.replace('rb', '')) * 1000
                    else:
                        seen_by = seen_by.replace('.', '')

                    d['DILIHAT'] = int(seen_by)

                    d['DESKRIPSI'] = driver.find_element_by_css_selector(
                        'div[data-testid="pdpDescriptionContainer"]').text

                    d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


                    self.data.append(d)
                    self.scraped_count += 1
                    print(f"    Item #{self.scraped_count} completed")

                except Exception as err:
                    print(err)
                    self.errors.append(driver.current_url)

            else:
                self.errors.append(driver.current_url)

    def handle_data(self, start_time):
        print("Time taken: " + str(datetime.now() - start_time))

        handle_data = uts.HandleResult(self.data, False, self.id)
        handle_data.update()

        if len(self.errors) > 0:
            file_name = f"{self.output_dir}tokopedia_{str(datetime.now()).replace(':', '꞉')}.json"
            with open(file_name.replace('.json', '_errors.json'), 'w') as errorFile:
                json.dump(self.errors, errorFile)

    def scrape_errors(self):
        driver = self.start_driver()

        start_time = datetime.now()

        for u in self.url:
            driver.get(u)
            self.scrape_page(driver)

        driver.quit()

        self.handle_data(start_time)