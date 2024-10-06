import socket
import threading
import json
import requests
import string
from bs4 import BeautifulSoup

# Define server IP and port
SERVER_IP = ""
SERVER_PORT = 3389
clients = []
usernames = {}

# Function to handle each client connection
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    while True:
        try:
            data = client_socket.recv(2048)  # Receive data from the client
            if not data:
                break
            print(f"Received from {client_address}: {data.decode('utf-8')}")
            data = str(data.decode("utf-8"))
            data = json.loads(data)
            if data["command"] == "Start":
                # Game load
                start_page = requests.get("https://en.wikipedia.org/wiki/Special:Random")
                start_url = start_page.url
                
                flag_1 = True
                while(flag_1):
                    print("Back at top of loop")
                    flag_2 = False
                    end_page = requests.get("https://en.wikipedia.org/wiki/Special:Random")
                    end_url = end_page.url
                    end_page_html = end_page.text
                    end_page_soup = BeautifulSoup(end_page_html, "html.parser")
                    end_title = end_page_soup.find(id = "firstHeading").get_text()

                    chars = string.printable

                    for char in end_title:
                        if char not in chars:
                            flag_2 = True
                            break
                    flag_1 = flag_2

                message = str(json.dumps({"command": "Start Game", "start_url": start_url, "end_url": end_url, "end_title": end_title, "usernames": {}, "winner": "", "time": "", "num_clicks": ""}))
                broadcast(message)
            elif data["command"] == "Join":
                username = data["username"]
                usernames[str(client_address)] = username
                message = str(json.dumps({"command": "Player Joined", "start_url": "", "end_url": "", "end_title": "", "usernames": usernames, "winner": "", "time": "", "num_clicks": ""}))
                broadcast(message)
            elif data["command"] == "Game Over":
                message = str(json.dumps({"command": "Game Over", "start_url": "", "end_url": "", "end_title": "", "usernames": {}, "winner": data["winner"], "time": data["time"], "num_clicks": data["num_clicks"]}))
                broadcast(message) 
        except ConnectionResetError:
            break

    print(f"Connection closed by {client_address}")
    client_socket.close()
    clients.remove(client_socket)
    usernames.pop(str(client_address), None)
    message = str(json.dumps({"command": "Player Joined", "start_url": "", "end_url": "", "end_title": "", "usernames": usernames, "winner": "", "time": "", "num_clicks": ""}))
    broadcast(message)

# Function to broadcast data to all clients
def broadcast(message):
    message = message.encode("utf-8")
    print(message)
    for client in clients:
        client.send(message)

# Main server function
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(12)
    print(f"Server started on {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        clients.append(client_socket)
        
        # Start a new thread for each client
        client_thread = threading.Thread(target = handle_client, args = (client_socket, client_address))
        client_thread.start()

start_server()
