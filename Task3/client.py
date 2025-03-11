import socket
import time
import argparse

def setup_client(nagle_enabled, delayed_ack_enabled):
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set socket options
    if not nagle_enabled:
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    # Set delayed ACK option (platform specific)
    if not delayed_ack_enabled:
        # On Linux:
        try:
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        except AttributeError:
            print("TCP_QUICKACK not supported on this platform")
    
    return client_socket

def run_client(nagle_enabled, delayed_ack_enabled):
    client_socket = setup_client(nagle_enabled, delayed_ack_enabled)
    
    # Connect to the server
    server_address = ('localhost', 10000)
    print(f"Connecting to {server_address} with Nagle: {'Enabled' if nagle_enabled else 'Disabled'}, "
          f"Delayed-ACK: {'Enabled' if delayed_ack_enabled else 'Disabled'}")
    client_socket.connect(server_address)
    
    try:
        # Generate 4KB of sample data
        data = b'X' * (4 * 1024)
        
        data_size = len(data)
        bytes_sent = 0
        
        # Transfer rate: 40 bytes/second
        chunk_size = 40
        
        start_time = time.time()
        print("Starting data transfer...")
        
        # Send data at specified rate for ~2 minutes
        running_time = 0
        while running_time < 120:  # ~2 minutes
            if bytes_sent < data_size:
                # Calculate the next chunk to send
                end_index = min(bytes_sent + chunk_size, data_size)
                chunk = data[bytes_sent:end_index]
                
                # Send the chunk
                client_socket.sendall(chunk)
                
                # Update bytes sent
                bytes_sent += len(chunk)
                
                # If we've sent all the data, start over
                if bytes_sent >= data_size:
                    bytes_sent = 0
                    print(f"Completed one cycle of sending 4KB file at {time.time() - start_time:.2f} seconds")
                
                # If we need to disable delayed ACK for each packet
                if not delayed_ack_enabled:
                    try:
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                    except AttributeError:
                        pass
                
                # Wait to maintain the transfer rate
                time.sleep(1.0)  # 1 second per chunk (40 bytes/second)
            
            running_time = time.time() - start_time
        
        print(f"Transfer completed after {running_time:.2f} seconds")
        
    finally:
        print("Closing socket")
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Client for Nagle Algorithm Analysis')
    parser.add_argument('--nagle', dest='nagle', action='store_true', default=True, 
                        help='Enable Nagle\'s algorithm (default: enabled)')
    parser.add_argument('--no-nagle', dest='nagle', action='store_false',
                        help='Disable Nagle\'s algorithm')
    parser.add_argument('--delayed-ack', dest='delayed_ack', action='store_true', default=True,
                        help='Enable Delayed ACK (default: enabled)')
    parser.add_argument('--no-delayed-ack', dest='delayed_ack', action='store_false',
                        help='Disable Delayed ACK')
    
    args = parser.parse_args()
    
    run_client(args.nagle, args.delayed_ack)
