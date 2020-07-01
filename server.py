import mysql.connector
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QHeaderView
import socket
import ssl
import threading
from _thread import start_new_thread
from PySide2.QtSql import QSqlQueryModel, QSqlQuery
import bcrypt
import numpy as np
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler

# information about server, clients & ssl certificates
listen_addr = '127.0.0.1'
listen_port = 8082
server_cert = 'server.crt'
server_key = 'server.key'
client_certs = 'client.crt'

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=server_cert, keyfile=server_key)
context.load_verify_locations(cafile=client_certs)


class Window(object):
    def __init__(self, MainWindow):
        # main window - building, sizing, font, background
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(960, 720)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(960, 720))
        MainWindow.setMaximumSize(QtCore.QSize(960, 720))
        # MainWindow.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        font.setPointSize(12)
        MainWindow.setFont(font)
        MainWindow.setWindowTitle("Authentication System Manager")
        MainWindow.setAutoFillBackground(False)

        # main widget
        self.main_widget = QtWidgets.QWidget(MainWindow)
        self.main_widget.setObjectName("main_widget")

        # widget with two tabs: one with history logs, one with information and commands regarding users
        self.logs_and_users = QtWidgets.QTabWidget(self.main_widget)
        self.logs_and_users.setGeometry(QtCore.QRect(0, 0, 971, 521))
        self.logs_and_users.setObjectName("logs_and_users")
        self.logs_and_users.currentChanged.connect(
            self.reload_data)  # when the user changes the tab, the data is forcefully reloaded

        # the first tab - history logs (displayed as a table)
        self.logs_tab = QtWidgets.QWidget()
        self.logs_tab.setObjectName("logs_tab")
        self.logs_table = QtWidgets.QTableWidget(self.logs_tab)
        self.logs_table.setGeometry(QtCore.QRect(0, 0, 956, 484))
        self.logs_table.setObjectName("logs_table")
        self.logs_table.setRowCount(0)
        self.logs_table.setColumnCount(0)
        self.logs_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.logs_and_users.addTab(self.logs_tab, "")

        # the second tab - information & commands regarding users
        # users displayed as a list
        self.users_tab = QtWidgets.QWidget()
        self.users_tab.setObjectName("users_tab")
        self.users_list = QtWidgets.QListWidget(self.users_tab)
        # self.users_list.setGeometry(QtCore.QRect(0, 0, 471, 484))
        self.users_list.setGeometry(QtCore.QRect(0, 0, 271, 484))
        self.users_list.setObjectName("users_list")
        self.users_list.itemClicked.connect(self.load_users_logs)

        # a table with logs regarding selected user's activity
        self.users_logs_table = QtWidgets.QTableWidget(self.users_tab)
        # self.users_logs_table.setGeometry(QtCore.QRect(474, 0, 481, 192))
        self.users_logs_table.setGeometry(QtCore.QRect(274, 0, 681, 271))
        self.users_logs_table.setObjectName("users_logs_table")
        self.users_logs_table.setColumnCount(0)
        self.users_logs_table.setRowCount(0)
        self.users_logs_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # self.users_logs_table.horizontalHeaderItem().setTextAlignment(QtCore.Qt.AlignHCenter)

        # button for changing a user's username
        self.change_username_button = QtWidgets.QPushButton(self.users_tab)
        # self.change_username_button.setGeometry(QtCore.QRect(610, 240, 191, 41))
        self.change_username_button.setGeometry(QtCore.QRect(510, 310, 191, 41))
        self.change_username_button.setObjectName("change_username_button")
        self.change_username_button.clicked.connect(self.change_username_button_action)

        # button for changing a user's password
        self.change_password_button = QtWidgets.QPushButton(self.users_tab)
        # self.change_password_button.setGeometry(QtCore.QRect(610, 300, 191, 41))
        self.change_password_button.setGeometry(QtCore.QRect(510, 360, 191, 41))
        self.change_password_button.setObjectName("change_password_button")
        self.change_password_button.clicked.connect(self.change_password_button_action)

        # button for deleting a user from the database
        self.delete_user_button = QtWidgets.QPushButton(self.users_tab)
        # self.delete_user_button.setGeometry(QtCore.QRect(610, 360, 191, 41))
        self.delete_user_button.setGeometry(QtCore.QRect(510, 410, 191, 41))
        self.delete_user_button.setObjectName("delete_user_button")
        self.delete_user_button.clicked.connect(self.delete_user_button_action)
        self.logs_and_users.addTab(self.users_tab, "")

        # button for deleting old patterns from the database
        self.delete_patterns_button = QtWidgets.QPushButton(self.main_widget)
        self.delete_patterns_button.setGeometry(QtCore.QRect(40, 610, 411, 51))
        self.delete_patterns_button.setObjectName("delete_patterns_button")
        self.delete_patterns_button.clicked.connect(self.delete_old_authentication_patterns_button_action)

        # button for deleting old logs from the database
        self.delete_logs_button = QtWidgets.QPushButton(self.main_widget)
        self.delete_logs_button.setGeometry(QtCore.QRect(500, 610, 411, 51))
        self.delete_logs_button.setObjectName("delete_logs_button")
        self.delete_logs_button.clicked.connect(self.delete_old_logs_button_action)

        # button for reloading/ refreshing data
        self.reload_data_button = QtWidgets.QPushButton(self.main_widget)
        self.reload_data_button.setGeometry(QtCore.QRect(270, 540, 411, 51))
        self.reload_data_button.setObjectName("reload_data_button")
        self.reload_data_button.clicked.connect(self.reload_data)
        MainWindow.setCentralWidget(self.main_widget)

        # menu, status bar
        self.menu_bar = QtWidgets.QMenuBar(MainWindow)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 960, 30))
        self.menu_bar.setObjectName("menu_bar")
        self.menuHelp = QtWidgets.QMenu(self.menu_bar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menu_bar)
        self.status_bar = QtWidgets.QStatusBar(MainWindow)
        self.status_bar.setObjectName("status_bar")
        MainWindow.setStatusBar(self.status_bar)
        self.actionAbout_Authentication_System_Manager = QtWidgets.QAction(MainWindow)
        self.actionAbout_Authentication_System_Manager.setObjectName("actionAbout_Authentication_System_Manager")
        self.menuHelp.addAction(self.actionAbout_Authentication_System_Manager)
        self.menuHelp.addSeparator()
        self.menu_bar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.logs_and_users.setCurrentIndex(0)  # setting the history logs tab as the default one
        self.load_history_logs()  # displaying initial history logs
        # self.load_users_list()  # displaying initial users list

        # this is a server, so it has to accept connections from clients
        threading.Thread(target=accept_connections, daemon=True).start()

    def retranslateUi(self, MainWindow):
        # naming everything
        _translate = QtCore.QCoreApplication.translate
        self.logs_and_users.setTabText(self.logs_and_users.indexOf(self.logs_tab),
                                       _translate("MainWindow", "History Logs"))
        self.change_username_button.setText(_translate("MainWindow", "Change username"))
        self.change_password_button.setText(_translate("MainWindow", "Change password"))
        self.delete_user_button.setText(_translate("MainWindow", "Delete user"))
        self.logs_and_users.setTabText(self.logs_and_users.indexOf(self.users_tab),
                                       _translate("MainWindow", "Users List"))
        self.delete_patterns_button.setText(_translate("MainWindow", "Delete old authentication patterns"))
        self.delete_logs_button.setText(_translate("MainWindow", "Delete old logs"))
        self.reload_data_button.setText(_translate("MainWindow", "Reload data"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionAbout_Authentication_System_Manager.setText(
            _translate("MainWindow", "About Authentication System Manager"))

    # function that loads the history logs that have been fetched from the database into a table
    def load_history_logs(self):
        self.logs_table.clear()
        self.logs_table.setRowCount(0)
        self.logs_table.setColumnCount(0)
        result = get_history_logs()
        if len(result) == 0:
            self.logs_table.insertRow(0)
            self.logs_table.insertColumn(0)
            item = QtWidgets.QTableWidgetItem("No history logs.")
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable & ~QtCore.Qt.ItemIsSelectable)
            self.logs_table.setItem(0, 0, item)
        else:
            for row_number, row_data in enumerate(result):
                self.logs_table.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    if row_number == 0:
                        self.logs_table.insertColumn(column_number)
                    item = QtWidgets.QTableWidgetItem(str(data))
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                    self.logs_table.setItem(row_number, column_number, item)
            self.logs_table.setHorizontalHeaderLabels(["Username", "Action", "Timestamp", "Hostname", "IP Address"])

    # function that loads the users that have been fetched from the database into a list
    def load_users_list(self):
        # loading the list of users that has been fetched from the database
        self.users_list.clear()
        result = get_users()
        if len(result) == 0:
            self.users_list.addItem(QtWidgets.QListWidgetItem("There are currently no registered users."))
        else:
            for row_number, row_data in enumerate(result):
                if len(row_data) == 1:
                    self.users_list.addItem(
                        QtWidgets.QListWidgetItem(str(row_number + 1) + ": " + row_data[0]))

    # function that reloads/ refreshes data into the application
    def reload_data(self):
        if self.logs_and_users.currentIndex() == 0:
            self.load_history_logs()
        elif self.logs_and_users.currentIndex() == 1:
            self.load_users_list()
            self.load_users_logs()

    # function that loads the history logs of a user that have been fetched from the database into a table
    def load_users_logs(self):
        # loading history_logs (regarding a selected users) that have been fetched from the database
        self.users_logs_table.clear()
        self.users_logs_table.setRowCount(0)
        self.users_logs_table.setColumnCount(0)

        selected_user = self.users_list.currentItem()
        if selected_user:
            selected_user = selected_user.text()[3:]
            result = get_users_history_logs(selected_user)
        else:
            result = ''
        if len(result) == 0:
            self.users_logs_table.insertRow(0)
            self.users_logs_table.insertColumn(0)
            item = QtWidgets.QTableWidgetItem("No history logs for the selected user.")
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable & ~QtCore.Qt.ItemIsSelectable)
            self.users_logs_table.setItem(0, 0, item)
        else:
            for row_number, row_data in enumerate(result):
                self.users_logs_table.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    if row_number == 0:
                        self.users_logs_table.insertColumn(column_number)
                    item = QtWidgets.QTableWidgetItem(str(data))
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                    self.users_logs_table.setItem(row_number, column_number, item)
            self.users_logs_table.setHorizontalHeaderLabels(["Action", "Timestamp", "Hostname", "IP Address"])

    # the function that triggers the action for the "Change username" button
    def change_username_button_action(self):
        selected_user = self.users_list.currentItem()
        if selected_user:
            result = selected_user.text()[3:]
        else:
            result = ''
        if len(result) == 0:
            message = QtWidgets.QMessageBox()
            message.setIcon(QtWidgets.QMessageBox.Critical)
            font = QtGui.QFont()
            font.setFamily("Bahnschrift SemiCondensed")
            message.setFont(font)
            message.setWindowTitle("Sorry, something went wrong")
            message.setText("You haven't selected any user from the list!")
            message.exec_()
        else:
            message = QtWidgets.QMessageBox()
            message.setIcon(QtWidgets.QMessageBox.Question)
            font = QtGui.QFont()
            font.setFamily("Bahnschrift SemiCondensed")
            message.setFont(font)
            message.setWindowTitle("Change username")
            message.setText("Are you sure you want to change " + result + "'s username? \n\n" + result +
                            " might be denied access.")
            message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            message.setDefaultButton(QtWidgets.QMessageBox.No)
            value = message.exec_()  # 0x00004000 is associated with Yes, 0x00010000 is associated with No
            if value == 0x00004000:  # if the administrator confirms
                dialog = QtWidgets.QInputDialog()
                new_username, ok = dialog.getText(dialog, "New username",
                                                  "Please enter the new username for " + result)
                if ok and new_username:
                    change_username(result, new_username)

    # the function that triggers the action for the "Change password" button
    def change_password_button_action(self):
        selected_user = self.users_list.currentItem()
        if selected_user:
            result = selected_user.text()[3:]
        else:
            result = ''
        if len(result) == 0:
            message = QtWidgets.QMessageBox()
            message.setIcon(QtWidgets.QMessageBox.Critical)
            font = QtGui.QFont()
            font.setFamily("Bahnschrift SemiCondensed")
            message.setFont(font)
            message.setWindowTitle("Sorry, something went wrong")
            message.setText("You haven't selected any user from the list!")
            message.exec_()
        else:
            message = QtWidgets.QMessageBox()
            message.setIcon(QtWidgets.QMessageBox.Question)
            font = QtGui.QFont()
            font.setFamily("Bahnschrift SemiCondensed")
            message.setFont(font)
            message.setWindowTitle("Change password")
            message.setText("Are you sure you want to change " + result + "'s password? \n\n " + result +
                            " might be denied access and all the behavioural data associated with this account "
                            "will be lost.")
            message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            message.setDefaultButton(QtWidgets.QMessageBox.No)
            value = message.exec_()  # 0x00004000 is associated with Yes, 0x00010000 is associated with No
            if value == 0x00004000:  # if the administrator confirms
                dialog = QtWidgets.QInputDialog()
                new_password, ok = dialog.getText(dialog, "New password", "Please enter the new password for " +
                                                  result, echo=QtWidgets.QLineEdit.Password)
                if ok and new_password:
                    # todo
                    system_change_password(result, new_password)

    # the function that triggers the action for the "Delete user" button
    def delete_user_button_action(self):
        selected_user = self.users_list.currentItem()
        if selected_user:
            result = selected_user.text()[3:]
        else:
            result = ''
        if len(result) == 0:
            message = QtWidgets.QMessageBox()
            message.setIcon(QtWidgets.QMessageBox.Critical)
            font = QtGui.QFont()
            font.setFamily("Bahnschrift SemiCondensed")
            message.setFont(font)
            message.setWindowTitle("Sorry, something went wrong")
            message.setText("You haven't selected any user from the list!")
            message.exec_()
        else:
            message = QtWidgets.QMessageBox()
            message.setIcon(QtWidgets.QMessageBox.Question)
            font = QtGui.QFont()
            font.setFamily("Bahnschrift SemiCondensed")
            message.setFont(font)
            message.setWindowTitle("Delete account")
            message.setText("Are you sure you want to delete " + result + "'s account? \n\n" + result +
                            " will be denied access and all history logs and behavioural data associated with "
                            "this account will be lost. Please note that this action is not reversible.")
            message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            message.setDefaultButton(QtWidgets.QMessageBox.No)
            value = message.exec_()  # 0x00004000 is associated with Yes, 0x00010000 is associated with No
            if value == 0x00004000:  # if the administrator confirms
                delete_account(result)

    # the function that triggers the action for the "Delete old authentication patterns" button
    @staticmethod
    def delete_old_authentication_patterns_button_action():
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Question)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        message.setFont(font)
        message.setWindowTitle("Delete old authentication patterns")
        message.setText("Are you sure you want to delete all old authentication patterns? \n\nA pattern is considered "
                        "old if 90 days have passed since it was collected or there are more than 750 newer "
                        "patterns for the same user. This might allow some users to connect using only their "
                        "password, leaving their account at risk. Please note that this action is not reversible.")
        message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message.setDefaultButton(QtWidgets.QMessageBox.No)
        value = message.exec_()  # 0x00004000 is associated with Yes, 0x00010000 is associated with No
        if value == 0x00004000:  # if the administrator confirms
            delete_old_authentication_patterns()

    # the function that triggers the action for the "Delete old logs" button
    @staticmethod
    def delete_old_logs_button_action():
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Question)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        message.setFont(font)
        message.setWindowTitle("Delete old logs")
        message.setText("Are you sure you want to delete all old history logs? \n\nA log is considered old if 2 years "
                        "have passed since it was collected. Please note that this action is not reversible.")
        message.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message.setDefaultButton(QtWidgets.QMessageBox.No)
        value = message.exec_()  # 0x00004000 is associated with Yes, 0x00010000 is associated with No
        if value == 0x00004000:  # if the administrator confirms
            start_new_thread(delete_old_history_logs, ())


