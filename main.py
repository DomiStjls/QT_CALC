from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap
import pyqtgraph
from pyqtgraph import PlotWidget
from pyqtgraph import *
import sys
import sqlite3
import random
import csv
import os


class Format_not_eq(Exception):
    pass


class Format_eq_not_one(Exception):
    pass


class Format_not_main_ch(Exception):
    pass


class Format_not_x(Exception):
    pass


class Bd(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi("bd.ui", self)
        self.other = other
        # делаем связь между  классами
        self.connection = sqlite3.connect("graph_db.db")
        self.cursor = self.connection.cursor()
        self.key = 10000000
        # создаем базу
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Style (
        style INTEGER PRIMARY KEY,
        pen TEXT NOT NULL,
        back TEXT NOT NULL,
        width INTEGER,
        range INTEGER,
        lines TEXT NOT NULL
        );
        """
        )
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Main (
        style INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        x TEXT,
        y TEXT
        );
        """
        )
        self.connection.commit()
        self.Delete.clicked.connect(self.delete)
        self.Save.clicked.connect(self.save_results)
        self.Find.clicked.connect(self.find)
        self.Open.clicked.connect(self.open)
        # связываем функции и дизайн
        self.show_b()

    def show_b(self):
        # функция чтобы показать таблицу
        query = """
            SELECT DISTINCT Main.name, Main.style
            FROM Main, Style
        """

        self.connection.commit()
        res = self.cursor.execute(query).fetchall()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Название", "Стиль"])
        self.tableWidget.setRowCount(0)
        # Заполняем таблицу элементами
        for i, row in enumerate(res):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))

    def delete(self):
        # удаляем запись из базы данных
        button = QMessageBox.question(
            self,
            "Deleting",
            f"Точно хотите удалить запись под именем {self.Name_d.text()}?",
        )
        # сообщение с подтверждением
        if button == QMessageBox.StandardButton.Yes:
            query = """
            DELETE FROM Main
            WHERE name = ?
            """
            res = self.cursor.execute(query, [self.Name_d.text()]).fetchall()
            self.show_b()

    def save_results(self):
        # сохранение записи
        button = QMessageBox.question(
            self,
            "Saving",
            f"Точно хотите сохранить запись под именем {self.Name_s.text()}?",
        )
        r = int(self.key * random.random())
        # ключ
        query = """
            SELECT DISTINCT Main.name, Main.style
            FROM Main, Style
            WHERE Main.name LIKE ?
        """
        res = self.cursor.execute(query, [self.Name_s.text()]).fetchall()
        # проверка на дублирование
        if res != []:
            button = QMessageBox.warning(
                self,
                "Warning",
                f"Запись под именем {self.Name_s.text()} уже существует.",
            )
        if button == QMessageBox.StandardButton.Yes and res == []:
            # запись в бд
            query = """
            INSERT INTO Main VALUES(?, ?, ?, ?);

            """
            res = self.cursor.execute(
                query,
                [
                    r,
                    self.Name_s.text(),
                    "/".join(
                        [
                            " ".join([str(ch) for ch in el])
                            for el in self.other.all_data_x
                        ]
                    ),
                    "/".join(
                        [
                            " ".join([str(ch) for ch in el])
                            for el in self.other.all_data_y
                        ]
                    ),
                ],
            ).fetchall()
            query = """
            INSERT INTO Style VALUES(?, ?, ?, ?, ?, ?);
            """
            a = [
                r,
                " ".join(
                    [
                        str(el)
                        for el in [
                            self.other.r_pen_p_main,
                            self.other.g_pen_p_main,
                            self.other.b_pen_p_main,
                        ]
                    ]
                ),
                " ".join(
                    [
                        str(el)
                        for el in [
                            self.other.r_back_p_main,
                            self.other.g_back_p_main,
                            self.other.b_back_p_main,
                        ]
                    ]
                ),
                self.other.width_main,
                self.other.range_main,
                self.other.line_main,
            ]
            res = self.cursor.execute(
                query,
                a,
            ).fetchall()
            self.connection.commit()
            self.show_b()
            # показ реультата
            with open("styles.csv", "a", encoding="utf8", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(a)
                # запись в csv изменений

    def find(self):
        # поиск записи
        name = self.Name_f.text()
        if name == "":
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Ошибка!")
            dlg.setText(f"Вы не ввели название")
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.setIcon(QMessageBox.Icon.Warning)
            button = dlg.exec()
        else:
            query = """
                SELECT Main.name, Main.style
                FROM Main, Style
                WHERE Main.name LIKE ?
                AND Main.style = Style.style
            """

            res = self.cursor.execute(query, ["%" + name + "%"]).fetchall()
            self.connection.commit()
            self.tableWidget.setColumnCount(2)
            self.tableWidget.setRowCount(0)
            # Заполняем таблицу элементами
            for i, row in enumerate(res):
                self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
                for j, elem in enumerate(row):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))

    def open(self):
        # открываем запись
        button = QMessageBox.question(
            self,
            "Opening",
            f"Точно хотите открыть запись под именем {self.Name_o.text()}?",
        )
        if button == QMessageBox.StandardButton.Yes:
            query = """
                SELECT pen, back, width, range, lines, Main.x, Main.y
                FROM Main, Style
                WHERE Main.name LIKE ?
                AND Main.style = Style.style
            """
            res = self.cursor.execute(query, [self.Name_o.text()]).fetchall()
            if res == []:
                button = QMessageBox.warning(
                    self,
                    "",
                    f"Записи с именем {self.Name_s.text()} не найдено.",
                )
            elif len(res) > 1:
                button = QMessageBox.warning(
                    self,
                    "",
                    f"Записей с именем {self.Name_s.text()} больше одной. Удалите ненужные.",
                )
            else:
                params = res[0]
                color_p = [int(el) for el in params[0].split()]
                color_b = [int(el) for el in params[1].split()]
                
                width = int(params[2])
                range_b = int(params[3])
                line = int(params[4])
                x = [[float(ch) for ch in el.split()] for el in params[5].split("/")]
                y = [[float(ch) for ch in el.split()] for el in params[6].split("/")]

                self.other.clear_p()
                # посылаем запрос для построения графика
                self.other.change_back(color_b, color_p, width, range_b, line, x, y)


