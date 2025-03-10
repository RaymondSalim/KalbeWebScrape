import json
import os
import platform
import HandleResult as uts
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Bukalapak:
    id = 'bukalapak'
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
            self.output_dir = self.current_dir.replace('/Bukalapak', '/Output/')
            self.current_dir = self.current_dir.replace('/Bukalapak', '/Files/chromedriver-linux')
        elif str(self.operating_system) == 'Windows':
            self.output_dir = self.current_dir.replace('\\Bukalapak', '\\Output\\')
            self.current_dir = self.current_dir.replace('\\Bukalapak', '\\Files\\chromedriver-win.exe')

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

        final_url = "https://www.bukalapak.com/products?page=1&search%5Bkeywords%5D=" + self.keyword

        driver = self.start_driver()

        driver.get(final_url)

        page = 1

        if self.page_limit == 0:
            self.page_limit = 99999

        attempt = 0
        while page <= self.page_limit:
            try:
                self.wait.until(ec.presence_of_element_located((By.XPATH, '//div[@class="bl-product-card__thumbnail"]//*//a')), "No items found on this page")
            except:
                # Retry one more time
                attempt += 1
                page -= 1
                if attempt > 1:
                    break
                else:
                    continue
            else:
                attempt = 0

                print(f"Page {page}")
                elems = driver.find_elements_by_css_selector('div[class="bl-product-card__description"]')

                for items in elems:
                    try:
                        temp_url = items.find_element_by_tag_name('a').get_attribute('href')
                        if any(completed in temp_url for completed in self.completed_url):
                            print("Item skipped")
                            continue

                        self.open_new_tab(temp_url, driver)

                    except Exception as err:
                        print(err)
                        continue

                page += 1


                try:
                    next_button = driver.find_element_by_css_selector("a[class*='pagination__next']")

                    if next_button.is_enabled():
                        print("Next page")
                        driver.implicitly_wait(0)
                        next_button.click()
                        # wait = WebDriverWait(driver, self.timeout_limit)
                        # wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'div[class="bl-product-card__wrapper"]')))
                    else:
                        break

                except TimeoutException as err:
                    print(err)
                    break

                except NoSuchElementException as err:
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

        # Closes and switch focus to the main tab
        driver.execute_script("window.close();")
        handle = driver.window_handles
        driver.switch_to.window(handle[0])

    def scrape_page(self, driver):
        try:
            self.wait.until(ec.presence_of_element_located((By.ID, 'section-informasi-barang')))

        except Exception as err:
            print(err)
            print("timed out, skipping")
            self.errors.append(driver.current_url)

        else:
            valid = driver.find_elements_by_css_selector('h1[class="u-fg--ash-light u-txt--bold"]')

            if len(valid) == 0:
                try:
                    driver.implicitly_wait(0)
                    d = dict()

                    d['KEYWORD'] = self.keyword

                    d['PRODUK'] = ""
                    d['FARMASI'] = ""
                    d['E-COMMERCE'] = 'BUKALAPAK'

                    shop = driver.find_element_by_class_name('c-seller__info')
                    d['TOKO'] = shop.find_element_by_css_selector('a[class="c-link--primary--black"]').text

                    d['ALAMAT'] = ""

                    location = driver.find_element_by_css_selector('a[class="c-seller__city u-mrgn-bottom--2"]').text
                    d['KOTA'] = location

                    d['BOX'] = ""


                    mpr = driver.find_element_by_class_name("c-main-product__reviews").text
                    mpr_arr = mpr.split()

                    ratingc = None
                    soldc = None

                    if len(mpr_arr) == 4:
                        ratingc = int(mpr_arr[0].replace('.',''))
                        soldc = int(mpr_arr[2].replace('.',''))

                    elif len(mpr_arr) == 2:
                        soldc = int(mpr_arr[0].replace('.',''))

                    d['JUAL (UNIT TERKECIL)'] = int(soldc) if len(mpr) > 0 else ""

                    price = driver.find_element_by_css_selector('div.c-main-product__price').text.split('\n')
                    d['HARGA UNIT TERKECIL'] = float((price[0][2::]).replace(".", ""))

                    d['VALUE'] = ""

                    discount = driver.find_elements_by_css_selector('span[class="c-main-product__price__discount-percentage"]')
                    if len(discount) > 0:
                        text_disc = discount[0].text.split()
                    d['% DISC'] = float(text_disc[-1].replace('%', ''))/100 if len(discount) > 0 else ""

                    shop_category = driver.find_element_by_css_selector('div[class="c-seller__badges"]').text
                    if shop_category.count("Seller") > 1:
                        shop_category = shop_category.replace("Seller", "Seller ")
                        d['KATEGORI'] = shop_category
                    else:
                        d['KATEGORI'] = ""

                    url = driver.current_url
                    if '?' in url:
                        url = url[:str(driver.current_url).index('?')]
                    d['SOURCE'] = url

                    d['NAMA PRODUK E-COMMERCE'] = driver.find_element_by_css_selector('h1[class="c-main-product__title u-txt--large"]').text

                    rating = driver.find_elements_by_css_selector('span[class="summary__score"]')
                    d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating[0].text) if len(rating) > 0 else ""

                    d['JML ULASAN'] = int(ratingc) if len(mpr_arr) == 4 else ""

                    d['DILIHAT'] = ""

                    d['DESKRIPSI'] = driver.find_element_by_css_selector(
                        'div[class="c-information__description-txt"]').text

                    d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            self.file_name = f"{self.output_dir}bukalapak_{str(datetime.now()).replace(':', '꞉')}.json"
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
