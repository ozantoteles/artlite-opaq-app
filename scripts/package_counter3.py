import re
from collections import defaultdict
from datetime import datetime
import numpy as np
import json

def load_device_mapping(mapping_file_path):
    with open(mapping_file_path, 'r') as file:
        return json.load(file)

def count_packets(file_path, device_mapping):
    packet_counts = defaultdict(int)
    first_timestamp = None
    last_timestamp = None
    timestamps = defaultdict(list)
    
    with open(file_path, 'r') as file:
        for line in file:
            try:
                timestamp_match = re.search(r'\[(.*?)\]', line)
                match = re.search(r"'UniqueID':\s*'\"([a-fA-F0-9]+)", line)
                if timestamp_match and match:
                    identifier = match.group(1)
                    timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                    
                    packet_counts[identifier] += 1
                    timestamps[identifier].append(timestamp)
                    
                    if first_timestamp is None:
                        first_timestamp = timestamp
                    last_timestamp = timestamp
            except Exception as e:
                # Ignore the line if any error occurs
                print(f"Ignored line due to error: {e}")
                continue
    
    elapsed_time = (last_timestamp - first_timestamp).total_seconds() if first_timestamp and last_timestamp else 0
    
    return packet_counts, elapsed_time, first_timestamp, last_timestamp, timestamps

def generate_ascii_graph(packet_counts, elapsed_time, first_timestamp, last_timestamp, timestamps, device_mapping):
    max_count = max(packet_counts.values())
    min_count = min(packet_counts.values())
    avg_count = sum(packet_counts.values()) / len(packet_counts) if packet_counts else 0
    std_dev_count = np.std(list(packet_counts.values())) if packet_counts else 0
    
    scale_factor = 50 / max_count if max_count > 0 else 1
    
    num_devices = len(packet_counts)
    
    # Calculate packet arrival rate (PPS)
    pps = sum(packet_counts.values()) / elapsed_time if elapsed_time > 0 else 0
    pps_per_device = avg_count / elapsed_time if elapsed_time > 0 else 0
    
    print(f"\nPacket Counts and other Info (Elapsed Time: {elapsed_time:.2f} seconds):")
    print(f"Time Range: {first_timestamp} to {last_timestamp}")
    print(f"Number of Devices: {num_devices}")
    print(f"Average Packet Count per Device: {avg_count:.2f}")
    print(f"Standard Deviation of Packet Counts: {std_dev_count:.2f}")
    print(f"Minimum Packet Count: {min_count}")
    print(f"Maximum Packet Count: {max_count}")
    print(f"Packet Arrival Rate (PPS): {pps:.2f} packets/second")
    print(f"Packet Arrival Rate Per Device: {pps_per_device:.2f} packets/device/second\n")
    
    print(f"{'Identifier':<15} {'Device ID':<12} {'Packet Count':<15} {'Max Gap (s)':<15} {'Avg Gap (s)':<15} {'Min Gap (s)':<15}")
    print("="*90)
    
    for identifier, count in packet_counts.items():
        device_id = device_mapping.get(identifier, "Unknown Device ID")
        time_gaps = [(timestamps[identifier][i+1] - timestamps[identifier][i]).total_seconds() for i in range(len(timestamps[identifier]) - 1)]
        max_gap = max(time_gaps) if time_gaps else 0
        avg_gap = np.mean(time_gaps) if time_gaps else 0
        min_gap = min(time_gaps) if time_gaps else 0
        
        bar_length = int(count * scale_factor)
        print(f"{identifier:<15} {device_id:<12} {count:<15} {max_gap:<15.2f} {avg_gap:<15.2f} {min_gap:<15.2f} {'#' * bar_length}")

def main():
    file_path = '/usr/local/artlite-opaq-app/data/receiver_log_buffer.txt'  # Update with your file path
    mapping_file_path = '/usr/local/artlite-opaq-app/config/device_mapping.json'  # Update with your mapping file path
    
    device_mapping = load_device_mapping(mapping_file_path)
    packet_counts, elapsed_time, first_timestamp, last_timestamp, timestamps = count_packets(file_path, device_mapping)
    
    generate_ascii_graph(packet_counts, elapsed_time, first_timestamp, last_timestamp, timestamps, device_mapping)

if __name__ == "__main__":
    main()