# continuously accepting connections from clients
def accept_connections():
    while 1:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.bind((listen_addr, listen_port))
            # waiting for connections
            socket_tcp.listen(101)
            # establish connection with a client
            connection, addr = socket_tcp.accept()
            # starting a new conversation thread with the new client
            start_new_thread(client, (connection,))


# teaching the server how to react when it connects to a client
def client(connection):
    with connection:
        print('Connected to client')
        try:
            while True:
                data = connection.recv(4096)
                if data:
                    data = eval(data.decode('utf-8'))
                    print(data)
                    if data[0] == "create_account":
                        # print("I have to create an account")
                        taken_username = check_if_user_exists(data[1])
                        if taken_username == True:
                            connection.send(b'username_taken')
                        else:
                            create_new_account(data[1], data[2], data[3], data[4])
                            create_biometrics_table(data[1])
                            connection.send(b'success')
                        break
                    elif data[0] == "insert_behavioural_data":
                        # print("I have to insert some behavioural data")
                        insert_behavioural_data(data[1], data[2], data[3][0], data[3][1], data[3][2], data[3][3],
                                                data[3][4], data[3][5], data[3][6], data[3][7], data[3][8], data[3][9],
                                                data[3][10], data[3][11], data[3][12], data[3][13], data[3][14])
                        connection.send(b'success')
                    elif data[0] == "verify_credentials":
                        # print("I have to verify some credentials")
                        if verify_credentials(data[1], data[2], data[3], data[4], False):
                            connection.send(b'valid')
                        else:
                            connection.send(b'invalid')
                    elif data[0] == "how_much_data":
                        # print("I have to tell a client how much data I own about a user")
                        how_much_data = str(count_biometrics(data[1]))
                        connection.send(how_much_data.encode("utf-8"))
                    elif data[0] == "change_password":
                        # print("I have to change a password")
                        if not verify_credentials(data[1], data[2], data[4], data[5], False):
                            connection.send(b'invalid')
                        else:
                            insert_log(data[1], "requested a change of password", data[4], data[5])
                            if not change_password(data[1], data[2], data[3]):
                                connection.send(b'unknown')
                            else:
                                connection.send(b'success')
                    elif data[0] == "verify_behavioural_data":
                        print("I have to verify behavioural data")
                        result = verify_behavioural_data(data[1], data[2], data[5])
                        if result == True:
                            connection.send(b'valid')
                        elif result == False:
                            insert_log(data[1], "failed behavioural authentication", data[3], data[4])
                            connection.send(b'invalid')
                        elif result == "wrong_password":
                            connection.send(b'ignore')
                    break
        except ConnectionResetError:
            pass
        finally:
            print("Closed connection")
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()


