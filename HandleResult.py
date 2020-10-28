import csv
import os
import platform
import json


from Bukalapak import BLSelenium
from Shopee import ShopeeSelenium
from Tokopedia import TPSelenium


class HandleResult:
    data = []

    operating_system = platform.system()
    current_dir = str(os.path.dirname(os.path.realpath(__file__)))
    output_dir = ""

    if str(operating_system) == 'Linux':
        output_dir = current_dir + '/Output/'

    elif str(operating_system) == 'Windows':
        output_dir = current_dir + '\\Output\\'

    def __init__(self, data=None, launched_from_start=None, file_name="", choice=""):
        self.data = data
        self.launched_start = launched_from_start
        self.file_name = file_name
        self.choice = choice.lower()

    def update(self):

        if self.choice == "continue":
            url = [values['SOURCE'] for values in self.data]
            arg = {
                'keyword': self.data[0]['KEYWORD'],
                'result': "json" if "json" in self.file_name else "csv",
                'filename': self.file_name
            }

            if "tokopedia" in url[0]:
                process = TPSelenium.Tokopedia(continue_args=arg, completed_url=url)
                process.scrape_search_results()

            elif "bukalapak" in url[0]:
                process = BLSelenium.Bukalapak(continue_args=arg, completed_url=url)
                process.scrape_search_results()

            elif "shopee" in url[0]:
                process = ShopeeSelenium.Shopee(continue_args=arg, completed_url=url)
                process.scrape_search_results()

            filepath = self.current_dir + '/Output/' + self.file_name
            data = []

            if "csv" in filepath:
                print(filepath)
                with open(filepath, 'r') as openFile:
                    data = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                                 for row in csv.DictReader(openFile, skipinitialspace=True)]
                print(f"Length of data is {len(data)}")

                filepath = filepath.replace('_continued', '')

                print(filepath)
                with open(filepath, 'r') as openFile:
                    tempdata = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                            for row in csv.DictReader(openFile, skipinitialspace=True)]
                print(f"Length of tempdata is {len(tempdata)}")

                finaldata = data + tempdata
                print(f"Length of finaldata is {len(finaldata)}")

                print(f"Saving to {filepath}")
                # self.save_csv(filepath, finaldata)

            elif "json" in filepath:
                with open(filepath, 'r') as openFile:
                    data = json.load(openFile)

                filepath = filepath.replace('_continued', '')

                with open(filepath, 'r') as openFile:
                    tempdata = json.load(openFile)

                finaldata = data + tempdata
                print(f"Saving to {filepath}")
                self.save_json(filepath, finaldata)

        else:

            if not self.launched_start:
                if not os.path.exists(os.path.normpath(self.output_dir)):
                    os.mkdir(os.path.normpath(self.output_dir))
            else:
                self.file_name = self.current_dir + '/Output/' + self.file_name

            if self.choice == 'csv':
                path = self.file_name.replace('.json', '.csv')
                self.save_csv(path, self.data)

            if self.choice == 'json':
                path = self.file_name.replace('.csv', '.json')
                self.save_json(path, self.data)

    def save_csv(self, path, data):
        if len(data) > 0:
            keys = data[0].keys()
            print(f"Saving to {path}")
            try:
                with open(path, 'w', newline='', encoding='utf-8') as csvFile:
                    dict_writer = csv.DictWriter(csvFile, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(data)
            except:
                with open(path.replace('.csv', '.json'), 'w') as outFile:
                    json.dump(data, outFile)
        else:
            print("Nothing scraped")

    def save_json(self, path, data):
        if len(data) > 0:
            print(f"Saving to {path}")
            with open(path, 'w') as outFile:
                json.dump(data, outFile)
        else:
            print("Nothing scraped")
