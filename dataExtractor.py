import csv
import sys
import os
from operator import itemgetter


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.getcwd())
    return os.path.join(base_path, relative_path)


def find_key_category(key):
    category = {
        "Key.esc": "l", "Key.delete": "r",
        "'`'": "l", "'1'": "l", "'2'": "l", "'3'": "l", "'4'": "l", "'5'": "l",
        "'6'": "r", "'7'": "r", "'8'": "r", "'9'": "r", "'0'": "r", "'-'": "r", "'='": "r",
        "'q'": "l", "'w'": "l", "'e'": "l", "'r'": "l", "'t'": "l",
        "'y'": "r", "'u'": "r", "'i'": "r", "'o'": "r", "'p'": "r", "'['": "r", "']'": "r", "'\\'": "r",
        "'a'": "l", "'s'": "l", "'d'": "l", "'f'": "", "'g'": "l",
        "'h'": "r", "'j'": "r", "'k'": "r", "'l'": "r", "';'": "r", "'''": "r", "Key.enter": "r",
        "'z'": "l", "'x'": "l", "'c'": "l", "'v'": "l", "'b'": "l",
        "'n'": "r", "'m'": "r", "','": "r", "'.'": "r", "'/'": "r"
    }
    if key in category:
        return category.get(key)
    else:
        if key.lower() in category:
            return category.get(key.lower())
        else:
            return key


