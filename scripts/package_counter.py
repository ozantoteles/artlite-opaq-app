import re
from collections import defaultdict

def count_packets(file_path):
    packet_counts = defaultdict(int)
    
    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(r"'UniqueID':\s*'\"([a-fA-F0-9]+)", line)
            if match:
                identifier = match.group(1)
                packet_counts[identifier] += 1
    
    return packet_counts

def main():
    file_path = '/usr/local/artlite-opaq-app/data/receiver_log_buffer.txt'  # Updated with your file path
    packet_counts = count_packets(file_path)
    
    print("Packet counts per unique identifier:")
    for identifier, count in packet_counts.items():
        print(f"{identifier}: {count}")

if __name__ == "__main__":
    main()
