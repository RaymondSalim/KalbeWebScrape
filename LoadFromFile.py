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

    def __init__(self):
        pass

    def main(self):
        if os.path.exists(self.current_dir):
            files = os.listdir(self.current_dir)
            if len(files) == 0:
                print("No files found")
                return
        else:
            print("No files found")
            return

        print('\n*************************************************************\n')
        for i in range(len(files)):
            print(f"{i+1}. {files[i]}")
        print('\n*************************************************************\n')

        number = int(input('Enter the number of the file\n')) - 1
        file = files[number]
        source = file[:file.index('_'):]

        if "csv" in file:
            print("Cannot load csv file!")
            return

        if str(self.operating_system) == 'Linux':
            file = f"{self.current_dir}/{file}"

        elif str(self.operating_system) == 'Windows':
            file = f"{self.current_dir}\\{file}"



        try:
            with open(file, 'r') as openFile:
                self.data = json.load(openFile)
        except Exception as err:
            print(err)
            return
        else:
            if "error" in file:
                print(f"Retrying {len(self.data)} errors")
                load_error = LoadError(self.data, file)
                load_error.start()

            else:
                handle_data = uts.HandleResult(self.data, True, source)
                handle_data.update()


class LoadError:
    def __init__(self, data, file_name):
        self.data = data
        self.f_name = file_name

    def start(self):
        if "tokopedia" in self.f_name:
            process = TPSelenium.Tokopedia(urls=self.data)
            process.scrape_errors()

        if "shopee" in self.f_name:
            process = ShopeeSelenium.Shopee(urls=self.data)
            process.scrape_errors()

        if "bukalapak" in self.f_name:
            process = BLSelenium.Bukalapak(urls=self.data)
            process.scrape_errors()