class Settings(QWidget):
    def __init__(self, other):
        # класс настроек
        super().__init__()
        uic.loadUi("g_settings.ui", self)
        self.save_settings.clicked.connect(self.save_set)
        self.other = other

        self.r_line = QRadioButton("Сплошная")
        self.r_punct = QRadioButton("Пунктирная")
        self.verticalLayout_2.addWidget(self.r_line)
        self.verticalLayout_2.addWidget(self.r_punct)
        self.line = QtCore.Qt.SolidLine

        self.range_r.valueChanged.connect(self.change_range)
        self.range_value = 40
        self.l_range.setText(self.l_range.text() + str(self.range_value))

        self.r_line.setChecked(True)
        self.r_punct.setChecked(False)
        self.lines = QButtonGroup()
        self.lines.setExclusive(False)
        self.lines.buttonClicked.connect(self.change_line)
        self.lines.addButton(self.r_line)
        self.lines.addButton(self.r_punct)

        self.s_width.setWrapping(True)

        self.r_pen.setWrapping(True)
        self.g_pen.setWrapping(True)
        self.b_pen.setWrapping(True)

        self.r_back.setWrapping(True)
        self.g_back.setWrapping(True)
        self.b_back.setWrapping(True)

        self.width = int(self.s_width.value())

        self.r_pen_p = 255
        self.g_pen_p = 255
        self.b_pen_p = 255

        self.r_back_p = 0
        self.g_back_p = 0
        self.b_back_p = 0

    def change_range(self):
        # смена колличества значений
        self.range_value = self.range_r.value()
        self.l_range.setText(self.l_range.text()[:-2] + str(self.range_value))

    def change_line(self, radioButton):
        # смена стиля линии
        for button in self.lines.buttons():
            if button is not radioButton:
                button.setChecked(False)
        if not any(b.isChecked() for b in self.lines.buttons()):
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Ошибка!")
            dlg.setText(
                f"Вы не выбрали ни одного параметра линии. Если вы не выбирете, будет выбран параметр по умолчанию <Сплошная>"
            )
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.setIcon(QMessageBox.Icon.Warning)
            button = dlg.exec()
        # 2 варианта стиля линии
        if radioButton.isChecked() and radioButton == self.r_punct:
            self.line = QtCore.Qt.DashDotLine
        else:
            self.line = QtCore.Qt.SolidLine

    def save_set(self):
        # после сохранения изменений надо построить график
        self.width = int(self.s_width.value())

        self.r_pen_p = int(self.r_pen.value())
        self.g_pen_p = int(self.g_pen.value())
        self.b_pen_p = int(self.b_pen.value())

        self.r_back_p = int(self.r_back.value())
        self.g_back_p = int(self.g_back.value())
        self.b_back_p = int(self.b_back.value())
        
        
        # строим график
        self.other.change_back(
            (self.r_back_p, self.g_back_p, self.b_back_p),
            (self.r_pen_p, self.g_pen_p, self.b_pen_p),
            self.width,
            self.range_value,
            self.line,
        )


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        # главный класс
        uic.loadUi("MainWindow.ui", self)
        self.g = self.graphWidget
        self.w = Settings(self)
        self.b = Bd(self)
        pixmap = QPixmap("pixmap.png")
        self.image.setPixmap(pixmap)
        # связываем классы
        self.r_pen_p_main = Settings(self).r_pen_p
        self.g_pen_p_main = Settings(self).g_pen_p
        self.b_pen_p_main = Settings(self).b_pen_p
        self.pen = (self.r_pen_p_main, self.g_pen_p_main, self.b_pen_p_main)

        self.r_back_p_main = Settings(self).r_back_p
        self.g_back_p_main = Settings(self).g_back_p
        self.b_back_p_main = Settings(self).b_back_p
        self.back_color = (self.r_back_p_main, self.g_back_p_main, self.b_back_p_main)
        self.graphWidget.setBackground(self.back_color)

        self.width_main = Settings(self).width
        self.range_main = Settings(self).range_value
        self.line_main = Settings(self).line

        for i in range(4):
            for j in range(6):
                self.gridLayout.itemAt(j + i * 6).widget().clicked.connect(
                    self.make_function
                )
        self.data_y = []
        self.data_x = []

        self.all_data_x = [[], [], []]
        self.all_data_y = [[], [], []]

        self.Build.setStatusTip("Нажмите, чтобы построить график")
        self.Build.triggered.connect(self.do_function)

        self.Graph_Settings.setStatusTip("Нажмите, чтобы открыть настройки графика")
        self.Graph_Settings.triggered.connect(self.show_graph_settings)

        self.Clear.setStatusTip("Нажмите, чтобы очистить поле для графика")
        self.Clear.triggered.connect(self.clear_p)
        self.Referense.triggered.connect(self.open_ref)
        self.Save.triggered.connect(self.save)

        self.equation1.setEnabled(False)
        self.equation2.setEnabled(False)
        self.equation3.setEnabled(False)

        self.choice = 0
        self.equations = [
            self.equation1,
            self.equation2,
            self.equation3,
        ]
        self.setStatusBar(QStatusBar(self))
        self.pr.setStatusTip(f"Выбрано поле номер: {self.choice + 1}")

        self.Open_bd.setStatusTip("Нажмите, чтобы открыть баззу данных")
        self.Open_bd.triggered.connect(self.open_bd)

    def open_ref(self):
        # открыть справку
        os.startfile("referenses.docx")

    def open_bd(self):
        # открыть базу данных
        self.b.show()

    def make_function(self):
        # записываем уравнение
        if self.sender().text() == "Переход к новому уравнению":
            self.choice = (self.choice + 1) % 3
            self.pr.setStatusTip(f"Выбрано поле номер: {self.choice + 1}")
        elif self.sender().text() == "⌫":
            self.equations[self.choice].setText(self.equations[self.choice].text()[:-1])
        elif self.sender().text() == "^":
            self.equations[self.choice].setText(
                self.equations[self.choice].text() + "**"
            )
        else:
            self.equations[self.choice].setText(
                self.equations[self.choice].text() + self.sender().text()
            )

    def do_function(self):
        # преобразуем записанное уравнение в график
        var = ["y", "f", "g"]
        self.pr.setStatusTip(f"Выбрано поле номер: {self.choice + 1}")
        try:
            d = self.equations[self.choice].text().split("=")
            if len(d) > 2:
                raise Format_eq_not_one(
                    "Неправильный формат. Больше чем один знак '='."
                )
            if len(d) == 1:
                raise Format_not_eq("Неправильный формат. Нет знака '='.")
            main_ch = ""
            flag = 0
            for el in var:
                if el in d[0] and (
                    "x" in d[1] or ("x" not in d[1] and "x" not in d[0])
                ):
                    main_ch = el
                    flag = 1
                    break
                if el in d[1] and (
                    "x" in d[0] or ("x" not in d[1] and "x" not in d[0])
                ):
                    main_ch = el
                    flag = 1
                    break

            if flag == 0:
                raise Format_not_main_ch(
                    "Неправильный формат. Запись должна представлять из себя уравнение вида f(x)/g(x)/y(x)."
                )
            if main_ch in d[0]:
                s = d[1]
            else:
                s = d[0]
            if s == "":
                raise SyntaxError("Неверная запись уравнения.")
            for el in var:
                if el != main_ch and el in d[0] or el in d[1]:
                    raise SyntaxError(f"Лишний символ '{el}'")
            # само построение
            self.data_y = []
            self.data_x = []
            data_x_n = [i for i in range(self.range_main + 1)]
            self.pen = pyqtgraph.mkPen(
                color=(self.r_pen_p_main, self.g_pen_p_main, self.b_pen_p_main),
                width=self.width_main,
                style=self.line_main,
            )
            self.back_color = (
                self.r_back_p_main,
                self.g_back_p_main,
                self.b_back_p_main,
            )
            for x in data_x_n:
                s_copy = s.replace("x", str(x))

                y = eval(s_copy)
                self.data_y.append(y)
                self.data_x.append(x)

            self.all_data_x[self.choice] = self.data_x
            self.all_data_y[self.choice] = self.data_y
            self.graphWidget.clear()
            for i in range(3):
                self.graphWidget.plot(
                    self.all_data_x[i],
                    self.all_data_y[i],
                    pen=self.pen,
                )
        # если есть деление на 0
        except ZeroDivisionError:
            data_x_n = [i for i in range(self.range_main + 1) if i != x]
            self.data_y = []
            self.data_x = []
            for x in data_x_n:
                s_copy = s.replace("x", str(x))
                y = eval(s_copy)
                self.data_y.append(y)
                self.data_x.append(x)

            self.all_data_x[self.choice] = self.data_x
            self.all_data_y[self.choice] = self.data_y
            self.graphWidget.clear()
            for i in range(3):
                self.graphWidget.plot(
                    self.all_data_x[i],
                    self.all_data_y[i],
                    pen=self.pen,
                )
        except SyntaxError as e:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Ошибка!")
            dlg.setText(f"Уравнение записано математически неверно. Проверьте еще раз.")
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.setIcon(QMessageBox.Icon.Question)
            button = dlg.exec()

        except Exception as e:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Ошибка!")
            dlg.setText(f"Возникла ошибка при вводе уравнения: {e}")
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.setIcon(QMessageBox.Icon.Question)
            button = dlg.exec()

    def show_graph_settings(self, checked):
        # показать настройки
        self.w.show()

    def clear_p(self):
        # очищение графика полностью
        for i in range(3):
            self.graphWidget.clear()
            self.all_data_x[i] = []
            self.all_data_y[i] = []
        self.equation1.setText("")
        self.equation2.setText("")
        self.equation3.setText("")

    def change_back(self, c_b, c_p, w, r, li, x=0, y=0):
        # смена настроек
        if x != 0 and y != 0:
            self.all_data_x = x
            self.all_data_y = y
        self.back_color = c_b
        self.r_back_p_main, self.g_back_p_main, self.b_back_p_main = c_b
        self.r_pen_p_main, self.g_pen_p_main, self.b_pen_p_main = c_p
        self.graphWidget.clear()
        self.width_main = w
        self.range_main = r
        self.line_main = li
        self.graphWidget.setBackground(self.back_color)
        for i in range(len(self.all_data_x)):
            self.graphWidget.plot(
                self.all_data_x[i][: self.range_main],
                self.all_data_y[i][: self.range_main],
                pen=pyqtgraph.mkPen(
                    color=(self.r_pen_p_main, self.g_pen_p_main, self.b_pen_p_main),
                    width=self.width_main,
                    style=self.line_main,
                ),
            )

    def save(self):
        # стандартный диалог + сохранение
        button = QMessageBox.question(self, "Saving", "Точно хотите сохранить?")

        if button == QMessageBox.StandardButton.Yes:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save File", ".", "Text Files (*.txt);"
            )
            if filename:
                fn = (
                    filename + "_ONLY_FOR_GRAPH"
                    if not filename.endswith("_ONLY_FOR_GRAPH")
                    else filename
                )
                with open(fn, "w") as file:
                    file.write(
                        f"{' '.join([str(el) for el in self.data_x])}\n{' '.join([str(el) for el in self.data_y])}\n"
                    )
        else:
            pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
