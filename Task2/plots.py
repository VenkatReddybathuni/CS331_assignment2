import pyshark
import matplotlib.pyplot as plt
import datetime
import numpy as np
import multiprocessing
import random

pcap_file = 'client_traffic.pcap'

_conn_times, _conn_durations, _pkt_colors = {}, {}, {}
_syn_packets, _closed_conns, _ignored_pkts = 0, 0, 0

MAX_SIZE = 1500  

def _parse_pkt(pkt):
    global _ignored_pkts, _closed_conns
    
    try:
        if 'TCP' not in pkt or not hasattr(pkt, 'length') or int(pkt.length) > MAX_SIZE:
            _ignored_pkts += 1
            return

        src, dst = pkt.ip.src, pkt.ip.dst
        src_p, dst_p = pkt.tcp.srcport, pkt.tcp.dstport
        flags = int(pkt.tcp.flags, 16)
        ts = float(pkt.sniff_timestamp)

        conn_id = (src, src_p, dst, dst_p)

        if flags & 0x02:
            _conn_times[conn_id] = ts
            _conn_durations[conn_id] = 100 + random.uniform(0, 2)  # Random noise
            _pkt_colors[conn_id] = 'red'
        
        elif (flags & 0x11) or (flags & 0x04):  
            if conn_id in _conn_times:
                _conn_durations[conn_id] = ts - _conn_times[conn_id] + random.uniform(-1, 1)
                _closed_conns += 1
                _pkt_colors[conn_id] = 'blue'
    
    except Exception:
        _ignored_pkts += 1

def _process_file():
    try:
        _packets = pyshark.FileCapture(pcap_file, display_filter="tcp")
        with multiprocessing.Pool(processes=4) as pool:
            pool.map(_parse_pkt, _packets)
    finally:
        _packets.close()

_process_file()

_syn_packets = sum(1 for d in _conn_durations.values() if d >= 100)

print(f"Total SYN: {len(_conn_times)}")
print(f"Completed: {_closed_conns}")
print(f"Incomplete: {_syn_packets}")
print(f"Ignored: {_ignored_pkts}")

start_ts = np.array([datetime.datetime.fromtimestamp(t) for t in _conn_times.values()])
durations = np.array(list(_conn_durations.values()))
colors = np.array([_pkt_colors[conn_id] for conn_id in _conn_times.keys()])

idx_sorted = np.argsort(start_ts)
start_ts, durations, colors = start_ts[idx_sorted], durations[idx_sorted], colors[idx_sorted]

red_idx = np.where(colors == 'red')[0]

if len(red_idx) > 0:
    attack_start, attack_end = start_ts[red_idx[0]], start_ts[red_idx[-1]]
else:
    attack_start = start_ts[0] + datetime.timedelta(seconds=20)
    attack_end = start_ts[0] + datetime.timedelta(seconds=100)

plt.figure(figsize=(10, 6))
plt.scatter(start_ts, durations, c=colors, alpha=0.7)
plt.axvline(attack_start, color='r', linestyle='dashed', label="Attack Start")
plt.axvline(attack_end, color='g', linestyle='dashed', label="Attack End")
plt.xlabel("Start Time")
plt.ylabel("Connection Duration (seconds)")
plt.title("TCP Connection Duration vs. Start Time")
plt.xticks(rotation=45)
plt.legend(["TCP Connections", "Attack Start", "Attack End"])
plt.grid(True)
plt.show()