import csv
import json
import os
import platform
import HandleResult as uts
from Tokopedia import  TPSelenium
from Shopee import ShopeeSelenium
from Bukalapak import BLSelenium

class LoadFromFile:
    current_dir = str(os.path.dirname(os.path.realpath(__file__)))
    operating_system = platform.system()
    data = None

    if str(operating_system) == 'Linux':
        current_dir = current_dir + '/Output/'
    elif str(operating_system) == 'Windows':
        current_dir = current_dir + '\\Output\\'

    def __init__(self, args):
        self.args = args
        self.file_name = args.filename
        self.result = args.result
        pass

    def main(self):
        if os.path.exists(self.current_dir):
            files = os.listdir(self.current_dir)
            if len(files) == 0:
                print("No files found")
                return
            files.sort()

        else:
            print("No files found")
            return

        file_name = self.file_name

        if str(self.operating_system) == 'Linux':
            file = f"{self.current_dir}/{file_name}"

        elif str(self.operating_system) == 'Windows':
            file = f"{self.current_dir}\\{file_name}"

        try:
            if "json" in file:
                with open(file, 'r') as openFile:
                    self.data = json.load(openFile)

            elif "csv" in file:
                with open(file, 'r') as openFile:
                    self.data = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                                 for row in csv.DictReader(openFile, skipinitialspace=True)]
        except Exception as err:
            print(err)
            return
        else:
            if "error" in file:
                print(f"Retrying {len(self.data)} errors")
                load_error = LoadError(self.data, self.args)
                load_error.start()

            else:
                print(self.result)
                upload_sql = uts.HandleResult(self.data, True, file_name=file_name, choice=self.result)
                upload_sql.update()


class LoadError:
    def __init__(self, data, args):
        self.data = data
        self.args = args
        self.f_name = args.filename

    def start(self):
        if "tokopedia" in self.f_name:
            process = TPSelenium.Tokopedia(urls=self.data, args=self.args)
            process.scrape_errors()

        if "shopee" in self.f_name:
            process = ShopeeSelenium.Shopee(urls=self.data, args=self.args)
            process.scrape_errors()

        if "bukalapak" in self.f_name:
            process = BLSelenium.Bukalapak(urls=self.data, args=self.args)
            process.scrape_errors()
