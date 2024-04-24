import keyboard
import threading
import time
import os
import re

from enum import Enum

# SETTINGS
screen_title = 'Trivia King'
left_choice = 'True'
right_choice = 'False'
fps = 10
max_messages = 5


class Color(Enum):
    """
    An enumeration of colors for console output.
    """
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def style_str(s: str, color: 'Color' = Color.END, bold: bool = False) -> str:
    """
    Returns a colored string.
    :param s: The string to color.
    :param color: The color to use.
    :param bold: A boolean indicating whether to make the string bold.
    :return: The colored string.
    """
    s = Color.BOLD.value + s if bold else s
    return color.value + s + Color.END.value


def centerize(s: str, width: int) -> str:
    """
    Centerizes a string in a given width.
    :param s: The string to centerize.
    :param width: The width to centerize the string in.
    :return: The centerized string.
    """
    visible_s = re.sub(r'\x1b\[[0-9;]*m', '', s)
    padding = (width - len(visible_s)) // 2
    extra_space = (width - len(visible_s)) % 2  # Add an extra space if the difference is an odd number
    return ' ' * padding + s + ' ' * (padding + extra_space)


class CLI:
    def __init__(self, enter_callback, win_width=80, win_height=20):
        self.enter_callback = enter_callback
        self.width = win_width
        self.height = win_height
        self.selected = 0
        self.messages = []
        self.input_thread = None
        self.stop_input = True

        # Add hotkeys
        keyboard.add_hotkey('left', self._change_selection, args=(1,))
        keyboard.add_hotkey('right', self._change_selection, args=(0,))
        keyboard.add_hotkey('enter', self._return_selection)

        self.print_thread = threading.Thread(target=self._printer)
        self.print_thread.start()

    def print_message(self, msg: str):
        self.messages.append(msg)
        if len(self.messages) > max_messages:
            self.messages.pop(0)

    def clear_messages(self):
        self.messages.clear()

    def _printer(self):
        while True:
            os.system('cls')
            self._print_screen()
            time.sleep(1 / fps)

    def _print_screen(self):
        self._print_title()
        self._print_main_window()
        self._print_choices()

    def _print_main_window(self):
        for i in range(self.height // 2):
            print('|' + ' ' * (self.width - 2) + '|')
        self._print_messages()
        for i in range(self.height // 2 + 1 + len(self.messages), self.height):
            print('|' + ' ' * (self.width - 2) + '|')

    def _print_messages(self):
        for msg in self.messages:
            visible_msg = re.sub(r'\x1b\[[0-9;]*m', '', msg)
            if len(visible_msg) > self.width - 2:
                self._print_long_message(msg)
            else:
                print('|' + centerize(msg, self.width - 2) + '|')

    def _print_long_message(self, msg: str):
        # Split the message into multiple lines if it's too long
        words = msg.split(' ')
        line = ''
        for word in words:
            if len(line) + len(word) + 1 > self.width - 2:  # +1 for the space
                print('|' + centerize(line, self.width - 2) + '|')
                line = word
            else:
                line += ' ' + word if line else word  # Don't add a space at the start of the line
        print('|' + centerize(line, self.width - 2) + '|')  # Print the last line

    def _print_title(self, title: str = screen_title):
        print('=' * self.width)
        print('|' + title.center(self.width - 2) + '|')
        print('|' + '-' * (self.width - 2) + '|')

    def _print_choices(self):
        padding = 1 if self.width % 2 == 0 else 0
        l: str = ('> ' + left_choice + ' <').center(self.width // 2 - 1) if self.selected else left_choice.center(self.width // 2 - 1)
        r: str = ('> ' + right_choice + ' <').center(self.width // 2 - 1 - padding) if not self.selected else right_choice.center(self.width // 2 - 1 - padding)
        print('|' + '-' * (self.width - 2) + '|')
        print('|' + l + '|' + r + '|')
        print('=' * self.width)

    def _change_selection(self, choice: int):
        self.selected = choice

    def _return_selection(self):
        self.enter_callback(str(self.selected))
