import socket
import subprocess
import base64
import select

class StealthServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port

    def handle_clients(self, server):
        inputs = [server]
        while True:
            readable, _, _ = select.select(inputs, [], [])
            for s in readable:
                if s is server:
                    conn, addr = server.accept()
                    inputs.append(conn)
                else:
                    try:
                        message = s.recv(1024)
                        if not message:
                            inputs.remove(s)
                            s.close()
                            continue
                        decoded_msg = base64.b64decode(message).decode(errors='ignore')
                        print(f"Received from client: {decoded_msg}")
                        response = base64.b64encode(f"Ack: {decoded_msg}".encode())
                        s.send(response)
                    except:
                        inputs.remove(s)
                        s.close()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        print(f"Server running on {self.host}:{self.port}")
        self.handle_clients(server)

def set_kernel_parameters():
    try:
        subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_max_syn_backlog=2048'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_syncookies=1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_synack_retries=2'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

if __name__ == "__main__":
    set_kernel_parameters()
    server = StealthServer()
    server.start_server()
