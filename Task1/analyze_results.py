
#!/usr/bin/env python

import os
import json
import matplotlib.pyplot as plt
import numpy as np
import subprocess
from scapy.all import rdpcap, TCP
import argparse

def process_iperf_json(file_path):
    """Process iperf3 JSON output file to extract throughput data"""
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
            
            # Initialize result structure
            result = {
                'times': [],
                'throughputs': [],
                'goodput': 0,
                'packet_loss_rate': 0,
                'retransmits': 0
            }
            
            # Extract interval data (standard format)
            if 'intervals' in data and data['intervals']:
                intervals = data.get('intervals', [])
                for interval in intervals:
                    result['times'].append(interval['sum']['start'])
                    result['throughputs'].append(interval['sum']['bits_per_second'] / 1e6)  # Convert to Mbps
            
            # Calculate summary statistics
            if 'end' in data:
                summary = data['end']
                
                # Handle standard format
                if 'sum_sent' in summary:
                    sent_data = summary['sum_sent']
                    result['retransmits'] = sent_data.get('retransmits', 0)
                    
                    total_sent = sent_data.get('bytes', 0)
                    total_time = sent_data.get('seconds', 0)
                    
                    if total_time > 0:
                        result['goodput'] = (total_sent * 8) / total_time / 1e6  # Mbps
                    else:
                        # Alternative calculation for goodput if available directly
                        result['goodput'] = sent_data.get('bits_per_second', 0) / 1e6
                
                # Get packet loss information
                if 'sum' in summary:
                    sum_data = summary['sum']
                    if 'lost_packets' in sum_data and 'packets' in sum_data and sum_data['packets'] > 0:
                        result['packet_loss_rate'] = (sum_data['lost_packets'] / sum_data['packets']) * 100
            
            # If we have goodput but no time series data, create a simple one-point series
            if result['goodput'] > 0 and not result['times']:
                result['times'] = [0]
                result['throughputs'] = [result['goodput']]
            
            return result
            
        except json.JSONDecodeError:
            print(f"Error: Could not parse JSON from {file_path}")
            return None
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None

def analyze_pcap(file_path):
    """Analyze pcap file to extract window size data"""
    try:
        packets = rdpcap(file_path)
        times = []
        window_sizes = []
        
        for packet in packets:
            if TCP in packet:
                # Append packet time
                times.append(packet.time - packets[0].time)  # Relative time
                # Extract window size
                window_sizes.append(packet[TCP].window)
        
        # Calculate maximum window size
        max_window_size = max(window_sizes) if window_sizes else 0
        
        return {
            'times': times,
            'window_sizes': window_sizes,
            'max_window_size': max_window_size
        }
    except Exception as e:
        print(f"Error analyzing pcap file {file_path}: {e}")
        return None