# data needed for connecting to the database
def connect():
    database = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="Welcome123$",
        ssl_ca="C:/ProgramData/MySQL/MySQL Server 8.0/Data/ca.pem",
        ssl_cert="C:/ProgramData/MySQL/MySQL Server 8.0/Data/client-cert.pem",
        ssl_key="C:/ProgramData/MySQL/MySQL Server 8.0/Data/client-key.pem",
        database="authentication_system"
    )
    return database


# function used to create the database used for the authentication system
def creating_database():
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute("CREATE DATABASE authentication_system")
    my_cursor.close()
    database.close()


# function used to create the two tables used for the authentication system
def creating_tables():
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute("CREATE TABLE IF NOT EXISTS users_credentials(username VARCHAR(255) PRIMARY KEY, "
                      "password VARBINARY(480) NOT NULL, last_change DATE NOT NULL)")
    my_cursor.execute("CREATE TABLE IF NOT EXISTS history_logs(username VARCHAR(255), action VARCHAR(255), "
                      "timestamp TIMESTAMP, hostname VARCHAR(50), ip_address VARCHAR(50))")
    my_cursor.close()
    database.close()


# function used to fetch system's users from the database
def get_users():
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute("SELECT username FROM users_credentials ORDER BY username")
    data = my_cursor.fetchall()
    my_cursor.close()
    database.close()
    insert_log("System", "fetched information about users", "Authentication System Manager", "")
    return data


