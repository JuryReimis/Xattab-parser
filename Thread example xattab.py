from PyQt5 import QtWidgets, QtCore
from testlabel import Ui_MainWindow
from warning import Ui_Warning_window
from table import Ui_Table
import sys
import requests
from bs4 import BeautifulSoup
import os
import csv
import time
import fake_useragent


class MyWindow(QtWidgets.QMainWindow):
    signal = QtCore.pyqtSignal(bool)
    signal_input = QtCore.pyqtSignal(bool)
    signal_cheker = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(MyWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.parser = Parser(mywindow=self)
        self.thread_1 = QtCore.QThread()
        self.parser.moveToThread(self.thread_1)
        self.signal.connect(self.parser.start)
        self.signal_input.connect(self.parser.input_line)
        self.signal_cheker.connect(self.parser.csv_creat)
        self.parser.signal.connect(self.warning_msg)

        self.ui.startbutton.clicked.connect(self.start_signal)
        self.ui.pagesbutton.clicked.connect(self.input_signal)
        self.ui.csvcreatcheck.clicked.connect(self.csv_signal)

        self.thread_1.start()

    def start_signal(self):
        self.signal.emit(True)

    def input_signal(self):
        self.signal_input.emit(True)

    def csv_signal(self):
        self.signal_cheker.emit(True)

    @QtCore.pyqtSlot(int)
    def warning_msg(self, value):
        if value == 0:
            self.warning = WarningMsg(0)
        if value == 1:
            self.warning = WarningMsg(flag=1, last_page=self.parser.last_page)
        self.warning.setWindowModality(2)
        self.warning.show()


###############################################################


class Parser(QtCore.QObject):
    def __init__(self, mywindow, parent=None):
        super(Parser, self).__init__(parent)
        self.mywindow = mywindow
        self.user_agent = fake_useragent.UserAgent()
        self.headers = {
            "port": "25565", "user-agent": self.creat_user_agent(), "accept": "*/*"}
        self.Games = {}
        self.default = {"number": None, "Год выхода": None, "Жанр": None, "Размер": None, "Таблетка": None,
                        "Ссылка": None}
        self.file_path = "repacks by xattab.csv"

        self.actual_link = self.get_actual_link()
        self.last_page = None
        self.pages = self.mywindow.ui.PagesNow.text()
        self.html = None
        self.game_number = 1
        self.warning = None
        print("__init__ end")

    @staticmethod
    def creat_user_agent():
        return fake_useragent.UserAgent().random

    @QtCore.pyqtSlot(bool)
    def start(self):
        self.mywindow.ui.parsing_status.setText("Парсинг начинается!")
        self.html = self.get_html(self.actual_link, self.pages)
        self.parser()
        self.mywindow.ui.parsing_status.setText("Операция завершена!")

    def get_actual_link(self):
        html_sup = self.get_html("https://vk.com/xatab_repack_net")
        actual_url = "https://vk.com" + html_sup.find("div", class_="line_value").find("a")["href"]
        actual_link = self.get_html(actual_url).find("input")["value"]
        return actual_link

    def get_html(self, link, page=1):
        print("start get html")
        if page == 1:
            url = requests.get(link, headers=self.headers)
        else:
            url = requests.get(link + "/page/" + str(page))
        if url.status_code == 200:
            html = BeautifulSoup(url.text, "html.parser")
            return html
        else:
            print("error")

    def get_last_page(self):
        print("start last page")
        self.html = self.get_html(self.actual_link)
        last_page = int(self.html.find("div", class_="pagination").find_all("a")[-1].get_text())

        return int(last_page)

    def parser(self):
        for page in range(1, self.pages + 1):
            self.info_block(page)
            self.get_data()
            time.sleep(1)
        if self.csv_creat():
            self.writer_csv()
        if self.mywindow.ui.opencheck.isChecked():
            self.open_file()
        if self.mywindow.ui.tablecheck.isChecked():
            self.table_creat()

    def get_data(self):
        for game in self.html.find_all("div", class_="entry_content"):
            game_html = self.get_html(game.find("a")["href"])
            b_name = (game_html.find("h1", class_="inner-entry__title").get_text().split("]"))[0]+"]"
            self.Games[b_name] = self.default.copy()
            game_details = game_html.find("div", class_="inner-entry__details").get_text().split("\n")
            year = game_details[1].replace('Год выпуска:  ', "").split()
            for i in year:
                try:
                    if i.isdigit() and int(i) // 1000 != 0:
                        self.Games[b_name]["Год выхода"] = i
                except:
                    self.Games[b_name]["Год выхода"] = "Не указано"
            self.Games[b_name]["Жанр"] = game_details[2].split(": ")[1]
            self.Games[b_name]["Размер"] = game_html.find("span", class_="entry__info-size").get_text()
            self.Games[b_name]["Таблетка"] = game_details[-2].split(": ")[1]
            self.Games[b_name]["Ссылка"] = game.find("a")["href"]
            self.Games[b_name]["number"] = self.game_number
            self.info_block()
            self.game_number += 1
            time.sleep(1)

    signal = QtCore.pyqtSignal(int)

    @QtCore.pyqtSlot(bool)
    def input_line(self):
        print("start_input")
        if self.mywindow.ui.InputLine.text():
            pages = int(self.mywindow.ui.InputLine.text())
        else:
            pages = int(self.mywindow.ui.PagesNow.text())
        self.last_page = self.get_last_page()
        if self.last_page >= pages > 5:
            self.signal.emit(0)
        if pages > self.last_page:
            self.signal.emit(1)
            pages = int(self.mywindow.ui.PagesNow.text())
        self.mywindow.ui.PagesNow.setText(str(pages))
        self.pages = pages

    def writer_csv(self):
        self.mywindow.ui.parsing_status.setText("Записываю в файл...")
        with open(self.file_path, mode="w", newline="") as file:
            headers = ["Игра", "number", "Год выхода", "Жанр", "Размер", "Таблетка", "Ссылка"]
            writer = csv.DictWriter(file, delimiter=";", fieldnames=headers)
            writer_game = csv.DictWriter(file, delimiter=";", lineterminator="", fieldnames=["Игра"])
            writer.writeheader()
            for item in self.Games.items():
                writer_game.writerow({"Игра": item[0]})
                writer.writerow(item[1])

    @QtCore.pyqtSlot(bool)
    def csv_creat(self):
        if self.mywindow.ui.csvcreatcheck.isChecked():
            self.mywindow.ui.opencheck.setEnabled(True)
            return True
        else:
            self.mywindow.ui.opencheck.setEnabled(False)
            self.mywindow.ui.opencheck.setChecked(False)
            return False

    def table_creat(self):
        self.mywindow.ui.parsing_status.setText("Создаю таблицу...")
        if self.mywindow.ui.tablecheck.isChecked():
            table = Table(self.Games)
            table.show()

    def open_file(self):
        if self.mywindow.ui.opencheck.isChecked():
            os.startfile(self.file_path)

    def info_block(self, page=0):
        if page == 0:
            full_progress = int(self.pages) / 100  # float
            self.mywindow.ui.progressBar.setValue((1 / full_progress) * int(page + 1))
        else:
            self.mywindow.ui.parsing_status.setText(f"Парсинг страницы {page}...")


class WarningMsg(QtWidgets.QWidget):
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
        headers_h = list(list(self.Games.items())[0][1].keys())
        headers_v = list(self.Games.keys())
        self.ui.tableWidget.setHorizontalHeaderLabels(headers_h)
        self.ui.tableWidget.setVerticalHeaderLabels(headers_v)

        for row in self.Games.keys():
            column_now = 0
            for column in list(self.Games.items())[self.Games[row]["number"] - 1][1].keys():
                if column == "Ссылка":
                    self.lable = QtWidgets.QLabel(self.ui.tableWidget)
                    self.lable.setText(f'<a href="{self.Games[row]["Ссылка"]}"> Ссылка </a>')
                    self.lable.setOpenExternalLinks(True)
                    self.ui.tableWidget.setCellWidget(self.Games[row]["number"] - 1, column_now, self.lable)
                else:
                    self.ui.tableWidget.setItem(self.Games[row]["number"] - 1, column_now, QtWidgets.QTableWidgetItem(str(self.Games[row][column])))
                column_now += 1


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = MyWindow()
    application.show()
    sys.exit(app.exec())