def plot_throughput_over_time(result_dir, congestion_algos):
    """Plot throughput over time for all congestion algorithms"""
    plt.figure(figsize=(10, 6))
    
    has_data = False
    for algo in congestion_algos:
        # Check both naming patterns
        possible_files = [
            os.path.join(result_dir, f'h1_h7_{algo}.json'),
            os.path.join(result_dir, f'iperf3_h1_to_h7_{algo}.json')
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                data = process_iperf_json(file_path)
                if data and data['times'] and data['throughputs']:
                    plt.plot(data['times'], data['throughputs'], label=algo)
                    has_data = True
                break
    
    if not has_data:
        print(f"No valid throughput data found in {result_dir}")
        plt.close()
        return
    
    plt.xlabel('Time (s)')
    plt.ylabel('Throughput (Mbps)')
    plt.title('Throughput over Time')
    plt.legend()
    plt.grid(True)
    
    output_file = os.path.join(result_dir, 'throughput_comparison.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Saved throughput plot to {output_file}")

def plot_window_size_over_time(result_dir, congestion_algos):
    """Plot window size over time for all congestion algorithms"""
    plt.figure(figsize=(10, 6))
    
    has_data = False
    for algo in congestion_algos:
        # Check both naming patterns
        possible_files = [
            os.path.join(result_dir, f'h1_h7_{algo}.pcap'),
            os.path.join(result_dir, f'h1_h7_{algo}.pcap')  # PCAP naming is likely consistent
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                data = analyze_pcap(file_path)
                if data and data['times'] and data['window_sizes']:
                    # Down-sample if there are too many points
                    if len(data['times']) > 1000:
                        indices = np.linspace(0, len(data['times'])-1, 1000, dtype=int)
                        times = [data['times'][i] for i in indices]
                        window_sizes = [data['window_sizes'][i] for i in indices]
                    else:
                        times = data['times']
                        window_sizes = data['window_sizes']
                    
                    plt.plot(times, window_sizes, label=f"{algo} (max: {data['max_window_size']})")
                    has_data = True
                break
    
    if not has_data:
        print(f"No valid window size data found in {result_dir}")
        plt.close()
        return
        
    plt.xlabel('Time (s)')
    plt.ylabel('Window Size (bytes)')
    plt.title('TCP Window Size over Time')
    plt.legend()
    plt.grid(True)
    
    output_file = os.path.join(result_dir, 'window_size_comparison.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Saved window size plot to {output_file}")

def summarize_results(result_dir, congestion_algos):
    """Create summary table of results"""
    results = []
    
    for algo in congestion_algos:
        # Check both naming patterns
        possible_files = [
            os.path.join(result_dir, f'h1_h7_{algo}.json'),
            os.path.join(result_dir, f'iperf3_h1_to_h7_{algo}.json')
        ]
        
        file_path = None
        for path in possible_files:
            if os.path.exists(path):
                file_path = path
                break
                
        if file_path:
            data = process_iperf_json(file_path)
            if data:
                # Check both naming patterns for PCAP
                pcap_paths = [
                    os.path.join(result_dir, f'h1_h7_{algo}.pcap'),
                    os.path.join(result_dir, f'h1_h7_{algo}.pcap')  # PCAP naming is likely consistent
                ]
                
                window_data = {'max_window_size': 'N/A'}
                for pcap_path in pcap_paths:
                    if os.path.exists(pcap_path):
                        window_data = analyze_pcap(pcap_path)
                        break
                
                results.append({
                    'Algorithm': algo,
                    'Goodput (Mbps)': f"{data['goodput']:.2f}",
                    'Packet Loss (%)': f"{data['packet_loss_rate']:.2f}",
                    'Max Window Size': window_data['max_window_size'],
                    'Retransmits': data['retransmits']
                })
    
    # Print summary table
    if results:
        print("\nSummary of Results:")
        print("-" * 80)
        header = results[0].keys()
        print(f"{'Algorithm':<10} {'Goodput (Mbps)':<15} {'Packet Loss (%)':<15} {'Max Window Size':<15} {'Retransmits':<10}")
        print("-" * 80)
        for row in results:
            print(f"{row['Algorithm']:<10} {row['Goodput (Mbps)']:<15} {row['Packet Loss (%)']:<15} {str(row['Max Window Size']):<15} {row['Retransmits']:<10}")
        print("-" * 80)
        
        # Save to file
        with open(os.path.join(result_dir, 'summary.txt'), 'w') as f:
            f.write("Summary of Results:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Algorithm':<10} {'Goodput (Mbps)':<15} {'Packet Loss (%)':<15} {'Max Window Size':<15} {'Retransmits':<10}\n")
            f.write("-" * 80 + "\n")
            for row in results:
                f.write(f"{row['Algorithm']:<10} {row['Goodput (Mbps)']:<15} {row['Packet Loss (%)']:<15} {str(row['Max Window Size']):<15} {row['Retransmits']:<10}\n")
            f.write("-" * 80 + "\n")
            print("done")

def analyze_experiment_b(result_dir, congestion_algos):
    """Analyze staggered client experiment results"""
    print(f"\nAnalyzing staggered client experiment in {result_dir}")
    
    # For each algorithm, create a plot showing the staggered clients
    for algo in congestion_algos:
        plt.figure(figsize=(12, 6))
        
        # Get data for each client
        clients = ['h1', 'h3', 'h4']
        start_times = [0, 15, 30]  # Start times in seconds for each client
        duration = [150, 120, 90]  # Duration in seconds for each client
        
        # Plot each client's throughput
        for i, client in enumerate(clients):
            file_path = os.path.join(result_dir, f'{client}_staggered_{algo}.json')
            if os.path.exists(file_path):
                data = process_iperf_json(file_path)
                if data and data['times'] and data['throughputs']:
                    # Adjust times to reflect staggered start
                    adjusted_times = [t + start_times[i] for t in data['times']]
                    plt.plot(adjusted_times, data['throughputs'], label=f'{client} (start: {start_times[i]}s)')
        
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.title(f'Staggered Clients with {algo.upper()}')
        plt.legend()
        plt.grid(True)
        
        # Draw vertical lines to show when clients start and stop
        for i, client in enumerate(clients):
            plt.axvline(x=start_times[i], color='r', linestyle='--', alpha=0.3)
            plt.axvline(x=start_times[i] + duration[i], color='g', linestyle='--', alpha=0.3)
        
        output_file = os.path.join(result_dir, f'staggered_{algo}_comparison.png')
        plt.savefig(output_file)
        plt.close()
        print(f"Saved staggered client plot for {algo} to {output_file}")
    
    # Analyze total network utilization for each algorithm
    plt.figure(figsize=(12, 6))
    
    for algo in congestion_algos:
        # Load PCAP file for overall analysis
        pcap_file = os.path.join(result_dir, f'staggered_{algo}.pcap')
        if os.path.exists(pcap_file):
            data = analyze_pcap(pcap_file)
            if data and data['times'] and data['window_sizes']:
                # Down-sample if needed
                if len(data['times']) > 1000:
                    indices = np.linspace(0, len(data['times'])-1, 1000, dtype=int)
                    times = [data['times'][i] for i in indices]
                    window_sizes = [data['window_sizes'][i] for i in indices]
                else:
                    times = data['times']
                    window_sizes = data['window_sizes']
                
                plt.plot(times, window_sizes, label=f"{algo}")
    
    plt.xlabel('Time (s)')
    plt.ylabel('TCP Window Size (bytes)')
    plt.title('Window Size Over Time for Staggered Clients')
    plt.legend()
    plt.grid(True)
    output_file = os.path.join(result_dir, 'staggered_window_comparison.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Saved window size comparison to {output_file}")
    
    # Create summary of results
    results = []
    for algo in congestion_algos:
        for client in clients:
            file_path = os.path.join(result_dir, f'{client}_staggered_{algo}.json')
            if os.path.exists(file_path):
                data = process_iperf_json(file_path)
                if data:
                    results.append({
                        'Algorithm': algo,
                        'Client': client,
                        'Goodput (Mbps)': f"{data['goodput']:.2f}",
                        'Retransmits': data['retransmits'],
                        'Packet Loss (%)': f"{data['packet_loss_rate']:.2f}"
                    })
    
    if results:
        # Print and save summary
        with open(os.path.join(result_dir, 'staggered_summary.txt'), 'w') as f:
            f.write("Staggered Clients Experiment Summary:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Algorithm':<10} {'Client':<6} {'Goodput (Mbps)':<15} {'Retransmits':<12} {'Packet Loss (%)':<15}\n")
            f.write("-" * 80 + "\n")
            
            for row in results:
                f.write(f"{row['Algorithm']:<10} {row['Client']:<6} {row['Goodput (Mbps)']:<15} {row['Retransmits']:<12} {row['Packet Loss (%)']:<15}\n")
                print(f"{row['Algorithm']:<10} {row['Client']:<6} {row['Goodput (Mbps)']:<15} {row['Retransmits']:<12} {row['Packet Loss (%)']:<15}")
            
            f.write("-" * 80 + "\n")
        print(f"Saved staggered experiment summary to {result_dir}/staggered_summary.txt")

def analyze_experiment_c(result_dir, congestion_algos):
    """Analyze custom bandwidth experiment results"""
    print(f"\nAnalyzing custom bandwidth experiment in {result_dir}")
    
    # C-I: Link S2-S4 active (H3 -> H7)
    # C-II-a: Link S1-S4 active (H1,H2 -> H7)
    # C-II-b: Link S1-S4 active (H1,H3 -> H7)
    # C-II-c: Link S1-S4 active (H1,H3,H4 -> H7)
    
    # Analysis for each part
    parts = {
        'c1': ['h3'],
        'c2a': ['h1', 'h2'],
        'c2b': ['h1', 'h3'],
        'c2c': ['h1', 'h3', 'h4']
    }
    
    # Create goodput comparison across all parts
    plt.figure(figsize=(15, 8))
    part_names = ['C-I', 'C-II-a', 'C-II-b', 'C-II-c']
    x = np.arange(len(part_names))
    width = 0.2
    offsets = [-width, 0, width]
    
    for i, algo in enumerate(congestion_algos):
        goodputs = []
        
        for part_code, part_name in zip(['c1', 'c2a', 'c2b', 'c2c'], part_names):
            # Calculate average goodput for this part
            total_goodput = 0
            client_count = 0
            
            for client in parts[part_code]:
                file_path = os.path.join(result_dir, f'{client}_{part_code}_{algo}.json')
                if os.path.exists(file_path):
                    data = process_iperf_json(file_path)
                    if data:
                        total_goodput += data['goodput']
                        client_count += 1
            
            avg_goodput = total_goodput / client_count if client_count > 0 else 0
            goodputs.append(avg_goodput)
        
        plt.bar(x + offsets[i], goodputs, width, label=algo)
    
    plt.xlabel('Experiment Configuration')
    plt.ylabel('Average Goodput per Client (Mbps)')
    plt.title('Goodput Comparison in Different Bandwidth Scenarios')
    plt.xticks(x, part_names)
    plt.legend()
    plt.grid(axis='y')
    
    output_file = os.path.join(result_dir, 'bandwidth_goodput_comparison.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Saved bandwidth comparison plot to {output_file}")
    
    # Create client comparison for each part and algorithm
    for part_code, clients in parts.items():
        for algo in congestion_algos:
            plt.figure(figsize=(10, 6))
            
            # Process pcap file for this part
            pcap_file = os.path.join(result_dir, f'{part_code}_{algo}.pcap')
            if os.path.exists(pcap_file):
                # Instead of window size, plot throughput from json files
                for client in clients:
                    file_path = os.path.join(result_dir, f'{client}_{part_code}_{algo}.json')
                    if os.path.exists(file_path):
                        data = process_iperf_json(file_path)
                        if data and data['times'] and data['throughputs']:
                            plt.plot(data['times'], data['throughputs'], label=f'{client} throughput')
            
            plt.xlabel('Time (s)')
            plt.ylabel('Throughput (Mbps)')
            plt.title(f'Client Throughput for {part_code} with {algo.upper()}')
            plt.legend()
            plt.grid(True)
            
            output_file = os.path.join(result_dir, f'{part_code}_{algo}_client_comparison.png')
            plt.savefig(output_file)
            plt.close()
            print(f"Saved client comparison for {part_code} with {algo} to {output_file}")
    
    # Create summary table
    results = []
    for part_code, clients in parts.items():
        for algo in congestion_algos:
            for client in clients:
                file_path = os.path.join(result_dir, f'{client}_{part_code}_{algo}.json')
                if os.path.exists(file_path):
                    data = process_iperf_json(file_path)
                    if data:
                        results.append({
                            'Configuration': part_code,
                            'Algorithm': algo,
                            'Client': client,
                            'Goodput (Mbps)': f"{data['goodput']:.2f}",
                            'Retransmits': data['retransmits'],
                            'Packet Loss (%)': f"{data['packet_loss_rate']:.2f}"
                        })
    
    if results:
        # Print and save summary
        with open(os.path.join(result_dir, 'bandwidth_summary.txt'), 'w') as f:
            f.write("Custom Bandwidth Experiment Summary:\n")
            f.write("-" * 100 + "\n")
            f.write(f"{'Configuration':<15} {'Algorithm':<10} {'Client':<6} {'Goodput (Mbps)':<15} {'Retransmits':<12} {'Packet Loss (%)':<15}\n")
            f.write("-" * 100 + "\n")
            
            for row in results:
                f.write(f"{row['Configuration']:<15} {row['Algorithm']:<10} {row['Client']:<6} {row['Goodput (Mbps)']:<15} {row['Retransmits']:<12} {row['Packet Loss (%)']:<15}\n")
                print(f"{row['Configuration']:<15} {row['Algorithm']:<10} {row['Client']:<6} {row['Goodput (Mbps)']:<15} {row['Retransmits']:<12} {row['Packet Loss (%)']:<15}")
            
            f.write("-" * 100 + "\n")
        print(f"Saved bandwidth experiment summary to {result_dir}/bandwidth_summary.txt")

def analyze_packet_loss_experiment(result_dir, congestion_algos, loss_rate):
    """Analyze packet loss experiment results"""
    print(f"\nAnalyzing {loss_rate}% packet loss experiment in {result_dir}")
    
    clients = ['h1', 'h3', 'h4']
    
    # Aggregate throughput by algorithm
    plt.figure(figsize=(12, 6))
    
    for algo in congestion_algos:
        avg_throughputs = {}  # time -> throughput
        client_count = 0
        
        for client in clients:
            file_path = os.path.join(result_dir, f'{client}_d_{loss_rate}_{algo}.json')
            if os.path.exists(file_path):
                data = process_iperf_json(file_path)
                if data and data['times'] and data['throughputs']:
                    client_count += 1
                    for t, tp in zip(data['times'], data['throughputs']):
                        if t not in avg_throughputs:
                            avg_throughputs[t] = 0
                        avg_throughputs[t] += tp
        
        if client_count > 0:
            # Average the throughputs
            times = sorted(avg_throughputs.keys())
            throughputs = [avg_throughputs[t] / client_count for t in times]
            
            plt.plot(times, throughputs, label=f"{algo}")
    
    plt.xlabel('Time (s)')
    plt.ylabel('Average Throughput per Client (Mbps)')
    plt.title(f'Average Throughput with {loss_rate}% Packet Loss')
    plt.legend()
    plt.grid(True)
    
    output_file = os.path.join(result_dir, f'throughput_comparison_{loss_rate}pct_loss.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Saved throughput comparison for {loss_rate}% loss to {output_file}")
    
    # Compare retransmission rates across algorithms
    retransmits_by_algo = {algo: 0 for algo in congestion_algos}
    goodput_by_algo = {algo: 0 for algo in congestion_algos}
    total_clients = {algo: 0 for algo in congestion_algos}
    
    for algo in congestion_algos:
        for client in clients:
            file_path = os.path.join(result_dir, f'{client}_d_{loss_rate}_{algo}.json')
            if os.path.exists(file_path):
                data = process_iperf_json(file_path)
                if data:
                    retransmits_by_algo[algo] += data['retransmits']
                    goodput_by_algo[algo] += data['goodput']
                    total_clients[algo] += 1
    
    # Plot retransmissions comparison
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(congestion_algos))
    width = 0.35
    
    # Plot retransmissions
    retrans_data = [retransmits_by_algo[algo] / total_clients[algo] if total_clients[algo] > 0 else 0 for algo in congestion_algos]
    bars1 = ax1.bar(x - width/2, retrans_data, width, label='Avg Retransmissions')
    ax1.set_xlabel('Congestion Control Algorithm')
    ax1.set_ylabel('Average Retransmissions per Client')
    
    # Add second y-axis for goodput
    ax2 = ax1.twinx()
    goodput_data = [goodput_by_algo[algo] / total_clients[algo] if total_clients[algo] > 0 else 0 for algo in congestion_algos]
    bars2 = ax2.bar(x + width/2, goodput_data, width, label='Avg Goodput', color='orange')
    ax2.set_ylabel('Average Goodput per Client (Mbps)')
    
    # Add labels
    ax1.set_title(f'Performance with {loss_rate}% Packet Loss')
    ax1.set_xticks(x)
    ax1.set_xticklabels(congestion_algos)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    output_file = os.path.join(result_dir, f'performance_comparison_{loss_rate}pct_loss.png')
    plt.savefig(output_file)
    plt.close()
    print(f"Saved performance comparison for {loss_rate}% loss to {output_file}")
    
    # Create summary table
    results = []
    for algo in congestion_algos:
        for client in clients:
            file_path = os.path.join(result_dir, f'{client}_d_{loss_rate}_{algo}.json')
            if os.path.exists(file_path):
                data = process_iperf_json(file_path)
                if data:
                    results.append({
                        'Algorithm': algo,
                        'Client': client,
                        'Goodput (Mbps)': f"{data['goodput']:.2f}",
                        'Retransmits': data['retransmits'],
                        'Packet Loss (%)': f"{data['packet_loss_rate']:.2f}"
                    })
    
    if results:
        # Print and save summary
        with open(os.path.join(result_dir, f'loss_{loss_rate}pct_summary.txt'), 'w') as f:
            f.write(f"{loss_rate}% Packet Loss Experiment Summary:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Algorithm':<10} {'Client':<6} {'Goodput (Mbps)':<15} {'Retransmits':<12} {'Packet Loss (%)':<15}\n")
            f.write("-" * 80 + "\n")
            
            for row in results:
                f.write(f"{row['Algorithm']:<10} {row['Client']:<6} {row['Goodput (Mbps)']:<15} {row['Retransmits']:<12} {row['Packet Loss (%)']:<15}\n")
                print(f"{row['Algorithm']:<10} {row['Client']:<6} {row['Goodput (Mbps)']:<15} {row['Retransmits']:<12} {row['Packet Loss (%)']:<15}")
            
            f.write("-" * 80 + "\n")
        print(f"Saved {loss_rate}% loss experiment summary to {result_dir}/loss_{loss_rate}pct_summary.txt")

def main():
    parser = argparse.ArgumentParser(description='Analyze TCP congestion control experiment results')
    parser.add_argument('--experiment', choices=['a', 'b', 'c', 'd1', 'd5', 'all'], default='all',
                      help='Experiment results to analyze')
    
    args = parser.parse_args()
    experiment = args.experiment
    
    congestion_algos = ['cubic', 'vegas', 'htcp']
    
    if experiment == 'a' or experiment == 'all':
        result_dir = 'results/experiment_a'
        if os.path.exists(result_dir):
            plot_throughput_over_time(result_dir, congestion_algos)
            plot_window_size_over_time(result_dir, congestion_algos)
            summarize_results(result_dir, congestion_algos)
    
    if experiment == 'b' or experiment == 'all':
        result_dir = 'results/experiment_b'
        if os.path.exists(result_dir):
            analyze_experiment_b(result_dir, congestion_algos)
    
    if experiment == 'c' or experiment == 'all':
        result_dir = 'results/experiment_c'
        if os.path.exists(result_dir):
            analyze_experiment_c(result_dir, congestion_algos)
    
    if experiment == 'd1' or experiment == 'all':
        result_dir = 'results/experiment_d_1'
        if os.path.exists(result_dir):
            analyze_packet_loss_experiment(result_dir, congestion_algos, 1)
    
    if experiment == 'd5' or experiment == 'all':
        result_dir = 'results/experiment_d_5'
        if os.path.exists(result_dir):
            analyze_packet_loss_experiment(result_dir, congestion_algos, 5)

    print("Analysis complete!")

if __name__ == '__main__':
    main()
