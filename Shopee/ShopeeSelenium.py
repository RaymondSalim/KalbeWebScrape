import platform
import json
import csv
import os
import HandleResult as uts
import urllib.parse as parse
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Shopee:
    id = 'shopee'
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
            self.output_dir = self.current_dir.replace('/Shopee', '/Output/')
            self.current_dir = self.current_dir.replace('/Shopee', '/Files/chromedriver-linux')
        elif str(self.operating_system) == 'Windows':
            self.output_dir = self.current_dir.replace('\\Shopee', '\\Output\\')
            self.current_dir = self.current_dir.replace('\\Shopee', '\\Files\\chromedriver-win.exe')

    def clear_console(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def start_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = True
        chrome_options.add_argument('--log-level=3')
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

        final_url = "https://shopee.co.id/search?page=0&keyword=" + self.keyword

        driver = self.start_driver()

        driver.get(final_url)

        page = 1

        while page <= self.page_limit:
            print(f"Page {page}")
            try:
                self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="row shopee-search-item-result__items"]')))
                # driver.execute_script("window.scrollTo(0, 99999);")

            except:
                continue

            search_results = driver.find_element_by_css_selector('div[class="row shopee-search-item-result__items"]')
            elems = search_results.find_elements_by_css_selector('div.shopee-search-item-result__item')

            for item in elems:
                try:
                    new_link = item.find_element_by_tag_name('a').get_attribute('href')
                    self.open_new_tab(new_link, driver)
                    # driver.execute_script('window.scrollBy(0,100);')
                except Exception as err:
                    print(err)
                    continue

            page += 1

            try:
                driver.implicitly_wait(3)
                nextbtn = driver.find_element_by_css_selector('button[class="shopee-button-outline shopee-mini-page-controller__next-btn"')
                if nextbtn.is_enabled():
                    nextbtn.click()
                    self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div.shopee-search-item-result__item')), f'Items not found in page {page}')

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

        self.scrape_page(driver)


        driver.execute_script("window.close();")
        handle = driver.window_handles
        driver.switch_to.window(handle[0])

    def scrape_page(self, driver):
        try:
            self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div.page-product'), ""), "Page product not found")
            self.wait.until(ec.text_to_be_present_in_element((By.CLASS_NAME, 'qaNIZv'), ""))

        except Exception as err:
            print(err)
            print("Timed out, skipping")
            self.errors.append(driver.current_url)

        valid = driver.find_elements_by_css_selector('div[class="product-not-exist__content"]')

        if len(valid) == 0:
            try:
                driver.implicitly_wait(0)
                d = dict()

                d['PRODUK'] = ""
                d['FARMASI'] = ""
                d['E-COMMERCE'] = 'SHOPEE'

                self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div._3Lybjn')))
                d['TOKO'] = driver.find_element_by_css_selector('div._3Lybjn').text
                # d['shop_name'] = driver.find_element_by_class_name('_3Lybjn').text

                locations = driver.find_elements_by_css_selector('div[class="kIo6pj"]')[-1].text
                d['ALAMAT'] = locations.replace("Dikirim Dari", "") if "Dikirim Dari" in locations else "International"

                d['KOTA'] = ""

                d['BOX']= ""

                sold_count_val = driver.find_elements_by_css_selector('div[class="_22sp0A"]')
                if len(sold_count_val) > 0:
                    sol = sold_count_val[0].text
                    if 'RB' in sol:
                        sol = sol.replace('RB', '').replace(',', '').replace('+', '')
                        sol = int(sol) * 100
                    d['JUAL (UNIT TERKECIL)'] = int(sol)

                else:
                    d['JUAL (UNIT TERKECIL)'] = ""


                d['HARGA UNIT TERKECIL'] = int(((driver.find_element_by_css_selector('div[class="_3n5NQx"]').text.split() )[0] ).replace('.','').replace('Rp',''))

                d['VALUE'] = ""

                disc = driver.find_elements_by_css_selector('div[class="MITExd"]')
                if len(disc) > 0:
                    disc_float = (disc[0].text)[:(disc[0].text).index('%'):]
                    d['% DISC'] = float(disc_float)
                else:
                    d['% DISC'] = ""


                shop_cat = driver.find_elements_by_css_selector('div[class="_1oAxCI"]')
                if len(shop_cat) > 0:
                    cat = shop_cat[0].text
                    d['KATEGORI'] = cat if len(cat) > 0 else "Shopee Mall"

                else:
                    d['KATEGORI'] = ""

                d['SOURCE'] = driver.current_url


                self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="qaNIZv"]')))
                d['NAMA PRODUK E-COMMERCE'] = driver.find_element_by_css_selector('div[class="qaNIZv"]').text
                # d['name'] = driver.find_element_by_css_selector('div.qaNIZv').text

                rating_val = driver.find_elements_by_css_selector('div[class="_3Oj5_n _2z6cUg"]')
                d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating_val[0].text)*20 if len(rating_val) > 0 else ""

                rating_count_val = driver.find_elements_by_css_selector('div[class="_3Oj5_n"]')
                if len(rating_count_val) > 0:
                    rat = rating_count_val[0].text
                    if 'RB' in rat:
                        rat = rat.replace('RB', '').replace(',', '').replace('+', '')
                        rat = int(rat) * 1000
                    d['JML ULASAN'] = int(rat)

                else:
                    d['JML ULASAN'] = ""


                d['DILIHAT'] = ""

                d['DESKRIPSI'] = driver.find_element_by_css_selector('div[class="_2u0jt9"]').text

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