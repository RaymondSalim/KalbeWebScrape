import csv
import os
import platform
import json
import pyodbc
import mysql.connector
import stdiomask

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

        if self.choice == 'mysql':
            mydb = mysql.connector.connect(
                host=input("Enter SQL Server\n"),
                user=input("Enter SQL Username\n"),
                password=stdiomask.getpass(prompt='Enter SQL Password\n'),
                database=input("Enter SQL Database\n")
            )
            table_name = input("Enter database table name\n")

            mycursor = mydb.cursor()

            command = """INSERT IGNORE INTO {} VALUES (%(name)s, %(url)s, %(price)s, %(discount)s, %(rating)s, %(rating_count)s,
            %(sold_count)s, %(shop_name)s, %(shop_category)s, %(location)s, %(description)s, %(seen_date)s, %(seen_by)s,
            %(marketplace)s, %(category)s)""".format(table_name)

            if not mydb.is_connected():
                mydb.reconnect()

            try:
                mycursor.executemany(command, self.data)
                mydb.commit()

            except Exception as err:
                print(err)

                if not self.launched_start:
                    if not os.path.exists(os.path.normpath(self.output_dir)):
                        os.mkdir(os.path.normpath(self.output_dir))

                    print(f"Saving to {self.file_name}")
                    with open(self.file_name, 'w') as outFile:
                        json.dump(self.data, outFile)

                    file_csv = self.file_name.replace('.json', '.csv')
                    keys = self.data[0].keys()
                    with open(file_csv, 'w', encoding='utf-8') as csvFile:
                        dict_writer = csv.DictWriter(csvFile, keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(self.data)

            else:
                print("Upload succesful")

        elif self.choice == "sqls":
            ## https://docs.microsoft.com/en-us/sql/connect/python/pyodbc/step-3-proof-of-concept-connecting-to-sql-using-pyodbc?view=sql-server-ver15
            server = input('Enter SQL Server\n')
            database = input('Enter SQL Database\n')
            username = input('Enter SQL Username\n')
            password = stdiomask.getpass(prompt='Enter SQL Password\n')
            table_name = input("Enter database table name\n")
            cnxn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

            mycursor = cnxn.cursor()

            try:
                for items in self.data:
                    placeholders = ""  # ', '.join(("'" + str(v)  + "'") for v in items.values())

                    for i in items.values():

                        if i == "":
                            placeholders = placeholders + "NULL, "
                            continue

                        if type(i) is str:
                            i = i.replace('\'', '\'\'')
                            placeholders = placeholders + f"'{i}', "
                        else:
                            placeholders = placeholders + f"{i}, "

                    placeholders = placeholders[:-2:]
                    columns = ', '.join(items.keys())
                    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholders)

                    mycursor.execute(sql)

                cnxn.commit()

            except Exception as err:
                print(err)

                if not self.launched_start:
                    if not os.path.exists(os.path.normpath(self.output_dir)):
                        os.mkdir(os.path.normpath(self.output_dir))

                    print(f"Saving to {self.file_name}")
                    with open(self.file_name, 'w') as outFile:
                        json.dump(self.data, outFile)

                    file_csv = self.file_name.replace('.json', '.csv')
                    keys = self.data[0].keys()
                    with open(file_csv, 'w', encoding='utf-8') as csvFile:
                        dict_writer = csv.DictWriter(csvFile, keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(self.data)

            else:
                print("Upload succesful")

        elif self.choice == "continue":
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
                with open(filepath, 'r') as openFile:
                    data = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                                 for row in csv.DictReader(openFile, skipinitialspace=True)]

                filepath = filepath.replace('_continued', '')

                with open(filepath, 'r') as openFile:
                    tempdata = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                            for row in csv.DictReader(openFile, skipinitialspace=True)]

                finaldata = data + tempdata
                print(f"Saving to {filepath}")
                self.save_csv(filepath, finaldata)

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