# function used to fetch history logs from the database
def get_history_logs():
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute(
        "SELECT username, action, timestamp, hostname, ip_address FROM history_logs ORDER BY timestamp DESC")
    data = my_cursor.fetchall()
    my_cursor.close()
    database.close()
    insert_log("System", "fetched information about history logs", "Authentication System Manager", "")
    return data


# function used to fetch history logs regarding a specific user from the database
def get_users_history_logs(username):
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute(
        "SELECT action, timestamp, hostname, ip_address FROM history_logs WHERE username = %s ORDER BY timestamp DESC",
        (username,))
    data = my_cursor.fetchall()
    my_cursor.close()
    database.close()
    insert_log("System", "fetched information about " + username + "'s history logs", "Authentication System Manager",
               "")
    return data


# function used to insert a new log into the database
def insert_log(user, action, hostname, ip_address):
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute("INSERT INTO history_logs VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)",
                      (user, action, hostname, ip_address))
    my_cursor.close()
    database.commit()
    database.close()


# function that checks is a username is taken
def check_if_user_exists(user):
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute("SELECT COUNT(*) FROM users_credentials WHERE username = %s", (user,))
    data = my_cursor.fetchall()
    my_cursor.close()
    database.commit()
    database.close()
    return data[0][0] > 0


