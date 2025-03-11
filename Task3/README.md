# Nagle's Algorithm Analysis

This project analyzes the effect of Nagle's algorithm on TCP/IP performance by comparing different 
combinations of Nagle's algorithm and Delayed-ACK settings.

## Requirements

- Python 3.6+
- matplotlib
- pandas

Install the required packages:

```bash
pip install matplotlib pandas
```

## Files

- `server.py` - TCP server that receives data and tracks metrics
- `client.py` - TCP client that sends data at 40 bytes/second
- `analyze_results.py` - Analyzes and visualizes the results
- `run_experiments.py` - Automation script to run all configurations
- `tcp_performance_results.csv` - Generated CSV file with test results
- `tcp_performance_comparison.png` - Generated comparison chart

## Running the Experiments

To run all four configurations of tests automatically:

```bash
python run_experiments.py
```

To run a specific configuration manually:

1. Start the server (in one terminal):
   ```bash
   # For Nagle enabled, Delayed-ACK enabled:
   python server.py
   
   # For Nagle disabled, Delayed-ACK enabled:
   python server.py --no-nagle
   
   # For Nagle enabled, Delayed-ACK disabled:
   python server.py --no-delayed-ack
   
   # For Nagle disabled, Delayed-ACK disabled:
   python server.py --no-nagle --no-delayed-ack
   ```

2. Start the client (in another terminal):
   ```bash
   # For Nagle enabled, Delayed-ACK enabled:
   python client.py
   
   # For Nagle disabled, Delayed-ACK enabled:
   python client.py --no-nagle
   
   # For Nagle enabled, Delayed-ACK disabled:
   python client.py --no-delayed-ack
   
   # For Nagle disabled, Delayed-ACK disabled:
   python client.py --no-nagle --no-delayed-ack
   ```

## Analysis

After running the experiments, view the results:

```bash
python analyze_results.py
```

The analysis includes:
- Throughput comparison
- Goodput comparison  
- Packet loss rate comparison
- Maximum packet size comparison

A visual comparison is saved as `tcp_performance_comparison.png`.

## Expected Observations

1. **Nagle Enabled, Delayed-ACK Enabled**: Can create a "deadlock" situation where the sender waits for ACKs while the receiver delays them. This typically results in poor performance for small, interactive transfers.

2. **Nagle Enabled, Delayed-ACK Disabled**: Offers better performance than the first configuration as ACKs are not delayed, reducing sender waiting time.

3. **Nagle Disabled, Delayed-ACK Enabled**: Better for interactive applications where small packets need to be sent promptly, even if they're not full-sized.

4. **Nagle Disabled, Delayed-ACK Disabled**: Often provides the best responsiveness but may result in more network overhead due to many small packets and immediate ACKs.
