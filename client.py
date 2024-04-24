import threading
import time
import select
import socket
from cli import CLI, style_str, Color
import keyboard

# SETTINGS
client_name = 'Goku'
client_port = 13117
use_cli = True              # Toggle between using CLI and console
retry_time = 1              # Time to wait before retrying to listen for broadcasts after a failed connection
max_packet_time = 10        # Oldest broadcast packet to accept, in seconds
magic_number = 0xabcddcba   # Magic number for the broadcast packet, has to match the server side

# Key mapping for the client's input
key_mapping = {
    'y': 1,
    'n': 0,
    '1': 1,
    '0': 0
}


class Client:
    """
    A Client class.
    """

    def __init__(self, name: str, port: int, cli: bool = use_cli):
        """
        Initializes a new client with a given name and port number.
        :param name: The name of the player.
        :param port: The port number to use.
        :param cli: :class:`CLI` object to use for the client. None uses console (default).
        """
        self.name = name
        self.port = port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = None
        self.response_needed = False
        self.cli = CLI(lambda x: self.tcp_socket.send(x.encode())) if cli else None

        if not cli:
            self.input_thread = threading.Thread(target=self.input_listener)
            self.input_thread.start()

        self.udp_socket.bind(('', self.port))
        self._print_to_screen(style_str(name, bold=True) + style_str(' client started', Color.YELLOW))

    def listen_for_broadcasts(self) -> 'tuple[str, int]':
        """
        Listens for game broadcasts over UDP and when found returns the address as tuple of `(IP, port)`.
        :return: The IP and port of the server to connect to.
        """
        self._print_to_screen(style_str('Listening for game offers...', Color.YELLOW))
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            data = data.decode().split(' ')  # {magic_number} {message_type} {server_name} {server_port} {packet_time}
            if data[0] != str(magic_number) or float(data[4]) + max_packet_time < time.time():
                continue
            if data[1] == '2':
                self._print_to_screen(style_str('Received offer from server ', Color.YELLOW) + style_str(data[2], bold=True) + style_str(' at address ', Color.YELLOW) + style_str(addr[0], bold=True))
                return addr[0], int(data[3])  # IP, port

    def connect_server(self, ip: str, port: int) -> bool:
        """
        Connects to the server on a given IP and port address. Returns True if successful, and False otherwise.
        :param ip: The IP address of the server.
        :param port: The port number of the server.
        :return: True if connection was successful, False otherwise.
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._print_to_screen(style_str('Attempting to connect...', Color.YELLOW))
        try:
            self.tcp_socket.connect((ip, port))
            self.tcp_socket.send(self.name.encode())
            response = self.tcp_socket.recv(1024)
            if response:
                self._print_to_screen(style_str('Connected successfully', Color.GREEN))
                return True
            else:
                self._print_to_screen(style_str('Connection failed', Color.RED))
                return False
        except ConnectionRefusedError:
            self._print_to_screen(style_str('Connection refused', Color.RED))
            return False
        except TimeoutError:
            self._print_to_screen(style_str('Connection timed out'), Color.RED)
            return False

    def _print_to_screen(self, message: str):
        """
        Prints to the screen using the correct method (CLI or console)
        :param message: The message to print.
        """
        self.cli.print_message(message) if self.cli else print(message)

    def input_listener(self):
        while True:
            try:
                key = keyboard.read_key().lower()
                if key in key_mapping and self.response_needed:
                    self.tcp_socket.send(str(key_mapping[key]).encode())
                    self.response_needed = False
            except:
                continue

    def start_game(self):
        """
        Begins the game loop, continuously receiving and handling messages from the server.
        The function listens for incoming data from the server, processes it accordingly, and interacts with the :class:`CLI` if available.
        Boorekas Gvina Boorekas Gvina!!!!!!!!
        """
        buffer = []
        try:
            while True:
                # read from the socket if there is data to read
                ready_to_read, _, _ = select.select([self.tcp_socket], [], [], 0)
                if ready_to_read:
                    data = self.tcp_socket.recv(1024)
                    if data == b'':
                        return
                    buffer += data.decode().split('\n')
                    while len(buffer) > 0:
                        msg = buffer.pop(0)
                        if msg == '':
                            continue
                        self._print_to_screen(msg)
                        self.response_needed = True if not self.cli else False
        except socket.error:
            return

    def end_game(self):
        """
        Ends the game and closes the TCP socket connection.
        """
        self.response_needed = False
        self.tcp_socket.close()
        self._print_to_screen(style_str('Disconnected from server', Color.YELLOW))

    def run(self):
        """
        Main function to run the client, connecting to a server and starting the game loop.
        """
        while True:
            while True:
                ip, port = self.listen_for_broadcasts()
                if self.connect_server(ip, port):
                    self.start_game()
                    self.end_game()
                time.sleep(retry_time)


def is_valid_port(port: int) -> bool:
    """
    Checks if a given port number is valid.
    :param port: The port number to check.
    :return: True if the port number is valid, False otherwise.
    """
    return 1024 <= port <= 65535


def validate_settings():
    """
    Validates the settings of the client.
    """
    assert is_valid_port(client_port), 'Invalid port number'
    assert client_name.replace(' ', '') != '', 'Invalid client name'
    assert retry_time >= 0, 'Invalid retry time'
    assert (i in [0, 1] for i in key_mapping.values()), 'Invalid key mapping'


if __name__ == "__main__":
    validate_settings()
    c1 = Client(client_name, client_port)
    c1.run()