# function that creates a new account
def create_new_account(username, password, hostname, ip_address):
    database = connect()
    my_cursor = database.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        my_cursor.execute("INSERT INTO users_credentials VALUES (%s, %s, CURRENT_TIMESTAMP)", (username, hashed_password))
    except mysql.connector.IntegrityError:
        my_cursor.close()
        database.close()
        return False
    my_cursor.close()
    database.commit()
    database.close()
    insert_log(username, 'created a new account', hostname, ip_address)
    return True


# function to create a biometrics table for a selected user
def create_biometrics_table(username):
    database = connect()
    my_cursor = database.cursor()
    table_name = "biometrics_" + username
    my_cursor.execute("CREATE TABLE {table} (timestamp TIMESTAMP, hold_left VARBINARY(1000), hold_right "
                      "VARBINARY(1000), hold_space VARBINARY(1000), pp_left_left VARBINARY(1000), "
                      "pp_left_right VARBINARY(1000), pp_right_left VARBINARY(1000), pp_right_right VARBINARY(1000), "
                      "rr_left_left VARBINARY(1000), rr_left_right VARBINARY(1000), rr_right_left VARBINARY(1000), "
                      "rr_right_right VARBINARY(1000), pr_left_left VARBINARY(1000), pr_left_right VARBINARY(1000), "
                      "pr_right_left VARBINARY(1000), pr_right_right VARBINARY(1000))".format(table=table_name))
    my_cursor.close()
    database.commit()
    database.close()


