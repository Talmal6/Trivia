import os.path
import re
import socket
import time
import threading
import subprocess

from cli import Color, style_str
from trivia import Trivia
from players_data import PlayersData

# SETTINGS
server_name = 'Universe7'
server_port = 13117
welcome_message = f'Welcome to the ' + style_str(server_name, bold=True) + ' server'
questions_file = 'questions.csv'        # File containing the questions
players_data_file = 'players_data.csv'  # File containing the players data, for statistics
question_time = 5                       # Time given to answer each question
players_wait_time = 3                   # Time to wait for players to join
minimum_players = 1                     # Minimum number of players required to start the game
broadcast_timeout = 1                   # Time to wait between game broadcasts
tick_time = 1                           # Time between each server tick
magic_number = 0xabcddcba               # Magic number for the broadcast packet, has to match the client side


class Server:
    """
    A class representing a server for a trivia game.
    """
    def __init__(self, ip: str, port: int, name: str):
        """
        Initializes a server with the given IP address, port number, and name.
        :param ip: The IP address of the server.
        :param port: The port number of the server.
        :param name: The name of the server.
        """
        self.ip = ip
        self.port = port
        self.name = name
        self.udp_socket = None  # UDP socket
        self.tcp_socket = None  # TCP socket
        self.last_connection_time = -1
        self.waiting_for_connections = False
        self.clients = {}
        self.trivia = Trivia(questions_file)
        self.players_data = PlayersData(players_data_file)
        print(style_str(server_name, bold=True) + style_str(' server started', Color.YELLOW))

    def _broadcast(self):
        """
        Private method.
        Continuously broadcasts a :class:`Packet` over UDP.
        """
        packet = Packet(self.name, self.port).encode()
        broadcast_ip = '.'.join(self.ip.split('.')[:-1]) + '.255'
        while self.waiting_for_connections:
            self.udp_socket.sendto(packet, (broadcast_ip, self.port))
            time.sleep(broadcast_timeout)

    def _accept_connections(self):
        """
        Private method.
        Accepts incoming connections from clients over TCP.
        """
        self.tcp_socket.listen(1)  # listen for incoming connections
        while self.waiting_for_connections:
            try:
                conn, addr = self.tcp_socket.accept()
                data = conn.recv(1024).decode()  # receive data from the client
                print(style_str(data, bold=True) + style_str(' connected to the server', Color.YELLOW))
                conn.send(f'{data}'.encode())   # send an arbitrary msg to verify connection
                self.clients.update({conn: data})
                self.last_connection_time = time.time()
            except socket.error:
                return

    def broadcast_game_offer(self):
        """
        Broadcasts game offers using `_broadcast()`, and waits for clients to connect over TCP using `_accept_connections()`.
        """
        # init sockets
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.ip, self.port))
        self.waiting_for_connections = True

        # Start the broadcast thread
        broadcast_thread = threading.Thread(target=self._broadcast)
        broadcast_thread.start()

        # Start the connections thread
        connection_thread = threading.Thread(target=self._accept_connections)
        connection_thread.start()

        # Wait for clients to connect
        print(style_str('Broadcasting game offer on IP address ', Color.YELLOW) + style_str(self.ip, bold=True))
        self.last_connection_time = time.time()
        while len(self.clients) < minimum_players:
            time.sleep(time.time() - self.last_connection_time + players_wait_time)
        self.waiting_for_connections = False
        self.udp_socket.close()
        print(style_str('Done broadcasting, game will begin shortly...', Color.YELLOW))

    def send_message(self, msg: str, print_msg=True):
        """
        Sends a message to all clients over TCP.
        :param msg: A message to send.
        :param print_msg: A boolean indicating whether to print the message to the server's console.
        """
        msg += '\n'
        for conn, name in self.clients.copy().items():
            try:
                conn.send(msg.encode())
            except:
                self.clients.pop(conn)
                conn.close()
                print(style_str('Connection with ', Color.YELLOW) + style_str(name, bold=True) + style_str(' lost', Color.YELLOW))
        print(msg, end='') if print_msg else None

    def _send_welcome_msg(self):
        """
        Sends a welcome message to all clients over TCP, using the `send_message()` method.
        """
        msg = f'\n{welcome_message}'
        count = 1
        for player in self.clients.values():
            msg += f'\nPlayer {count}: {player}'
            count += 1
        self.send_message(msg)

    def _handle_response(self, connection: socket, answer: bool):
        """
        Handles the response from a client, and sends a message to all clients indicating whether the answer was correct or not.
        :param connection: A socket connection to a client to get the response from.
        :param answer: The correct answer to the question.
        """
        try:
            data = connection.recv(1024)
            response = data.decode()[-1] == '1'
            if not self.stop_event.is_set():
                self.responses[connection] = response
                self.send_message(style_str(self.clients[connection], bold=True) + ' is ' + (style_str('correct', Color.GREEN) if response == answer else style_str('incorrect', Color.RED)))
        except socket.error:
            if connection in self.clients:
                self.clients.pop(connection)
                connection.close()

    def _game_loop(self):
        """
        The main game loop, handles the game logic.
        """
        self.active_players = self.clients.copy()
        self.stop_event = threading.Event()
        round_num = 1
        while True:
            # Send the next question to all clients
            question = self.trivia.get_question()
            players = ', '.join(self.active_players.values())
            self.send_message(style_str(f'===== Round {round_num} =====', bold=True))
            time.sleep(tick_time)
            self.send_message(f'Players: {players}')
            time.sleep(tick_time)
            self.send_message(question.question, True)

            # Listen for clients responses
            self.responses = {}
            response_threads = []
            self.stop_event.clear()
            for conn, name in self.active_players.items():    # Start a thread for each client
                responses_thread = threading.Thread(target=self._handle_response, args=(conn, question.answer))
                responses_thread.start()
                response_threads.append(responses_thread)
            [thread.join(timeout=question_time) for thread in response_threads]
            self.stop_event.set()   # Stop responses_thread

            # Handle time-outs
            if len(self.responses) < len(self.active_players):
                self.send_message('Time is up!')
                time.sleep(tick_time)
                for conn, player_name in self.active_players.copy().items():
                    if conn not in self.responses:
                        self.send_message(style_str(player_name, bold=True) + ' did not answer in time')
                        self.active_players.pop(conn)
                        time.sleep(tick_time)

            # Handle answers
            self.send_message('The correct answer is ' + style_str(str(question.answer), bold=True))
            for conn, response in self.responses.items():
                self.players_data.add_data(self.clients[conn], response == question.answer)     # Update players data
                if response != question.answer:
                    self.active_players.pop(conn)
            time.sleep(tick_time)

            # Calculate % of correct answers
            perc = round(len(self.active_players) / len(self.responses) * 100, 2) if (len(self.responses) > 0) else 0
            self.send_message(f'{perc}% of players answered correctly')

            # Check if the game is over
            if len(self.active_players) < 2 or self.trivia.is_empty():
                self.send_message(style_str('===== Game Over =====', bold=True))
                time.sleep(tick_time)
                if len(self.active_players) == 0:
                    self.send_message('No winners')
                elif len(self.active_players) == 1:
                    winner = list(self.active_players.values())[0]
                    self.send_message(style_str(winner, bold=True) + style_str(' is the winner!', Color.CYAN))
                else:
                    winners = ', '.join(style_str(winner, bold=True) for winner in self.active_players.values())
                    self.send_message(style_str(winners, bold=True) + style_str(' are the winners!', Color.CYAN))
                time.sleep(tick_time)
                return
            round_num += 1
            time.sleep(tick_time)

    def start_game(self):
        """
        Starts the game. Loads the questions, sends the welcome message, and starts the game loop.
        """
        self.trivia.load_questions()
        self._send_welcome_msg()
        self._game_loop()
        self.end_game()

    def _send_leaderboard(self):
        """
        Sends the current scores to all clients.
        """
        self.send_message(style_str('===== Leaderboard =====', bold=True))
        sorted_dict = dict(sorted(self.players_data.get_percentages().items(), key=lambda item: item[1], reverse=True))
        for key, value in sorted_dict.items():
            self.send_message(f'{key}: {round(value, 2)}%')
            time.sleep(tick_time)

    def end_game(self):
        """
        Ends the game. Closes the TCP connections and the socket.
        """
        self._send_leaderboard()
        time.sleep(tick_time)
        for conn in self.clients.copy():
            conn.close()
        self.tcp_socket.close()
        self.clients.clear()
        self.active_players.clear()
        print(style_str('Game ended', Color.YELLOW))
        self.players_data.update_file()
        time.sleep(tick_time)

    def run(self):
        """
        Main method. Runs the server.
        """
        while True:
            self.broadcast_game_offer()
            self.start_game()
            time.sleep(tick_time)


