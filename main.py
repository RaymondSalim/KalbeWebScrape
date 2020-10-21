import json
import platform
import sys
from datetime import datetime
from Tokopedia import TPSelenium
from Bukalapak import BLSelenium
from Shopee import ShopeeSelenium
import signal
import LoadFromFile as lff
import urllib.parse as parse
import os


header = """
1. Tokopedia
2. Bukalapak
3. Shopee

9. Load from file to SQL or Rescrape errors\n"""
class Main:

    operating_system = platform.system()

    def clearConsole(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def fixKeyWord(self, key):
        return parse.quote(key)

    def main(self):
        self.clearConsole()

        print(header)
        option = int(input())


        while not (9 >= option >= 1):
            option = int(input("Enter a valid number\n"))
            print(header)

        self.clearConsole()
        if option != 9:
            keyword = self.fixKeyWord(input("Enter search keyword\n"))
            page_limit = int(input("\nNumber of pages to scrape\n"))

        if option == 1:  # TOKOPEDIA
            self.process = TPSelenium.Tokopedia(keyword_in=keyword, page_lim=page_limit)
            self.process.scrape_search_results()

        elif option == 2:  # BUKALAPAK
            self.process = BLSelenium.Bukalapak(keyword_in=keyword, page_lim=page_limit)
            self.process.scrape_search_results()

        elif option == 3: # SHOPEE
            self.process = ShopeeSelenium.Shopee(keyword_in=keyword, page_lim=page_limit)
            self.process.scrape_search_results()

        elif option == 9:
            load_json = lff.LoadFromFile()
            load_json.main()
        else:
            print("rip")

    def handleInterrupt(self, signal, frame):

        data = self.process.data
        errors = self.process.errors
        if len(data) > 0:
            output_dir = str(os.path.dirname(os.path.realpath(__file__)))

            if str(self.operating_system) == 'Linux':
                output_dir = output_dir.replace('/CLI', '/CLI/Output/')
            elif str(self.operating_system) == 'Windows':
                output_dir = output_dir.replace('\\CLI', '\\CLI\\Output\\')

            file_name = f"{output_dir}{self.process.id}_{str(datetime.now()).replace(':', '꞉')}.json"

            if not os.path.exists(os.path.normpath(output_dir)):
                os.mkdir(os.path.normpath(output_dir))

            print(f"Saving to {file_name}")
            with open(file_name, 'w') as outFile:
                json.dump(data, outFile)

        if len(errors) > 0:
            with open(file_name.replace('.json', '_errors.json')) as out:
                json.dump(errors, out)

        print("\nExiting...")
        exit(1)



if __name__ == "__main__":
    main = Main()
    signal.signal(signal.SIGINT, main.handleInterrupt)
    # try:
    main.main()
    # except Exception as err:
    #     print(err)