# function used to insert behavioural data in the user's personal table
def insert_behavioural_data(username, password, hold_left, hold_right, hold_space, pp_left_left, pp_left_right,
                            pp_right_left, pp_right_right, rr_left_left, rr_left_right, rr_right_left, rr_right_right,
                            pr_left_left, pr_left_right, pr_right_left, pr_right_right):
    database = connect()
    my_cursor = database.cursor()
    table_name = "biometrics_" + username
    my_cursor.execute("INSERT INTO {table} VALUES (CURRENT_TIMESTAMP, AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), "
                      "AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))), AES_ENCRYPT(%s, UNHEX(SHA2(%s, 256))))"
                      .format(table=table_name), (hold_left, password, hold_right, password, hold_space, password,
                                                  pp_left_left, password, pp_left_right, password, pp_right_left,
                                                  password, pp_right_right, password, rr_left_left, password,
                                                  rr_left_right, password, rr_right_left, password, rr_right_right,
                                                  password, pr_left_left, password, pr_left_right, password,
                                                  pr_right_left, password, pr_right_right, password))
    my_cursor.close()
    database.commit()
    database.close()


# function used to verify credentials
def verify_credentials(username, password, hostname, ip_address, silence_flag):
    database = connect()
    my_cursor = database.cursor()
    my_cursor.execute("SELECT password FROM users_credentials WHERE username = %s", (username,))
    data = my_cursor.fetchall()
    if len(data) == 0:
        if silence_flag is False:
            insert_log(username, "tried to connect to an account that doesn't exist", hostname, ip_address)
        return False
    data = data[0][0]
    valid = bcrypt.checkpw(password.encode("utf-8"), data.encode("utf-8"))
    my_cursor.close()
    database.close()
    if silence_flag is False:
        if valid:
            insert_log(username, "logged in using password", hostname, ip_address)
        else:
            insert_log(username, "tried to log in using the wrong password", hostname, ip_address)
    return valid


# function that counts how many biometric data there is in the database about a specific user
def count_biometrics(username):
    database = connect()
    my_cursor = database.cursor()
    table_name = "biometrics_" + username
    my_cursor.execute("SELECT COUNT(*) FROM {table}".format(table=table_name))
    data = my_cursor.fetchall()
    data = data[0][0]
    my_cursor.close()
    database.close()
    return data


# function that changes a user's password (from the client side)
def change_password(username, old_password, new_password):
    database = connect()
    my_cursor = database.cursor()

    # decrypting all biometrics from the user's table and encrypting it again with the new password
    table_name = "biometrics_" + username
    try:
        my_cursor.execute("UPDATE {table} SET hold_left = "
                          "AES_ENCRYPT(AES_DECRYPT(hold_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "hold_right = "
                          "AES_ENCRYPT(AES_DECRYPT(hold_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "hold_space = "
                          "AES_ENCRYPT(AES_DECRYPT(hold_space, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pp_left_left = "
                          "AES_ENCRYPT(AES_DECRYPT(pp_left_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pp_left_right = "
                          "AES_ENCRYPT(AES_DECRYPT(pp_left_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pp_right_left = "
                          "AES_ENCRYPT(AES_DECRYPT(pp_right_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pp_right_right = "
                          "AES_ENCRYPT(AES_DECRYPT(pp_right_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "rr_left_left = "
                          "AES_ENCRYPT(AES_DECRYPT(rr_left_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "rr_left_right = "
                          "AES_ENCRYPT(AES_DECRYPT(rr_left_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "rr_right_left = "
                          "AES_ENCRYPT(AES_DECRYPT(rr_right_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "rr_right_right = "
                          "AES_ENCRYPT(AES_DECRYPT(rr_right_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pr_left_left = "
                          "AES_ENCRYPT(AES_DECRYPT(pr_left_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pr_left_right = "
                          "AES_ENCRYPT(AES_DECRYPT(pr_left_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pr_right_left = "
                          "AES_ENCRYPT(AES_DECRYPT(pr_right_left, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256))), "
                          "pr_right_right = "
                          "AES_ENCRYPT(AES_DECRYPT(pr_right_right, UNHEX(SHA2(%s, 256))), UNHEX(SHA2(%s, 256)))"
                          .format(table=table_name),
                          (old_password, new_password, old_password, new_password, old_password, new_password,
                           old_password, new_password, old_password, new_password, old_password, new_password,
                           old_password, new_password, old_password, new_password, old_password, new_password,
                           old_password, new_password, old_password, new_password, old_password, new_password,
                           old_password, new_password, old_password, new_password, old_password, new_password))
    except mysql.connector.Error:
        my_cursor.close()
        database.close()
        insert_log("System", "failed changing " + username + "'s password", "Authentication System Manager", "")
        return False

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    try:
        my_cursor.execute("UPDATE users_credentials SET password = %s WHERE username = %s", (hashed_password, username))
    except mysql.connector.Error:
        my_cursor.close()
        database.rollback()
        database.close()
        insert_log("System", "failed changing " + username + "'s password", "Authentication System Manager", "")
        return False
    my_cursor.close()
    database.commit()
    database.close()
    insert_log("System", "changed " + username + "'s password", "Authentication System Manager", "")
    return True


