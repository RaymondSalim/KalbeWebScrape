import csv
import os
import platform
import json
import pyodbc
import mysql.connector
import stdiomask


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

        else:

            if not self.launched_start:
                if not os.path.exists(os.path.normpath(self.output_dir)):
                    os.mkdir(os.path.normpath(self.output_dir))
            else:
                self.file_name = self.current_dir + '/Output/' + self.file_name

            if self.choice == 'csv':
                self.file_name = self.file_name.replace('.json', '.csv')
                print(f"Saving to {self.file_name}")
                keys = self.data[0].keys()
                try:
                    with open(self.file_name, 'w', newline='', encoding='utf-8') as csvFile:
                        dict_writer = csv.DictWriter(csvFile, keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(self.data)
                except:
                    with open(self.file_name, 'w') as outFile:
                        json.dump(self.data, outFile)

            if self.choice == 'json':
                print(f"Saving to {self.file_name}")
                with open(self.file_name, 'w') as outFile:
                    json.dump(self.data, outFile)