class DataExtractor:
    def __init__(self, path):
        # hold time
        self.hold_left = 0.0
        self.hold_right = 0.0
        self.hold_space = 0.0

        # latency
        self.pp_left_left = 0.0
        self.pp_left_right = 0.0
        self.pp_right_left = 0.0
        self.pp_right_right = 0.0

        self.rr_left_left = 0.0
        self.rr_left_right = 0.0
        self.rr_right_left = 0.0
        self.rr_right_right = 0.0

        self.pr_left_left = 0.0
        self.pr_left_right = 0.0
        self.pr_right_left = 0.0
        self.pr_right_right = 0.0

        self.path = path
        with open(resource_path(self.path), newline='') as file:
            self.data = list(csv.reader(file))
        self.average_hold_time = []

    def delete_duplicates(self):
        i = 0
        while i < len(self.data) - 2:
            if self.data[i][0] == self.data[i + 1][0] and self.data[i][1] == self.data[i + 1][1]:
                del self.data[i + 1]
            else:
                i = i + 1

    def format_data(self):
        # self.data.pop()
        formatted_data = []
        for log in self.data:
            if (not log[1] == "Key.shift") & (not log[1] == "Key.shift_r") & (not log[1] == "Key.shift_l") \
                    & (not log[1] == "Key.caps_lock"):
                log[2] = float(log[2])
                formatted_data.append(log)
        self.data = formatted_data
        self.data = sorted(self.data, key=itemgetter(2))
        self.delete_duplicates()
        for log in self.data:
            log[2] = str(log[2])

    def determine_average_hold_time(self):
        hold_time = []
        for i in range(0, len(self.data)):
            if (self.data[i][0]) == "pressed":
                for j in range(i + 1, len(self.data)):
                    if (self.data[j][0]) == "released":
                        if self.data[i][1] == self.data[j][1]:  # found a pair
                            pair = [self.data[i][1], float(self.data[j][2]) - float(self.data[i][2])]
                            hold_time.append(pair)
                        break
        for row in hold_time:
            row[0] = find_key_category(row[0])
        # print(hold_time)

        total = 0.0
        number = 0
        for row in hold_time:
            if row[0] == 'l':
                total += float(row[1])
                number += 1
        if number != 0:
            self.hold_left = total / number
        # print(self.hold_left)

        total = 0.0
        number = 0
        for row in hold_time:
            if row[0] == 'r':
                total += float(row[1])
                number += 1
        if number != 0:
            self.hold_right = total / number
        # print(self.hold_right)

        total = 0.0
        number = 0
        for row in hold_time:
            if row[0] == 'Key.space':
                total += float(row[1])
                number += 1
        if number != 0:
            self.hold_space = total / number
        # print(self.hold_space)

    def determine_latency(self):
        pressed_key_timestamp = []
        for pressed in self.data:
            if pressed[0] == "pressed":
                # introducem valori de tipul (categoria tastei, timestamp)
                pair = [find_key_category(pressed[1]), pressed[2]]
                if not pair[0] == "Key.space":
                    pressed_key_timestamp.append(pair)
        # print(pressed_key_timestamp)

        total_pp_left_left = 0.0
        number_pp_left_left = 0
        total_pp_left_right = 0.0
        number_pp_left_right = 0
        total_pp_right_left = 0.0
        number_pp_right_left = 0
        total_pp_right_right = 0.0
        number_pp_right_right = 0
        for i in range(0, len(pressed_key_timestamp) - 1):
            key1 = pressed_key_timestamp[i][0]
            time1 = float(pressed_key_timestamp[i][1])
            key2 = pressed_key_timestamp[i + 1][0]
            time2 = float(pressed_key_timestamp[i + 1][1])
            if time2 - time1 < 1.5:
                if (key1 == "l") & (key2 == "l"):
                    total_pp_left_left = total_pp_left_left + time2 - time1
                    number_pp_left_left += 1
                elif (key1 == "l") & (key2 == "r"):
                    total_pp_left_right = total_pp_left_right + time2 - time1
                    number_pp_left_right += 1
                elif (key1 == "r") & (key2 == "l"):
                    total_pp_right_left = total_pp_right_left + time2 - time1
                    number_pp_right_left += 1
                elif (key1 == "r") & (key2 == "r"):
                    total_pp_right_right = total_pp_right_right + time2 - time1
                    number_pp_right_right += 1

        if number_pp_left_left != 0:
            self.pp_left_left = total_pp_left_left / number_pp_left_left
        # print(self.pp_left_left)

        if number_pp_left_right != 0:
            self.pp_left_right = total_pp_left_right / number_pp_left_right
        # print(self.pp_left_right)

        if number_pp_right_left != 0:
            self.pp_right_left = total_pp_right_left / number_pp_right_left
        # print(self.pp_right_left)

        if number_pp_right_right != 0:
            self.pp_right_right = total_pp_right_right / number_pp_right_right
        # print(self.pp_right_right)

        #############################################################################################

        released_key_timestamp = []
        for released in self.data:
            if released[0] == "released":
                # introducem valori de tipul (categoria tastei, timestamp)
                pair = [find_key_category(released[1]), released[2]]
                if not pair[0] == "Key.space":
                    released_key_timestamp.append(pair)
        # print(released_key_timestamp)

        total_rr_left_left = 0.0
        number_rr_left_left = 0
        total_rr_left_right = 0.0
        number_rr_left_right = 0
        total_rr_right_left = 0.0
        number_rr_right_left = 0
        total_rr_right_right = 0.0
        number_rr_right_right = 0

        for i in range(0, len(released_key_timestamp) - 1):
            key1 = released_key_timestamp[i][0]
            time1 = float(released_key_timestamp[i][1])
            key2 = released_key_timestamp[i + 1][0]
            time2 = float(released_key_timestamp[i + 1][1])
            if time2 - time1 < 1.5:
                if (key1 == "l") & (key2 == "l"):
                    total_rr_left_left = total_rr_left_left + time2 - time1
                    number_rr_left_left += 1
                elif (key1 == "l") & (key2 == "r"):
                    total_rr_left_right = total_rr_left_right + time2 - time1
                    number_rr_left_right += 1
                elif (key1 == "r") & (key2 == "l"):
                    total_rr_right_left = total_rr_right_left + time2 - time1
                    number_rr_right_left += 1
                elif (key1 == "r") & (key2 == "r"):
                    total_rr_right_right = total_rr_right_right + time2 - time1
                    number_rr_right_right += 1

        if number_rr_left_left != 0:
            self.rr_left_left = total_rr_left_left / number_rr_left_left
        # print(self.rr_left_left)

        if number_rr_left_right != 0:
            self.rr_left_right = total_rr_left_right / number_rr_left_right
        # print(self.rr_left_right)

        if number_rr_right_left != 0:
            self.rr_right_left = total_rr_right_left / number_rr_right_left
        # print(self.rr_right_left)

        if number_rr_right_right != 0:
            self.rr_right_right = total_rr_right_right / number_rr_right_right
        # print(self.rr_right_right)

        #############################################################################################

        total_pr_left_left = 0.0
        number_pr_left_left = 0
        total_pr_left_right = 0.0
        number_pr_left_right = 0
        total_pr_right_left = 0.0
        number_pr_right_left = 0
        total_pr_right_right = 0.0
        number_pr_right_right = 0

        pressed_released_key_timestamps = []
        for i in range(0, len(self.data) - 1):
            if self.data[i][0] == "pressed":
                # introducem valori de tipul (categorie tasta apasata, timestamp apasare, timestamp eliberare)
                triple = [find_key_category(self.data[i][1]), float(self.data[i][2])]
                for j in range(i + 1, len(self.data)):
                    if (self.data[j][0] == "released") & (self.data[j][1] == self.data[i][1]):
                        triple.append(float(self.data[j][2]))
                        break
                if not triple[0] == "Key.space":
                    if len(triple) == 3:
                        pressed_released_key_timestamps.append(triple)
        # print(pressed_released_key_timestamps)

        for i in range(1, len(pressed_released_key_timestamps)):
            # pressed_released_key_timestamps[i] - pressed
            # pressed_released_key_timestamps[i-1] - released
            time1 = pressed_released_key_timestamps[i - 1][2]
            time2 = pressed_released_key_timestamps[i][1]
            if time2 - time1 < 1.5:
                if (pressed_released_key_timestamps[i][0] == 'l') & (pressed_released_key_timestamps[i - 1][0] == 'l'):
                    total_pr_left_left += time2 - time1
                    number_pr_left_left += 1
                elif (pressed_released_key_timestamps[i][0] == 'l') & (pressed_released_key_timestamps[i - 1][0] == 'r'):
                    total_pr_left_right += time2 - time1
                    number_pr_left_right += 1
                elif (pressed_released_key_timestamps[i][0] == 'r') & (pressed_released_key_timestamps[i - 1][0] == 'l'):
                    total_pr_right_left += time2 - time1
                    number_pr_right_left += 1
                elif (pressed_released_key_timestamps[i][0] == 'r') & (pressed_released_key_timestamps[i - 1][0] == 'r'):
                    total_pr_right_right += time2 - time1
                    number_pr_right_right += 1

        if number_pr_left_left != 0:
            self.pr_left_left = total_pr_left_left / number_pr_left_left
        # print(self.pr_left_left)

        if number_pr_left_right != 0:
            self.pr_left_right = total_pr_left_right / number_pr_left_right
        # print(self.pr_left_right)

        if number_pr_right_left != 0:
            self.pr_right_left = total_pr_right_left / number_pr_right_left
        # print(self.pr_right_left)

        if number_pr_right_right != 0:
            self.pr_right_right = total_pr_right_right / number_pr_right_right
        # print(self.pr_right_right)

    def get_keystroke_dynamic_information(self):
        return [self.hold_left, self.hold_right, self.hold_space,
                self.pp_left_left, self.pp_left_right, self.pp_right_left, self.pp_right_right,
                self.rr_left_left, self.rr_left_right, self.rr_right_left, self.rr_right_right,
                self.pr_left_left, self.pr_left_right, self.pr_right_left, self.pr_right_right]

    def run(self):
        self.format_data()
        # print(self.data)
        self.determine_average_hold_time()
        self.determine_latency()


# data_extractor = DataExtractor("E:/Program Files/AuthenticationSystem/test.csv")
# data_extractor.run()
# print(data_extractor.get_keystroke_dynamic_information())
