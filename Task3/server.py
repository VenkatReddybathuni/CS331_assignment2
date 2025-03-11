import socket
import time
import argparse
import csv
from datetime import datetime

def setup_server(nagle_enabled, delayed_ack_enabled):
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set socket options
    if not nagle_enabled:
        server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    # Set delayed ACK option (platform specific)
    if not delayed_ack_enabled:
        # On Linux:
        try:
            server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        except AttributeError:
            print("TCP_QUICKACK not supported on this platform")
    
    # Bind the socket to the address
    server_address = ('localhost', 10000)
    server_socket.bind(server_address)
    
    # Listen for incoming connections
    server_socket.listen(1)
    
    return server_socket

def run_server(nagle_enabled, delayed_ack_enabled):
    server_socket = setup_server(nagle_enabled, delayed_ack_enabled)
    
    print(f"Server started with Nagle: {'Enabled' if nagle_enabled else 'Disabled'}, "
          f"Delayed-ACK: {'Enabled' if delayed_ack_enabled else 'Disabled'}")
    
    print('Waiting for a connection...')
    connection, client_address = server_socket.accept()
    print(f'Connection from {client_address}')
    
    try:
        # Performance metrics
        start_time = time.time()
        total_bytes = 0
        actual_data_bytes = 0
        packet_count = 0
        lost_packets = 0
        max_packet_size = 0
        
        # Set a timeout for receiving data
        connection.settimeout(1)
        
        expected_size = 4 * 1024  # 4 KB
        data_buffer = bytearray()
        
        # Continue receiving data until we get the entire file or timeout
        running_time = 0
        while running_time < 120:  # ~2 minutes
            try:
                # Receive data
                data = connection.recv(4096)
                if data:
                    packet_size = len(data)
                    packet_count += 1
                    total_bytes += packet_size
                    actual_data_bytes += packet_size
                    max_packet_size = max(max_packet_size, packet_size)
                    data_buffer.extend(data)
                    
                    # If we need to disable delayed ACK for each packet
                    if not delayed_ack_enabled:
                        try:
                            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                        except AttributeError:
                            pass
                else:
                    # No data received, might be end of transmission
                    break
            except socket.timeout:
                lost_packets += 1
            
            running_time = time.time() - start_time
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate performance metrics
        throughput = total_bytes / duration if duration > 0 else 0  # bytes/second
        goodput = min(len(data_buffer), expected_size) / duration if duration > 0 else 0  # bytes/second
        loss_rate = lost_packets / (packet_count + lost_packets) if (packet_count + lost_packets) > 0 else 0
        
        # Save metrics to a CSV file
        config_name = f"nagle_{'on' if nagle_enabled else 'off'}_delayack_{'on' if delayed_ack_enabled else 'off'}"
        results = {
            'Configuration': config_name,
            'Throughput (bytes/s)': throughput,
            'Goodput (bytes/s)': goodput,
            'Packet Loss Rate': loss_rate,
            'Max Packet Size (bytes)': max_packet_size,
            'Total Packets': packet_count,
            'Lost Packets': lost_packets,
            'Total Bytes Received': total_bytes,
            'Duration (s)': duration
        }
        
        save_results(results)
        
        print(f"\nPerformance metrics for {config_name}:")
        print(f"Throughput: {throughput:.2f} bytes/second")
        print(f"Goodput: {goodput:.2f} bytes/second")
        print(f"Packet Loss Rate: {loss_rate:.4f}")
        print(f"Maximum Packet Size: {max_packet_size} bytes")
        print(f"Total packets: {packet_count}")
        print(f"Lost packets: {lost_packets}")
        print(f"Total bytes received: {total_bytes}")
        print(f"Duration: {duration:.2f} seconds")
        
    finally:
        connection.close()
        server_socket.close()

def save_results(results):
    filename = "tcp_performance_results.csv"
    file_exists = False
    
    try:
        with open(filename, 'r') as f:
            file_exists = True
    except FileNotFoundError:
        pass
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['Configuration', 'Throughput (bytes/s)', 'Goodput (bytes/s)', 
                     'Packet Loss Rate', 'Max Packet Size (bytes)', 'Total Packets',
                     'Lost Packets', 'Total Bytes Received', 'Duration (s)', 'Timestamp']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # Add timestamp
        results['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TCP Server for Nagle Algorithm Analysis')
    parser.add_argument('--nagle', dest='nagle', action='store_true', default=True, 
                        help='Enable Nagle\'s algorithm (default: enabled)')
    parser.add_argument('--no-nagle', dest='nagle', action='store_false',
                        help='Disable Nagle\'s algorithm')
    parser.add_argument('--delayed-ack', dest='delayed_ack', action='store_true', default=True,
                        help='Enable Delayed ACK (default: enabled)')
    parser.add_argument('--no-delayed-ack', dest='delayed_ack', action='store_false',
                        help='Disable Delayed ACK')
    
    args = parser.parse_args()
    
    run_server(args.nagle, args.delayed_ack)