def change_username(old_username, new_username):
    database = connect()
    my_cursor = database.cursor()
    old_table_name = "biometrics_" + old_username
    new_table_name = "biometrics_" + new_username
    try:
        my_cursor.execute("RENAME TABLE {old_table} TO {new_table}".format(old_table=old_table_name,
                                                                           new_table=new_table_name))
        my_cursor.execute("UPDATE users_credentials SET username = %s WHERE username = %s", (new_username,
                                                                                             old_username))
        my_cursor.execute("UPDATE history_logs SET username = %s WHERE username = %s", (new_username, old_username))
    except mysql.connector.Error:
        insert_log("System", "failed changing " + old_username + "'s username", "Authentication System Manager", "")
        my_cursor.close()
        database.rollback()
        database.close()
        return False
    my_cursor.close()
    database.commit()
    database.close()
    insert_log("System", "changed " + old_username + "'s username into " + new_username,
               "Authentication System Manager", "")
    return True


# function that changes a user's password (from the server's side)
def system_change_password(username, new_password):
    database = connect()
    my_cursor = database.cursor()

    # deleting all biometrics from the user's table
    table_name = "biometrics_" + username
    try:
        my_cursor.execute("DELETE FROM {table} WHERE timestamp < CURRENT_TIMESTAMP".format(table=table_name))
    except mysql.connector.Error:
        insert_log("System", "failed changing " + username + "'s password", "Authentication System Manager", "")
        my_cursor.close()
        database.rollback()
        database.close()
        return False

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    try:
        my_cursor.execute("UPDATE users_credentials SET password = %s WHERE username = %s", (hashed_password, username))
    except mysql.connector.Error:
        my_cursor.close()
        database.rollback()
        database.close()
        insert_log("System", "failed changing " + username + "'s password", "Authentication System Manager", "")
        return False
    my_cursor.close()
    database.commit()
    database.close()
    insert_log("System", "changed " + username + "'s password", "Authentication System Manager", "")
    return True


# function that deletes a user account
def delete_account(username):
    database = connect()
    my_cursor = database.cursor()
    table_name = "biometrics_" + username
    try:
        my_cursor.execute("DELETE FROM users_credentials WHERE username = %s", (username,))
        my_cursor.execute("DELETE FROM history_logs WHERE username = %s", (username,))
        my_cursor.execute("DROP TABLE {table}".format(table=table_name))
    except mysql.connector.Error:
        insert_log("System", "failed deleting " + username + "'s account", "Authentication System Manager", "")
        my_cursor.close()
        database.rollback()
        database.close()
        return False
    my_cursor.close()
    database.commit()
    database.close()
    insert_log("System", "deleted " + username + "'s account", "Authentication System Manager", "")
    return True


