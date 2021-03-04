from PyQt5 import QtWidgets, Qt, QtGui, QtCore
from testlabel import Ui_MainWindow
from warning import Ui_Warning_window
from table import Ui_Table
import sys
import requests
from bs4 import BeautifulSoup
import csv
import os


class MyWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.startbutton.clicked.connect(self.start)

        self.ui.pagesbutton.clicked.connect(self.inputline)

        self.ui.csvcreatcheck.clicked.connect(self.csv_creat)

        self.warning = Warning_msg()
        self.warning.setWindowModality(2)
        self.ui.parsing_status.setText("Парсинг не начат")
        self.default_link = "https://e1.xatab-repack.org/"
        self.default = {"number": None, "Год выхода": None, "Жанр": None, "Размер": None, "Таблетка": None,
                        "Ссылка": None}
        self.number = 1
        self.Games = {}
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81",
            "accept": "*/*"}
        self.pages = 1
        self.last_page = None
        self.file_path = "repacks by xattab.csv"

    def start(self):

        self.parser(self.get_actual_link(), self.pages)
        self.ui.parsing_status.setText("Задача выполнена!")
        print(self.Games)

    def get_actual_link(self):
        self.actual_html = self.get_html("https://vk.com/xatab_repack_net")
        self.actual_link = "https://vk.com" + self.actual_html.find("div", class_="line_value").find("a")["href"]
        self.actual_link = self.get_html(self.actual_link).find("input")["value"]
        return self.actual_link

    def parser(self, link, pages=1):
        for page in range(1, pages + 1):
            self.info_block(page)
            if page > 1:
                self.html = self.get_html(link, page)
                self.get_data()
            else:
                self.html = self.get_html(link)
                self.get_data()

        if self.csv_creat():
            self.writer_csv()
        if self.ui.opencheck.isChecked():
            self.open_file()
        if self.ui.tablecheck.isChecked():
            self.table_creat()

    def get_html(self, link, page=1):
        if page == 1:
            self.url = requests.get(link, headers=self.headers)
        else:
            self.url = requests.get(link + "/page/" + str(page))
        self.html = BeautifulSoup(self.url.text, "html.parser")
        return self.html

    def get_data(self):
        for game in self.html.find_all("div", class_="entry_content"):
            self.game_html = self.get_html(game.find("a")["href"])
            self.b_name = (self.game_html.find("h1", class_="inner-entry__title").get_text().split("]"))[0] + "]"
            self.Games[self.b_name] = self.default.copy()
            self.game_details = self.game_html.find("div", class_="inner-entry__details").get_text().split("\n")
            self.year = self.game_details[1].replace('Год выпуска:  ', "").split()
            for i in self.year:
                try:
                    if i.isdigit() and int(i) // 1000 != 0:
                        self.Games[self.b_name]["Год выхода"] = i
                except:
                    pass
            self.Games[self.b_name]["Жанр"] = self.game_details[2].split(": ")[1]
            self.Games[self.b_name]["Размер"] = self.game_html.find("span", class_="entry__info-size").get_text()
            self.Games[self.b_name]["Таблетка"] = self.game_details[-2].split(": ")[1]
            self.Games[self.b_name]["Ссылка"] = game.find("a")["href"]
            self.Games[self.b_name]["number"] = self.number
            self.number += 1

    def writer_csv(self):
        self.ui.parsing_status.setText("Записываю в файл...")
        with open("repacks by xattab.csv", mode="w", newline="") as file:
            headers = ["Игра", "number", "Год выхода", "Жанр", "Размер", "Таблетка", "Ссылка"]
            writer = csv.DictWriter(file, delimiter=";", fieldnames=headers)
            writer_game = csv.DictWriter(file, delimiter=";", lineterminator="", fieldnames=["Игра"])
            writer.writeheader()
            for item in self.Games.items():
                writer_game.writerow({"Игра": item[0]})
                writer.writerow(item[1])

    def csv_creat(self):
        if self.ui.csvcreatcheck.isChecked():
            self.ui.opencheck.setEnabled(True)
            return True
        else:
            self.ui.opencheck.setEnabled(False)
            self.ui.opencheck.setChecked(False)
            return False

    def table_creat(self):
        self.ui.parsing_status.setText("Создаю таблицу...")
        if self.ui.tablecheck.isChecked():
            self.table = Table(self.Games)
            self.table.show()

    def get_max_pages(self):
        self.get_html(self.default_link)
        self.last_page = int(self.html.find("div", class_="pagination").find_all("a")[-1].get_text())
        print(self.last_page)

    def inputline(self):
        if self.ui.InputLine.text():
            self.pages = int(self.ui.InputLine.text())
        else:
            self.pages = int(self.ui.PagesNow.text())
        self.get_max_pages()
        if self.pages > 5:
            self.warning = Warning_msg(0)
            self.warning.show()
        if self.pages > self.last_page:
            self.warning = Warning_msg(1, self.last_page)
            self.warning.show()
            self.pages = int(self.ui.PagesNow.text())
        self.pages_now()

    def pages_now(self):
        self.ui.PagesNow.setText(str(self.pages))

    def open_file(self):
        if self.ui.opencheck.isChecked():
            os.startfile(self.file_path)

    def info_block(self, page):
        self.ui.parsing_status.setText(f"Парсинг страницы {page}...")


class Warning_msg(QtWidgets.QWidget):
    def __init__(self, flag=0, last_page=None):
        super().__init__()
        self.last_page = last_page
        self.ui = Ui_Warning_window()
        self.ui.setupUi(self)
        if flag == 0:
            self.more_5()
        elif flag == 1:
            self.more_max()

    def more_5(self):
        self.ui.label.setText("Внимание, парсинг больше 5 страниц может занять значительное время!")

    def more_max(self):
        self.ui.label.setText(f"На сайте нет столько страниц! Последняя страница №{self.last_page}")


class Table(QtWidgets.QTableWidget):
    def __init__(self, games):
        self.Games = games
        super().__init__()
        self.ui = Ui_Table()
        self.ui.setupUi(self)
        self.columns = 6
        self.ui.tableWidget.setColumnCount(self.columns)  # Количество распарсенных параметров
        self.rows = len(self.Games.keys())
        self.ui.tableWidget.setRowCount(self.rows)  # Просчитать количество игр в словаре(Games.keys())
        headers_H = list(list(self.Games.items())[0][1].keys())
        headers_V = list(self.Games.keys())
        self.ui.tableWidget.setHorizontalHeaderLabels(headers_H)
        self.ui.tableWidget.setVerticalHeaderLabels(headers_V)

        for row in self.Games.keys():
            column_now = 0
            for column in list(self.Games.items())[self.Games[row]["number"] - 1][1].keys():
                if column == "Ссылка":
                    self.lable = QtWidgets.QLabel(self.ui.tableWidget)
                    self.lable.setText(f'<a href="{self.Games[row]["Ссылка"]}"> Ссылка </a>')
                    self.lable.setOpenExternalLinks(True)
                    self.ui.tableWidget.setCellWidget(self.Games[row]["number"] - 1, column_now, self.lable)
                else:
                    self.ui.tableWidget.setItem(self.Games[row]["number"] - 1, column_now,
                                                QtWidgets.QTableWidgetItem(str(self.Games[row][column])))
                column_now += 1


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()
    sys.exit(app.exec())
