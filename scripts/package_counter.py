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

def generate_ascii_graph(packet_counts):
    max_count = max(packet_counts.values())
    scale_factor = 50 / max_count if max_count > 0 else 1
    
    print("\nASCII Graph of Packet Counts:")
    for identifier, count in packet_counts.items():
        bar_length = int(count * scale_factor)
        print(f"{identifier}: {'#' * bar_length} ({count})")

def main():
    #file_path = 'D:\\Work\\plm\\Workground\\artlite-opaq-app\\data\\receiver_log_buffer.txt'  # Update with your file path
    file_path = '/usr/local/artlite-opaq-app/data/receiver_log_buffer.txt'  # Updated with your file path

    packet_counts = count_packets(file_path)
    
    print("Packet counts per unique identifier:")
    for identifier, count in packet_counts.items():
        print(f"{identifier}: {count}")
    
    generate_ascii_graph(packet_counts)

if __name__ == "__main__":
    main()
