import subprocess
import time
import os

def run_configuration(nagle, delayed_ack):
    """Run a test with the given configuration"""
    # Get configuration name for output
    nagle_str = "on" if nagle else "off"
    delayed_str = "on" if delayed_ack else "off"
    config_name = f"Nagle {nagle_str}, Delayed-ACK {delayed_str}"
    
    print(f"\n{'='*60}")
    print(f"Starting test with {config_name}")
    print(f"{'='*60}\n")
    
    # Prepare server command
    server_cmd = ["python", "server.py"]
    if not nagle:
        server_cmd.append("--no-nagle")
    if not delayed_ack:
        server_cmd.append("--no-delayed-ack")
    
    # Prepare client command
    client_cmd = ["python", "client.py"]
    if not nagle:
        client_cmd.append("--no-nagle")
    if not delayed_ack:
        client_cmd.append("--no-delayed-ack")
    
    # Start server
    server_process = subprocess.Popen(server_cmd)
    
    # Give server time to start
    time.sleep(1)
    
    # Run client
    client_process = subprocess.Popen(client_cmd)
    
    # Wait for client to finish
    client_process.wait()
    
    # Give server time to process final data and exit
    time.sleep(2)
    
    # Terminate server if it's still running
    if server_process.poll() is None:
        server_process.terminate()
    
    print(f"\n{'='*60}")
    print(f"Completed test with {config_name}")
    print(f"{'='*60}\n")

def run_all_experiments():
    """Run all four combinations of tests"""
    # Clear previous results file if it exists
    if os.path.exists("tcp_performance_results.csv"):
        os.remove("tcp_performance_results.csv")
    
    # Configuration 1: Nagle enabled, Delayed-ACK enabled
    run_configuration(nagle=True, delayed_ack=True)
    
    # Configuration 2: Nagle enabled, Delayed-ACK disabled
    run_configuration(nagle=True, delayed_ack=False)
    
    # Configuration 3: Nagle disabled, Delayed-ACK enabled
    run_configuration(nagle=False, delayed_ack=True)
    
    # Configuration 4: Nagle disabled, Delayed-ACK disabled
    run_configuration(nagle=False, delayed_ack=False)
    
    # Analyze results
    print("\nAnalyzing results...")
    subprocess.run(["python", "analyze_results.py"])

if __name__ == "__main__":
    run_all_experiments()