class Packet:
    """
    A class representing a packet to be broadcast to clients.
    """ 
    def __init__(self, server_name: str, server_port: int, p_type: int = 2):
        """
        Initializes a packet with the given server name, port, and type, and a magic number.
        :param server_name: The name of the server.
        :param server_port: The port number of the server.
        :param p_type: The type of the packet. Defaults to 2 (game offer).
        """
        self.type = p_type
        self.server_name = server_name
        self.server_port = server_port
        self.magic_number = magic_number

    def encode(self):
        """
        Encodes the packet as a byte string.
        """
        return f'{str(self.magic_number)} {str(self.type)} {self.server_name} {self.server_port} {str(time.time())}'.encode()


def get_ip_address() -> str:
    """
    Tries to get the IP address of the server automatically using `ipconfig`.
    :return: The IP address of the server.
    """
    try:
        ipconfig_output = subprocess.check_output("ipconfig", shell=True).decode()
        ip_addresses = re.findall(r"IPv4 Address[. ]+: ([\d.]+)", ipconfig_output)
        valid_ips = []
        for ip_address in ip_addresses:
            valid_ips.append(ip_address)

        if len(valid_ips) == 0:
            raise Exception("Could not find IP address")
        elif len(valid_ips) == 1:
            return valid_ips[0]
        elif len(valid_ips) > 1:
            print('Found multiple IP addresses:')
            for i, ip in enumerate(valid_ips):
                print(f'{i + 1})', ip)
            choice = input('Enter the number of the IP address to use: ')
            return valid_ips[int(choice) - 1]
    except Exception:
        print(f'Failed to get IP address automatically')
        ip_address = input('Enter the server IP address: ')
        while not is_valid_ip(ip_address):
            ip_address = input('Invalid IP address. Enter a valid IP address: ')
        return ip_address


def is_valid_ip(ip: str) -> bool:
    """
    Checks if a given string is a valid IP address.
    :param ip: The string to check.
    :return: True if the string is a valid IP address, False otherwise.
    """
    return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) is not None


def is_valid_port(port: int) -> bool:
    """
    Checks if a given port number is valid.
    :param port: The port number to check.
    :return: True if the port number is valid, False otherwise.
    """
    return 1024 <= port <= 65535


def validate_settings():
    """
    Validates the settings of the server.
    """
    assert is_valid_port(server_port), 'Invalid server port number'
    assert is_valid_ip(get_ip_address()), 'Invalid server IP address'
    assert is_valid_port(server_port), 'Invalid server port number'
    assert server_name != '', 'Invalid server name'
    assert minimum_players > 0, 'Minimum players must be greater than 0'
    assert broadcast_timeout >= 0, 'Broadcast timeout cannot be negative'
    assert players_wait_time >= 0, 'Players wait time cannot be negative'
    assert question_time >= 0, 'Question time cannot be negative'
    assert os.path.isfile(questions_file), 'Questions file not found'


if __name__ == '__main__':
    validate_settings()
    server_ip = get_ip_address()
    s1 = Server(server_ip, server_port, server_name)
    s1.run()
