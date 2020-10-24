import json
import platform
import sys
import argparse
from datetime import datetime
from Tokopedia import TPSelenium
from Bukalapak import BLSelenium
from Shopee import ShopeeSelenium
import signal
import LoadFromFile as lff
import urllib.parse as parse
import os

class Main:
    operating_system = platform.system()

    def __init__(self, args):
        self.args = args
        self.command = args.command
        print(self.command)

    def clearConsole(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def fixKeyWord(self, key):
        return parse.quote(key)

    def main(self):
        self.clearConsole()
        if self.command == 'scrape':
            if self.args.marketplace.lower() == 'tokopedia':
                print(f"tokopedia key:{self.args.query} and page={self.args.page} and result: {self.args.result}")
                self.process = TPSelenium.Tokopedia(args=self.args)
                self.process.scrape_search_results()

            elif self.args.marketplace.lower() == 'bukalapak':
                print(f"bukalapak key:{self.args.query} and page={self.args.page} and result: {self.args.result}")
                self.process = BLSelenium.Bukalapak(args=self.args)
                self.process.scrape_search_results()

            elif self.args.marketplace.lower() == 'shopee':
                print(f"shopee key:{self.args.query} and page={self.args.page} and result: {self.args.result}")
                self.process = ShopeeSelenium.Shopee(args=self.args)
                self.process.scrape_search_results()

        elif self.command == 'load':
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


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(required=True, dest='command')


parser_a = subparsers.add_parser('scrape', help='scrapes')
parser_a.add_argument('-m',
                      '--marketplace',
                      help='the marketplace',
                      metavar='',
                      type=str,
                      required=True)

parser_a.add_argument('-q',
                      '--query',
                      help='keyword for search',
                      metavar='',
                      type=str,
                      required=True)

parser_a.add_argument('-p',
                      '--page',
                      help='the number of pages to be scraped',
                      metavar='',
                      type=int,
                      required=True)

parser_a.add_argument('-r',
                      '--result',
                      help='the file format for the results',
                      metavar='',
                      type=str,
                      required=True)

parser_b = subparsers.add_parser('load', help='loads from existing file')
parser_b.add_argument('-f',
                      '--filename',
                      help='name of the file',
                      type=str,
                      metavar='',
                      required=True)
parser_b.add_argument('-r',
                      '--result',
                      help='the file format for the results',
                      metavar='',
                      type=str,
                      required=True)

try:
    args = parser.parse_args()
    print(vars(args))
except TypeError as err:
    parser.print_help()
    exit()



if __name__ == "__main__":
    main = Main(args)
    signal.signal(signal.SIGINT, main.handleInterrupt)
    # try:
    main.main()
    # except Exception as err:
    #     print(err)
