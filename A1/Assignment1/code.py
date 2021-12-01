import socket
import time
import struct
import select
import math
import random
from matplotlib import pyplot as plt

ICMP_ECHO_REQUEST = 8
ICMP_CODE = socket.getprotobyname('icmp')

def check_sum(source_string):
    sum = 0
    count_to = (len(source_string) / 2) * 2
    count = 0
    while count < count_to:
        this_val = (source_string[count + 1])*256 + (source_string[count])
        sum = sum + this_val
        sum = sum & 0xffffffff 
        count = count + 2
    if count_to < len(source_string):
        sum = sum + (source_string[len(source_string) - 1])
        sum = sum & 0xffffffff 
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def create_packet(id):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, id, 1)
    data = ''
    my_checksum = check_sum(header + data.encode('utf-8'))
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0,socket.htons(my_checksum), id, 1)
    return header + data.encode('utf-8')

def traceroute(name):
	
	host = socket.gethostbyname(name)
	print("Traceroute to " + name + ' (' + host + '), ' + "30 hops max")

	data = [[],[]]
	for ttl in range(1, 31):
		sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, ICMP_CODE)
		sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)

		packet_id = int(random.random() * 65535)
		
		packet = create_packet(packet_id)
		sock.sendto(packet, (host, 1))
		start = time.time()

		time_out  = 3
		time_left = time_out
		address = ""

		while True:
			
			started_select = time.time()
			ready = select.select([sock], [], [], time_left)
			how_long_in_select = time.time() - started_select
			if ready[0] == []: 
				data[0].append(ttl)
				data[1].append(0)
				if address == "":
					print(ttl, " * *")
				else:
					print(ttl, address, "*")
				break

			end = time.time()
			rec_packet, addr = sock.recvfrom(1024)
			address = addr[0]
			icmp_header = rec_packet[-8:]
			type, code, checksum, p_id, sequence = struct.unpack('bbHHh', icmp_header)
			if p_id == packet_id:
				total_time = (end - start) * 1000
				total_time = math.ceil(total_time * 1000)/1000
				data[0].append(ttl)
				data[1].append(total_time)
				print(ttl, address, total_time,"ms")
				break

		sock.close()
		if address == host:
			break

	return data

name = input()
data = traceroute(name)
plt.xlabel("Number of hops")
plt.ylabel("RTT Values (in ms)")
plt.title("RTT Values vs Number of Hops")
plt.plot(data[0], data[1], 'r', label = "RTT", marker = "o")
plt.legend(bbox_to_anchor=(1,1))
plt.show()
plt.savefig('plot.png')