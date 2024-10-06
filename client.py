import socket
import threading
import json

# Server IP and port (must match server settings)
SERVER_IP = '10.32.193.176'  # Replace with the actual server's IP address
SERVER_PORT = 5557

# Function to handle receiving data from the server
def receive_data(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Received from server: {data.decode('utf-8')}")
        except ConnectionResetError:
            break

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    
    print(f"Connected to the server at {SERVER_IP}:{SERVER_PORT}")

    # Start a new thread to listen for data from the server
    receive_thread = threading.Thread(target=receive_data, args=(client_socket,))
    receive_thread.start()

    while True:
        message = input("Enter a message: ")
        if (message == "Start"):
            message = json.dumps({"command": "Start", "username": ""}).encode("utf-8")
            client_socket.send(message)  # Send data to the server
        if (message == "Join"):
            username = "Joe"
            message = json.dumps({"command": "Join", "username": username}).encode("utf-8")
            client_socket.send(message)  # Send data to the server

if __name__ == "__main__":
    start_client()