# function that limits the number of patterns at 750 per user and deletes everything that's more than 60 days old
def delete_old_authentication_patterns():
    database = connect()
    my_cursor = database.cursor()
    users = get_users()
    for user in users:
        table_name = "biometrics_" + user[0]
        number_of_patterns = count_biometrics(user[0]) - 750
        if number_of_patterns > 0:
            try:
                my_cursor.execute('DELETE FROM {table} ORDER BY timestamp asc LIMIT %s'.format(table=table_name),
                                  (number_of_patterns,))
            except mysql.connector.Error:
                pass
        try:
            my_cursor.execute('DELETE FROM {table} WHERE timestamp < (SELECT CURRENT_TIMESTAMP - '
                              'INTERVAL 60 DAY FROM dual)'.format(table=table_name))
        except mysql.connector.Error:
            pass
    my_cursor.close()
    database.commit()
    database.close()
    insert_log("System", "deleted old authentication patterns", "Authentication System Manager", "")


# function that deletes history logs that are more than 2 years old
def delete_old_history_logs():
    database = connect()
    my_cursor = database.cursor()
    try:
        my_cursor.execute('DELETE FROM history_logs WHERE timestamp < (SELECT CURRENT_TIMESTAMP - '
                          'INTERVAL 2 YEAR FROM dual)')
    except mysql.connector.Error:
        pass
    my_cursor.close()
    database.commit()
    database.close()
    insert_log("System", "deleted old history logs", "Authentication System Manager", "")


def verify_behavioural_data(username, password, data):
    if verify_credentials(username, password, "", "", True) is False:
        return "wrong_password"
    database = connect()
    my_cursor = database.cursor()
    table_name = "biometrics_" + username
    try:
        my_cursor.execute("SELECT AES_DECRYPT(hold_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(hold_right, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(hold_space, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pp_left_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pp_left_right, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pp_right_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pp_right_right, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(rr_left_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(rr_left_right, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(rr_right_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(rr_right_right, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pr_left_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pr_left_right, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pr_right_left, UNHEX(SHA2(%s, 256))), "
                          "AES_DECRYPT(pr_right_right, UNHEX(SHA2(%s, 256))) "
                          "FROM {table} ORDER BY TIMESTAMP desc LIMIT 750"
                          .format(table=table_name), (password, password, password, password, password, password,
                                                      password, password, password, password, password, password,
                                                      password, password, password))
    except mysql.connector.Error:
        pass
    train_data = my_cursor.fetchall()
    my_cursor.close()
    database.close()
    for i in range(0, len(train_data)):
        train_data[i] = list(train_data[i])
        for j in range(0, len(train_data[i])):
            train_data[i][j] = float(train_data[i][j])
    train_data = np.asarray(train_data)
    test_data = [data]
    test_data = np.asarray(test_data)
    if len(train_data) < 100:
        result = my_svm_result(train_data, test_data)
    else:
        result = my_lof_result(train_data, test_data)
    if result == 1:
        insert_behavioural_data(username, password, data[0], data[1], data[2], data[3], data[4], data[5], data[6],
                                data[7], data[8], data[9], data[10], data[11], data[12], data[13], data[14])
    return result == 1


def my_svm_result(train_data, test_data):
    sc = MinMaxScaler()
    train_data = sc.fit_transform(train_data)
    test_data = sc.transform(test_data)
    my_svm = OneClassSVM(kernel='rbf', gamma=0.15, nu=1 / len(train_data))
    my_svm.fit(train_data)
    result = my_svm.predict(test_data)
    return result[0]


def my_lof_result(train_data, test_data):
    sc = StandardScaler()
    train_data = sc.fit_transform(train_data)
    test_data = sc.transform(test_data)
    lof = LocalOutlierFactor(n_neighbors=int(len(train_data) / 5), novelty=True, contamination=1 / len(train_data),
                             algorithm='auto', metric='sqeuclidean')
    lof.fit(train_data)
    result = lof.predict(test_data)
    return result[0]


def create_dummy_accounts():
    import random
    import os
    import pandas as pd
    for i in range(1, 248):
        username = 'TestUser' + str(i)
        password = 'user' + str(i)
        hostname = 'TestUser' + str(i) + "'s computer"
        ip_address = "192.168." + str(random.randrange(0, 256)) + "." + str(i)
        if os.path.exists('test_data/user' + str(i) + '.csv'):
            create_new_account(username, password, hostname, ip_address)
            create_biometrics_table(username)
            data = pd.read_csv('test_data/user' + str(i) + '.csv', header=None, encoding='unicode_escape')
            data = data.to_numpy()
            for j in data:
                insert_behavioural_data(username, password, j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7],
                                        j[8], j[9], j[10], j[11], j[12], j[13], j[14])


# main function, where all the magic happens and everything starts making sense (ha-ha)
def main():
    # creating_database()
    creating_tables()

    # displaying GUI
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    UI = Window(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


# create_dummy_accounts()
main()
