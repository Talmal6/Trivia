import string

from client import Client, is_valid_port
import time
import random

# SETTINGS
port = 13117
name_prefix = '[BOT]'
name_options = ['Android 16', 'Android 17', 'Android 18']
generate_name = False
generated_name_length = 5
reaction_time = 1  # Time to wait before sending input


class Bot(Client):
    """
    Bot client that generates random answers.
    """

    def __init__(self, port: int, name: str = None):
        """
        Initializes a bot client.
        :param name: The name of the bot.
        :param port: The port number to connect to.
        """
        name = name_prefix + ' '
        name += random.choice(name_options) if not generate_name else ''.join(random.choices(string.ascii_letters + string.digits, k=generated_name_length))
        super().__init__(name, port, False)

    def input_listener(self):
        while True:
            try:
                if self.response_needed:
                    choice = random.choice(['0', '1'])
                    self.tcp_socket.send(choice.encode())
                    self.response_needed = False
            except:
                continue


def validate_settings():
    """
    Validates the settings of the bot.
    """
    assert is_valid_port(port), 'Invalid port number'
    assert reaction_time >= 0, 'Reaction time cannot be negative'


if __name__ == '__main__':
    validate_settings()
    b1 = Bot(port)
    b1.run()
