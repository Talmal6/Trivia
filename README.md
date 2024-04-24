# Trivia Game Application

This project is a multiplayer trivia game implemented in Python, designed as a networked client-server application. It focuses on executing various network protocols effectively and includes a server that manages game logic and client connections. A client application allows players to interact with the game, and a command-line interface supports administrative functions. The game centers on true or false questions about the anime series "Dragon Ball."
Features

  1. Server-Client Architecture: Supports multiple players connecting and playing simultaneously over a LAN.
  2. Command-Line Interface: Facilitates administrative tasks and game settings adjustments.
  3. Dynamic Question Database: Utilizes CSV files for questions, making it easy to modify or expand the question pool.

## Installation
Prerequisites

  1. Python 3.x
  2.  keyboard Python package for capturing keyboard input:

    pip install keyboard

## Usage
### Server Setup
Start the server on one of the computers within the same network:

    python server.py

This will initiate the server and begin listening for client connections.
### Client Connection

Run the client script on the same or different computers within the same network:

    python client.py

Players should be able to connect to the server and participate in the trivia game.

## The Game

The trivia game involves simple true or false questions specifically about the "Dragon Ball" anime series. The goal of this project is to focus on executing various network protocols efficiently.
Game Flow

  1. Start the Server: Initiate the server which then broadcasts an offer every second.
  2. Connect Clients: Players start their clients and receive the server's offer.
  3. Game Play: Each client joins the game over TCP, sending their player names followed by trivia gameplay.


## Project Details

This project is part of the "Intro to Computer Networks 2023" coursework, designed to implement and test network programming capabilities extensively. It involves detailed simulations of client-server interactions over TCP/UDP, emphasizing non-blocking I/O operations and effective state management.
