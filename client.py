import sys
import socket
import ssl
import threading
import keylogger
import dataExtractor
import os
import re
from PyQt5 import QtCore, QtGui, QtWidgets
from multiprocessing import Process, Manager

# information about server, client & ssl certificates
host_addr = '127.0.0.1'
host_port = 8082
server_sni_hostname = 'example.com'
server_cert = 'server.crt'
client_cert = 'client.crt'
client_key = 'client.key'

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)
# RESTART = True


class Window(QtCore.QObject):
    finished_thread = QtCore.pyqtSignal()
    finished_thread_offline_server = QtCore.pyqtSignal()
    forced_password_change = QtCore.pyqtSignal()
    username = ""

    # noinspection PyArgumentList
    def __init__(self, MainWindow, restart_flag):
        from functools import partial
        super(Window, self).__init__()
        erase_residual_data()

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
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        font.setPointSize(12)
        MainWindow.setFont(font)
        MainWindow.setWindowTitle("Authentication System Client")
        # MainWindow.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        # main widget
        self.main_widget = QtWidgets.QWidget(MainWindow)
        self.main_widget.setObjectName("main_widget")

        ####################################
        # login page
        self.login_page_widget = QtWidgets.QWidget(self.main_widget)
        self.login_page_widget.setGeometry(QtCore.QRect(0, 0, 960, 669))
        self.login_page_widget.setObjectName("login_page_widget")

        # credentials group (username, password)
        self.credentials_group = QtWidgets.QGroupBox(self.login_page_widget)
        self.credentials_group.setGeometry(QtCore.QRect(180, 180, 571, 181))
        self.credentials_group.setAlignment(QtCore.Qt.AlignCenter)
        self.credentials_group.setObjectName("credentials_group")
        self.username_input = QtWidgets.QLineEdit(self.credentials_group)
        self.username_input.setGeometry(QtCore.QRect(170, 50, 311, 31))
        self.username_input.setText("")
        self.username_input.setObjectName("username_input")
        self.username_label = QtWidgets.QLabel(self.credentials_group)
        self.username_label.setGeometry(QtCore.QRect(70, 50, 161, 31))
        self.username_label.setObjectName("username_label")
        self.password_label = QtWidgets.QLabel(self.credentials_group)
        self.password_label.setGeometry(QtCore.QRect(70, 110, 91, 31))
        self.password_label.setObjectName("password_label")
        self.password_input = QtWidgets.QLineEdit(self.credentials_group)
        self.password_input.setGeometry(QtCore.QRect(170, 110, 311, 31))
        self.password_input.setText("")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setObjectName("password_input")

        # instructions and disclaimer about signing in or creating a new account
        self.instructions = QtWidgets.QLabel(self.login_page_widget)
        self.instructions.setGeometry(QtCore.QRect(100, 50, 751, 81))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.instructions.setFont(font)
        self.instructions.setTextFormat(QtCore.Qt.AutoText)
        self.instructions.setAlignment(QtCore.Qt.AlignJustify | QtCore.Qt.AlignVCenter)
        self.instructions.setWordWrap(True)
        self.instructions.setObjectName("instructions")
        self.disclaimer = QtWidgets.QLabel(self.login_page_widget)
        self.disclaimer.setGeometry(QtCore.QRect(100, 540, 751, 81))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.disclaimer.setFont(font)
        self.disclaimer.setTextFormat(QtCore.Qt.AutoText)
        self.disclaimer.setAlignment(QtCore.Qt.AlignJustify | QtCore.Qt.AlignVCenter)
        self.disclaimer.setWordWrap(True)
        self.disclaimer.setObjectName("disclaimer")

        # buttons for logging in & creating a new account
        self.login_button = QtWidgets.QPushButton(self.login_page_widget)
        self.login_button.setGeometry(QtCore.QRect(420, 390, 93, 28))
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.log_in)
        self.new_account_button = QtWidgets.QPushButton(self.login_page_widget)
        self.new_account_button.setGeometry(QtCore.QRect(370, 440, 201, 31))
        self.new_account_button.setObjectName("new_account_button")
        self.new_account_button.clicked.connect(self.switch_to_create_account_page)

        """self.credentials_group.raise_()
        self.disclaimer.raise_()
        self.login_button.raise_()
        self.new_account_button.raise_()
        self.instructions.raise_()"""

        ####################################
        # welcome page
        self.welcome_page_widget = QtWidgets.QWidget(self.main_widget)
        self.welcome_page_widget.setGeometry(QtCore.QRect(0, 0, 960, 669))
        self.welcome_page_widget.setObjectName("welcome_page_widget")
        self.welcome_page_widget.setVisible(False)
        self.welcome_label = QtWidgets.QLabel(self.welcome_page_widget)
        self.welcome_label.setGeometry(QtCore.QRect(260, 150, 431, 151))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.welcome_label.setFont(font)
        self.welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        self.welcome_label.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.welcome_label.setObjectName("welcome_label")

        # button for changing password
        self.change_password_button = QtWidgets.QPushButton(self.welcome_page_widget)
        self.change_password_button.setGeometry(QtCore.QRect(370, 400, 201, 31))
        self.change_password_button.setObjectName("change_password_button")
        self.change_password_button.clicked.connect(self.switch_to_change_password_page)

        # button for logging out
        self.log_out_button = QtWidgets.QPushButton(self.welcome_page_widget)
        self.log_out_button.setGeometry(QtCore.QRect(370, 480, 201, 31))
        self.log_out_button.setObjectName("log_out_button")
        self.log_out_button.clicked.connect(partial(self.log_out, restart_flag))

        ####################################
        # new account page
        self.new_account_page_widget = QtWidgets.QWidget(self.main_widget)
        self.new_account_page_widget.setVisible(False)
        self.new_account_page_widget.setGeometry(QtCore.QRect(0, 0, 960, 669))
        self.new_account_page_widget.setObjectName("new_account_page_widget")

        # disclaimer
        self.another_disclaimer = QtWidgets.QLabel(self.new_account_page_widget)
        self.another_disclaimer.setGeometry(QtCore.QRect(100, 540, 751, 81))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.another_disclaimer.setFont(font)
        self.another_disclaimer.setTextFormat(QtCore.Qt.AutoText)
        self.another_disclaimer.setAlignment(QtCore.Qt.AlignJustify | QtCore.Qt.AlignVCenter)
        self.another_disclaimer.setWordWrap(True)
        self.another_disclaimer.setObjectName("another_disclaimer")

        # credentials (username & password)
        self.new_account_credentials = QtWidgets.QGroupBox(self.new_account_page_widget)
        self.new_account_credentials.setGeometry(QtCore.QRect(180, 110, 571, 251))
        self.new_account_credentials.setAlignment(QtCore.Qt.AlignCenter)
        self.new_account_credentials.setObjectName("new_account_credentials")
        self.new_username_input = QtWidgets.QLineEdit(self.new_account_credentials)
        self.new_username_input.setGeometry(QtCore.QRect(170, 50, 311, 31))
        self.new_username_input.setText("")
        self.new_username_input.setObjectName("new_username_input")
        self.new_username_label = QtWidgets.QLabel(self.new_account_credentials)
        self.new_username_label.setGeometry(QtCore.QRect(70, 50, 161, 31))
        self.new_username_label.setObjectName("new_username_label")
        self.new_password_label = QtWidgets.QLabel(self.new_account_credentials)
        self.new_password_label.setGeometry(QtCore.QRect(70, 150, 91, 31))
        self.new_password_label.setObjectName("new_password_label")
        self.new_password_input = QtWidgets.QLineEdit(self.new_account_credentials)
        self.new_password_input.setGeometry(QtCore.QRect(170, 150, 311, 31))
        self.new_password_input.setText("")
        self.new_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.new_password_input.setObjectName("new_password_input")
        self.username_suggestion = QtWidgets.QLabel(self.new_account_credentials)
        self.username_suggestion.setGeometry(QtCore.QRect(210, 90, 271, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.username_suggestion.setFont(font)
        self.username_suggestion.setObjectName("username_suggestion")
        self.password_suggestion = QtWidgets.QLabel(self.new_account_credentials)
        self.password_suggestion.setGeometry(QtCore.QRect(150, 190, 331, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.password_suggestion.setFont(font)
        self.password_suggestion.setObjectName("password_suggestion")
        self.passphrase_suggestion = QtWidgets.QLabel(self.new_account_credentials)
        self.passphrase_suggestion.setGeometry(QtCore.QRect(220, 210, 261, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.passphrase_suggestion.setFont(font)
        self.passphrase_suggestion.setObjectName("passphrase_suggestion")

        # button for creating a new account
        self.create_account_button = QtWidgets.QPushButton(self.new_account_page_widget)
        self.create_account_button.setGeometry(QtCore.QRect(360, 390, 221, 28))
        self.create_account_button.setObjectName("create_account_button")
        self.create_account_button.clicked.connect(self.create_new_account)

        # button for logging in
        self.login_instead_button = QtWidgets.QPushButton(self.new_account_page_widget)
        self.login_instead_button.setGeometry(QtCore.QRect(410, 470, 121, 31))
        self.login_instead_button.setObjectName("login_instead_button")
        self.login_instead_button.clicked.connect(self.switch_to_login_page)
        self.login_instead_suggestion = QtWidgets.QLabel(self.new_account_page_widget)
        self.login_instead_suggestion.setGeometry(QtCore.QRect(370, 450, 201, 16))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.login_instead_suggestion.setFont(font)
        self.login_instead_suggestion.setAlignment(QtCore.Qt.AlignCenter)
        self.login_instead_suggestion.setObjectName("login_instead_suggestion")

        # fetching biometric data page (instructions, textbox)
        self.initial_biometric_data_page_widget = QtWidgets.QWidget(self.main_widget)
        self.initial_biometric_data_page_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setGeometry(QtCore.QRect(0, 0, 960, 669))
        self.initial_biometric_data_page_widget.setObjectName("initial_biometric_data_page_widget")
        self.last_step_info = QtWidgets.QLabel(self.initial_biometric_data_page_widget)
        self.last_step_info.setGeometry(QtCore.QRect(120, 50, 721, 231))
        self.last_step_info.setAlignment(QtCore.Qt.AlignCenter)
        self.last_step_info.setWordWrap(True)
        self.last_step_info.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.last_step_info.setObjectName("last_step_info")
        self.text_box = QtWidgets.QTextEdit(self.initial_biometric_data_page_widget)
        self.text_box.setGeometry(QtCore.QRect(130, 290, 691, 261))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.text_box.setFont(font)
        self.text_box.setAccessibleDescription("")
        self.text_box.setObjectName("text_box")

        ####################################
        # change password page
        self.change_password_widget = QtWidgets.QWidget(self.main_widget)
        self.change_password_widget.setGeometry(QtCore.QRect(0, 0, 960, 669))
        self.change_password_widget.setObjectName("change_password_widget")
        self.change_password_widget.setVisible(False)

        # the credentials required to change the password
        self.new_password_credentials = QtWidgets.QGroupBox(self.change_password_widget)
        self.new_password_credentials.setGeometry(QtCore.QRect(190, 120, 571, 381))
        self.new_password_credentials.setAlignment(QtCore.Qt.AlignCenter)
        self.new_password_credentials.setObjectName("new_password_credentials")

        # the current credentials (username plus password)
        self.current_username_input = QtWidgets.QLineEdit(self.new_password_credentials)
        self.current_username_input.setGeometry(QtCore.QRect(170, 50, 311, 31))
        self.current_username_input.setText("")
        self.current_username_input.setObjectName("current_username_input")
        self.current_username_label = QtWidgets.QLabel(self.new_password_credentials)
        self.current_username_label.setGeometry(QtCore.QRect(67, 50, 81, 31))
        self.current_username_label.setObjectName("current_username_label")
        self.current_password_label = QtWidgets.QLabel(self.new_password_credentials)
        self.current_password_label.setGeometry(QtCore.QRect(41, 130, 111, 31))
        self.current_password_label.setObjectName("current_password_label")
        self.current_password_input = QtWidgets.QLineEdit(self.new_password_credentials)
        self.current_password_input.setGeometry(QtCore.QRect(170, 130, 311, 31))
        self.current_password_input.setText("")
        self.current_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.current_password_input.setObjectName("current_password_input")

        # the new password (& confirmation)
        self.future_password_input = QtWidgets.QLineEdit(self.new_password_credentials)
        self.future_password_input.setGeometry(QtCore.QRect(170, 210, 311, 31))
        self.future_password_input.setText("")
        self.future_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.future_password_input.setObjectName("future_password_input")
        self.confirm_password_input = QtWidgets.QLineEdit(self.new_password_credentials)
        self.confirm_password_input.setGeometry(QtCore.QRect(170, 290, 311, 31))
        self.confirm_password_input.setText("")
        self.confirm_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_password_input.setObjectName("confirm_password_input")
        self.future_password_label = QtWidgets.QLabel(self.new_password_credentials)
        self.future_password_label.setGeometry(QtCore.QRect(33, 210, 111, 31))
        self.future_password_label.setObjectName("future_password_label")
        self.confirm_password_label = QtWidgets.QLabel(self.new_password_credentials)
        self.confirm_password_label.setGeometry(QtCore.QRect(5, 290, 141, 31))
        self.confirm_password_label.setObjectName("confirm_password_label")

        # save changes button
        self.save_password_button = QtWidgets.QPushButton(self.change_password_widget)
        self.save_password_button.setGeometry(QtCore.QRect(630, 510, 201, 41))
        self.save_password_button.setObjectName("save_password_button")
        self.save_password_button.clicked.connect(partial(self.change_password, restart_flag))

        # return button
        self.return_button = QtWidgets.QPushButton(self.change_password_widget)
        self.return_button.setGeometry(QtCore.QRect(120, 510, 201, 41))
        self.return_button.setObjectName("return_button")
        self.return_button.clicked.connect(self.switch_to_welcome_page)

        MainWindow.setCentralWidget(self.main_widget)

        # menu, status bar
        self.menu_bar = QtWidgets.QMenuBar(MainWindow)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 960, 30))
        self.menu_bar.setObjectName("menu_bar")
        self.menu_help = QtWidgets.QMenu(self.menu_bar)
        self.menu_help.setObjectName("menu_help")
        self.menu_bar.addAction(self.menu_help.menuAction())
        MainWindow.setMenuBar(self.menu_bar)
        self.status_bar = QtWidgets.QStatusBar(MainWindow)
        self.status_bar.setObjectName("status_bar")
        MainWindow.setStatusBar(self.status_bar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        threading.Thread(target=trigger_connection, daemon=True).start()
        self.finished_thread.connect(self.show_popup, QtCore.Qt.QueuedConnection)
        self.finished_thread_offline_server.connect(self.show_offline_server_notification, QtCore.Qt.QueuedConnection)
        self.forced_password_change.connect(self.show_forced_password_change_popup, QtCore.Qt.QueuedConnection)

    # noinspection PyArgumentList
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.credentials_group.setTitle(_translate("MainWindow", "Please enter your credentials"))
        self.username_label.setText(_translate("MainWindow", "Username"))
        self.password_label.setText(_translate("MainWindow", "Password"))
        self.instructions.setText(_translate("MainWindow", "To continue using the application, "
                                             + "please verify your credentials or create a new account and complete "
                                             + "any necessary security precautions such as biometric two-factor "
                                             + "authentication before proceeding."))
        self.disclaimer.setText(_translate("MainWindow", "Disclaimer! During the login process, your hostname, "
                                           + "IP address and biometric data may be logged for security purposes, but "
                                           + "they are not disclosed to other parties. If your account is locked or "
                                           + "if you are unable to login, please contact your system administrator."))
        self.login_button.setText(_translate("MainWindow", "LOG IN"))
        self.new_account_button.setText(_translate("MainWindow", "Create a new account"))
        self.welcome_label.setText(_translate("MainWindow", "Welcome to your account!"))
        self.change_password_button.setText(_translate("MainWindow", "Change password"))
        self.log_out_button.setText(_translate("MainWindow", "Log out"))
        self.another_disclaimer.setText(_translate("MainWindow", "Disclaimer! During the login process, your hostname, "
                                                   + "IP address and biometric data may be logged for security "
                                                   + "purposes, but they are not disclosed to other parties. If your "
                                                   + "account is locked or if you are unable to login, please contact "
                                                   + "your system administrator."))
        self.new_account_credentials.setTitle(_translate("MainWindow", "No account yet? Please fill in the form"))
        self.new_username_label.setText(_translate("MainWindow", "Username"))
        self.new_password_label.setText(_translate("MainWindow", "Password"))
        self.username_suggestion.setText(_translate("MainWindow", "We strongly suggest using your own name"))
        self.password_suggestion.setText(
            _translate("MainWindow", "Pick one that\'s easy to remember but hard to guess"))
        self.passphrase_suggestion.setText(
            _translate("MainWindow", "Not good with remembering stuff? Try a passphrase."))
        self.create_account_button.setText(_translate("MainWindow", "CREATE A NEW ACCOUNT"))
        self.login_instead_button.setText(_translate("MainWindow", "Log in instead"))
        self.login_instead_suggestion.setText(_translate("MainWindow", "Oops, I already have an account"))
        self.last_step_info.setText(_translate("MainWindow", "Last step before creating your new account: type "
                                               + "something - anything you want, because we promise it won\'t ever "
                                               + "leave your computer. \n\nIt will help us learn your behaviour - for "
                                               + "security purposes, of course. You can type here (whatever comes "
                                               + "to your mind, or you can even copy this message if you lack "
                                               + "inspiration), or continue your work (writing emails, reports, "
                                               + "messages), because we\'ll work in the background without disturbing "
                                               + "you. This message will go away after we feel like we know you "
                                               + "better and you\'ll be able to log in."))
        self.new_password_credentials.setTitle(
            _translate("MainWindow", "Please fill in the form to change your password"))
        self.current_username_label.setText(_translate("MainWindow", "Username"))
        self.current_password_label.setText(_translate("MainWindow", "Old Password"))
        self.future_password_label.setText(_translate("MainWindow", "New Password"))
        self.confirm_password_label.setText(_translate("MainWindow", "Confirm Password"))
        self.save_password_button.setText(_translate("MainWindow", "Save"))
        self.return_button.setText(_translate("MainWindow", "Return"))
        self.menu_help.setTitle(_translate("MainWindow", "Help"))

    # function that activates the new account page and hides the others
    def switch_to_create_account_page(self):
        erase_residual_data()
        self.login_page_widget.setVisible(False)
        self.welcome_page_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setVisible(False)
        self.change_password_widget.setVisible(False)
        self.new_account_page_widget.setVisible(True)

    # function that activates the login page and hides the others
    def switch_to_login_page(self):
        erase_residual_data()
        self.welcome_page_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setVisible(False)
        self.new_account_page_widget.setVisible(False)
        self.change_password_widget.setVisible(False)
        self.login_page_widget.setVisible(True)

    # function that activates the biometric data fetching page and hides the others
    def switch_to_biometric_data_page(self):
        self.login_page_widget.setVisible(False)
        self.welcome_page_widget.setVisible(False)
        self.new_account_page_widget.setVisible(False)
        self.change_password_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setVisible(True)
        username = self.new_username_input.text()
        password = self.new_password_input.text()
        self.new_username_input.clear()
        self.new_password_input.clear()
        # start_new_thread(initial_monitoring, (username, password, self))
        threading.Thread(target=initial_monitoring, args=(username, password, self), daemon=True).start()

    # function that activates the welcome page and hides the others
    def switch_to_welcome_page(self):
        self.current_username_input.clear()
        self.current_password_input.clear()
        self.future_password_input.clear()
        self.confirm_password_input.clear()
        self.login_page_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setVisible(False)
        self.new_account_page_widget.setVisible(False)
        self.change_password_widget.setVisible(False)
        self.welcome_page_widget.setVisible(True)

    def switch_to_change_password_page(self):
        erase_residual_data()
        self.login_page_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setVisible(False)
        self.new_account_page_widget.setVisible(False)
        self.welcome_page_widget.setVisible(False)
        self.change_password_widget.setVisible(True)
        self.return_button.setVisible(True)

    def switch_to_forced_change_password_page(self):
        erase_residual_data()
        self.login_page_widget.setVisible(False)
        self.initial_biometric_data_page_widget.setVisible(False)
        self.new_account_page_widget.setVisible(False)
        self.welcome_page_widget.setVisible(False)
        self.change_password_widget.setVisible(True)
        self.return_button.setVisible(False)

    # function that creates a new account
    def create_new_account(self):
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Critical)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        message.setFont(font)
        message.setWindowTitle("Sorry, something went wrong")

        if len(self.new_username_input.text()) < 5:
            if len(self.new_username_input.text()) == 0:
                message.setText("The username field can't be empty!")
            else:
                message.setText("The username you picked is too short!")
            message.exec_()
        elif re.match("^[A-Za-z0-9_]*$", self.new_username_input.text()) is None:
            message.setText("The username field includes illegal characters!")
            message.exec_()
        elif len(self.new_password_input.text()) < 10:
            if len(self.new_password_input.text()) == 0:
                message.setText("The password field can't be empty!")
            else:
                if re.match("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{10,}$",
                            self.new_password_input.text()) is None:
                    message.setText("The password you picked is too short and/or easy to guess!")
            message.exec_()
        else:
            response = trigger_creating_account(self.new_username_input.text(), self.new_password_input.text())
            if response is False:
                self.finished_thread_offline_server.emit()
            else:
                if response == 'username_taken':
                    message.setText("The username you picked is already taken!")
                    message.exec_()
                else:
                    self.switch_to_biometric_data_page()

    # function that logs in the user
    def log_in(self):
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Critical)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        message.setFont(font)
        message.setWindowTitle("Sorry, something went wrong")

        username = self.username_input.text()
        password = self.password_input.text()
        self.username_input.clear()
        self.password_input.clear()

        if len(username) == 0:
            message.setText("The username field can't be empty!")
            message.exec_()
        elif len(password) == 0:
            message.setText("The password field can't be empty!")
            message.exec_()
        else:
            response = trigger_logging_in(username, password)
            if response:
                self.username = username
                how_much_data = ask_server_how_much_data(username)
                if how_much_data < 20:
                    # if I don't have enough data, I let the user in only using his password
                    self.switch_to_welcome_page()
                    # but I keep monitoring to learn behaviour for future reference
                    # start_new_thread(initial_monitoring, (username, password, self))
                    threading.Thread(target=initial_monitoring, args=(username, password, self), daemon=True).start()
                else:
                    # if I have enough data, I verify the user's biometrics
                    message = QtWidgets.QMessageBox()
                    message.setIcon(QtWidgets.QMessageBox.Information)
                    font = QtGui.QFont()
                    font.setFamily("Bahnschrift SemiCondensed")
                    message.setFont(font)
                    message.setWindowTitle("Stage 2 of logging in")
                    message.setText("Welcome to the second stage of authentication - behavioural verification!\n\n"
                                    "Please continue your work (writing emails, reports, messages), because we\'ll "
                                    "work in the background without disturbing you. You'll land at the welcome page "
                                    "after we feel like you are who you claimed to be or you'll have to log in again "
                                    "if we can't verify your identity!")
                    message.exec_()
                    self.login_button.setVisible(False)
                    self.new_account_button.setVisible(False)
                    # start_new_thread(self.log_in_second, (username, password))
                    threading.Thread(target=self.log_in_second, args=(username, password), daemon=True).start()

            else:
                if response is None:
                    self.finished_thread_offline_server.emit()
                elif not response:
                    message.setText("Invalid username or password! Please try again!")
                    message.exec_()

    def log_in_second(self, username, password):
        result = self.monitor_behaviour(username, password, 1)
        if result is True:
            how_many_days = ask_server_about_last_password_change(username)
            if how_many_days > 90:
                self.switch_to_forced_change_password_page()
                self.forced_password_change.emit()
                return
            else:
                self.switch_to_welcome_page()
            # start_new_thread(self.monitor_behaviour, (username, password, 0))
            threading.Thread(target=self.monitor_behaviour, args=(username, password, 0), daemon=True).start()
        else:
            self.switch_to_login_page()
            if result != "offline":
                self.finished_thread.emit()
        self.login_button.setVisible(True)
        self.new_account_button.setVisible(True)

    def show_popup(self):
        failed_message = QtWidgets.QMessageBox()
        failed_message.setIcon(QtWidgets.QMessageBox.Information)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        failed_message.setFont(font)
        failed_message.setWindowTitle("Sorry, something went wrong")
        failed_message.setText("We detected unusual behaviour that couldn't be used to verify your identity. "
                               "If this was a mistake, please log in again.")
        failed_message.exec_()

    def show_forced_password_change_popup(self):
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Information)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        message.setFont(font)
        message.setWindowTitle("Please, change your password!")
        message.setText("Your password seems to be older than 90 days! Changing it is mandatory!")
        message.exec_()

    def monitor_behaviour(self, username, password, flag):
        if flag == 0:
            # control = True
            while True:
                keylogger.KeyLogger()
                my_data_extractor = dataExtractor.DataExtractor(resource_path("E:/Program Files/AuthenticationSystem/"
                                                                              "logged_keystrokes.csv"))
                my_data_extractor.run()
                data = my_data_extractor.get_keystroke_dynamic_information()
                response = send_to_verify_behavioural_data(username, password, data)
                if response == True:
                    pass
                elif response == False:
                    # control = False
                    self.switch_to_login_page()
                    self.finished_thread.emit()
                    break
                else:
                    if response == "ignore":
                        break
                    # control = False
                    else:
                        self.finished_thread_offline_server.emit()
        else:
            keylogger.KeyLogger()
            my_data_extractor = dataExtractor.DataExtractor(resource_path("E:/Program Files/AuthenticationSystem/"
                                                                          "logged_keystrokes.csv"))
            my_data_extractor.run()
            data = my_data_extractor.get_keystroke_dynamic_information()
            response = send_to_verify_behavioural_data(username, password, data)
            if response == True:
                return response
            elif response == False:
                return response
            else:
                self.finished_thread_offline_server.emit()
                return "offline"

    def change_password(self, restart_flag):
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Critical)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        message.setFont(font)
        message.setWindowTitle("Sorry, something went wrong")
        if len(self.current_username_input.text()) == 0:
            message.setText("The username field can't be empty!")
            message.exec_()
        elif len(self.current_password_input.text()) == 0:
            message.setText("The old (current) password field can't be empty!")
            message.exec_()
        elif len(self.future_password_input.text()) < 10:
            if len(self.future_password_input.text()) == 0:
                message.setText("The new password field can't be empty!")
            else:
                if re.match("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{10,}$",
                            self.future_password_input.text()) is None:
                    message.setText("The new password that you picked is too short and/or easy to guess!")
            message.exec_()
        elif len(self.confirm_password_input.text()) == 0:
            message.setText("Please confirm the new password by typing it again in the last field!")
            message.exec_()
        elif self.current_password_input.text() == self.future_password_input.text():
            message.setText("Your new password can't be your old (current) password!")
            message.exec_()
        elif self.future_password_input.text() != self.confirm_password_input.text():
            message.setText("The last two fields do not match!")
            message.exec_()
        else:
            response = trigger_changing_password(self.current_username_input.text(), self.current_password_input.text(),
                                                 self.future_password_input.text())
            if response is False:
                self.finished_thread_offline_server.emit()
            else:
                if response == "invalid":
                    message.setText("You might have typed your old (current) credentials wrong! Please try again.")
                    message.exec_()
                    self.future_password_input.clear()
                    self.confirm_password_input.clear()
                elif response == "unknown":
                    message.setText("Unknown problem, please try again later.")
                    message.exec_()
                    self.current_username_input.clear()
                    self.current_password_input.clear()
                    self.future_password_input.clear()
                    self.confirm_password_input.clear()
                else:
                    """self.current_username_input.clear()
                    self.current_password_input.clear()
                    self.future_password_input.clear()
                    self.confirm_password_input.clear()
                    self.switch_to_login_page()"""
                    self.log_out(restart_flag)

    def show_offline_server_notification(self):
        failed_message = QtWidgets.QMessageBox()
        failed_message.setIcon(QtWidgets.QMessageBox.Information)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiCondensed")
        failed_message.setFont(font)
        failed_message.setWindowTitle("Sorry, something went wrong")
        failed_message.setText("The server is currently unavailable. \n\nIf the issue persists, please notify "
                               "the system administrator.")
        failed_message.exec_()
        self.switch_to_login_page()

    def log_out(self, restart_flag):
        """global RESTART
        RESTART = True
        print(RESTART)"""
        send_log_out_information(self.username)
        restart_flag.value = 1
        QtWidgets.QApplication.quit()


# function that triggers a connection with the server
def trigger_connection():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            # print('Connected to server')
            socket_tcp.send(str(['just-checking']).encode())
            while 1:
                data = socket_tcp.recv(4096)
                # print('Received data: {}'.format(data.decode('utf-8')))
                # data = socket_tcp.recv(4096)
                break
        # print('Closed connection')
        return True
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


# function that triggers creating an account on the server
def trigger_creating_account(username, password):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            data = [session_id, "create_account", username, password, hostname, ip_address]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            return data
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


# function that sends behavioural data to the server (& database)
def send_behavioural_data(username, password, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            data = [session_id, "insert_behavioural_data", username, password, data]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            return data
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


# function that sends information about a user logging out to the server
def send_log_out_information(username):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            data = [session_id, "insert_log_out_information", username, hostname, ip_address]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            return data
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


# utility function
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.getcwd())
    return os.path.join(base_path, relative_path)


# function for initial monitoring
def initial_monitoring(username, password, window):
    for i in range(0, 20):
        keylogger.KeyLogger()
        my_data_extractor = dataExtractor.DataExtractor(resource_path("E:/Program Files/"
                                                                      "AuthenticationSystem/logged_keystrokes.csv"))
        my_data_extractor.run()
        data = my_data_extractor.get_keystroke_dynamic_information()
        response = send_behavioural_data(username, password, data)
        if response is False:
            window.finished_thread_offline_server.emit()
    window.switch_to_login_page()


def trigger_logging_in(username, password):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            data = [session_id, "verify_credentials", username, password, hostname, ip_address]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            if data == 'valid':
                return True
            return False
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return None


# function to ask the server how much biometric data it has
def ask_server_how_much_data(username):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            data = [session_id, "how_much_data", username]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            return int(data)
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


# function to ask the server when was the password changed last time
def ask_server_about_last_password_change(username):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            data = [session_id, "when_changed_password", username]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            return int(data)
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


def trigger_changing_password(username, old_password, new_password):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            data = [session_id, "change_password", username, old_password, new_password, hostname, ip_address]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            return data
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return False


# function that sends behavioural data to the server (& database) for verification
def send_to_verify_behavioural_data(username, password, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_tcp:
            socket_tcp.connect((host_addr, host_port))
            session_id = socket_tcp.recv(4096).decode('utf-8')
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            data = [session_id, "verify_behavioural_data", username, password, hostname, ip_address, data]
            data = str(data)
            socket_tcp.send(data.encode())
            data = socket_tcp.recv(4096).decode('utf-8')
            if data == "ignore":
                return data
            return data == "valid"
    except (ConnectionError, ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
        return None


# function that deletes the file collecting keystrokes
def erase_residual_data():
    if os.path.exists(resource_path("E:/Program Files/AuthenticationSystem/logged_keystrokes.csv")):
        os.remove(resource_path("E:/Program Files/AuthenticationSystem/logged_keystrokes.csv"))


# main function, activating GUI
# noinspection PyArgumentList
def start(restart_flag):
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    UI = Window(MainWindow, restart_flag)
    MainWindow.show()
    # sys.exit(app.exec_())
    app.exec_()


"""while RESTART is True:
    RESTART = False
    main()"""

if __name__ == '__main__':
    RESTART = Manager().Value('i', 1)
    """while RESTART is True:
        print(RESTART)
        RESTART = False
        p = Process(target=start)
        print("started")
        p.start()
        p.join()s
        print("ended")
        print(RESTART)"""
    while RESTART.value == 1:
        RESTART.value = 0
        p = Process(target=start, args=(RESTART,))
        p.start()
        p.join()
