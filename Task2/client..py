import socket
import time
import random
import string

class StealthClient:
    def __init__(self, host='172.23.198.251', port=8080):
        self.host = host
        self.port = port

    def generate_random_message(self, length=32):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def send_traffic(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            client.connect((self.host, self.port))
            while True:
                message = self.generate_random_message()
                client.sendall(message.encode())
                print(f"Sent message: {message}")
                
                try:
                    response = client.recv(1024).decode()
                    print(f"Received from server: {response}")
                except socket.timeout:
                    print("No response received")
                
                time.sleep(random.uniform(0.5, 3))  # Randomized delay
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            client.close()

if __name__ == "__main__":
    client = StealthClient()
    client.send_traffic()
