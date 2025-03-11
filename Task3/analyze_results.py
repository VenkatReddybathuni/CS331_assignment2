import csv
import matplotlib.pyplot as plt
import pandas as pd
import os

def load_results(filename="tcp_performance_results.csv"):
    """Load results from CSV file"""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found")
        return None
    
    df = pd.read_csv(filename)
    return df

def plot_comparison(df):
    """Generate comparison plots for all metrics"""
    if df is None or df.empty:
        print("No data to analyze")
        return
    
    # Ensure we have the right columns
    required_columns = ['Configuration', 'Throughput (bytes/s)', 'Goodput (bytes/s)', 
                       'Packet Loss Rate', 'Max Packet Size (bytes)']
    
    for col in required_columns:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            return
    
    # Set up the plots
    metrics = [
        'Throughput (bytes/s)',
        'Goodput (bytes/s)', 
        'Packet Loss Rate', 
        'Max Packet Size (bytes)'
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    
    # Plot each metric
    for i, metric in enumerate(metrics):
        ax = axes[i]
        df.plot(kind='bar', x='Configuration', y=metric, ax=ax, legend=False)
        ax.set_title(metric)
        ax.set_ylabel(metric)
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on top of each bar
        for p in ax.patches:
            ax.annotate(f"{p.get_height():.2f}", 
                      (p.get_x() + p.get_width() / 2., p.get_height()), 
                      ha='center', va='baseline', fontsize=9, color='black', xytext=(0, 5),
                      textcoords='offset points')
    
    plt.tight_layout()
    plt.savefig('tcp_performance_comparison.png', dpi=300, bbox_inches='tight')
    print("Comparison plot saved as tcp_performance_comparison.png")

def analyze_results():
    """Analyze and print summary of results"""
    df = load_results()
    if df is None:
        return
    
    # Print summary of results
    print("\nSummary of TCP Performance Results:\n")
    print(df.to_string(index=False))
    
    # Generate comparison with explanations
    print("\nComparison of TCP Configurations:")
    
    # Find best performing configuration for each metric
    best_throughput = df.loc[df['Throughput (bytes/s)'].idxmax()]['Configuration']
    best_goodput = df.loc[df['Goodput (bytes/s)'].idxmax()]['Configuration']
    least_loss = df.loc[df['Packet Loss Rate'].idxmin()]['Configuration']
    largest_packet = df.loc[df['Max Packet Size (bytes)'].idxmax()]['Configuration']
    
    print(f"- Best Throughput: {best_throughput}")
    print(f"- Best Goodput: {best_goodput}")
    print(f"- Lowest Packet Loss Rate: {least_loss}")
    print(f"- Largest Maximum Packet Size: {largest_packet}")
    
    # Create visualization
    plot_comparison(df)
    
    # Provide analysis and explanation
    print("\nAnalysis of Nagle's Algorithm and Delayed ACK Effect:")
    print("1. Nagle's algorithm aims to reduce small packet overhead by buffering small segments.")
    print("2. Delayed ACK reduces ACK traffic by acknowledging multiple segments at once.")
    print("3. When both are enabled, they can create a 'deadlock' causing delays.")
    print("4. Disabling Nagle's algorithm improves responsiveness for interactive applications.")
    print("5. Disabling Delayed ACK improves response time but increases network traffic.")
    print("6. The configuration with both disabled typically provides the best responsiveness")
    print("   but may not be the most network-efficient option.")

if __name__ == "__main__":
    analyze_results()
