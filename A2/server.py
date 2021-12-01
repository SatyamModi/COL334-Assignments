import socket
import select 
import sys
from _thread import *
import threading
import re

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_ip = "localhost"
port = 5000
server.bind((server_ip, port))
server.listen(100)

broadcast_packet = bytes()
broadcast_sender = ""

client_sockets = {}
num_of_user = 0

b_count = 0

class Client_socket:

	def __init__(self, send_conn, recv_conn, username, broadcasted):
		self.send_sock = send_conn
		self.recv_sock = recv_conn
		self.username = username
		self.broadcast = False

def get_username(client):

	for user in client_sockets:
		if client_sockets[user] == client:
			return user

#encapsulating the packet to be sent to some client
def make_packet(message, sender):
	content_length = sys.getsizeof(message)
	packet = "FORWARD {}\nContent-length: {}\n\n{}".format(sender, content_length, message)
	return packet.encode()

def get_sending_req(client):

	global broadcast_packet
	global broadcast_sender
	
	while True:
		packet = client.send_sock.recv(1024)
		packet = packet.decode("utf-8")

		if packet:
			
			sender_name = get_username(client) 
			try:
				#case when a sending request arrives to server
				if packet[0] == 'S':
					match = re.match(r'SEND ([a-zA-Z0-9]+)\nContent-length: ([0-9]+)\n\n(.*)', packet)
					recepient = match.group(1)
					content_length = int(match.group(2))
					message = match.group(3) 

					if content_length+1 != sys.getsizeof(message):
						packet = "ERROR 103 Header incomplete\n\n".encode()
						recv_sock = client_sockets[sender_name].recv_sock
						recv_sock.send(packet)

					else:
						if recepient in client_sockets:
							recv_sock = client_sockets[recepient].recv_sock
							packet = make_packet(message, sender_name)
							recv_sock.send(packet)	

						else:
							#if the message is to be broadcasted
							if recepient == "ALL":
								broadcast_sender = sender_name
								broadcast_packet = make_packet(message, broadcast_sender)
							
							#if the username is not found
							else:
								packet = "ERROR 102 Unable to send\n\n".encode()
								recv_sock = client.recv_sock
								recv_sock.send(packet)

				elif packet[0] == 'R':
					match = re.match(r'RECEIVED ([a-zA-Z0-9]+)\n\n', packet)
					recepient = match.group(1)
					packet = "SEND {}\n\n".format(recepient)
					packet = packet.encode()
					recv_sock = client_sockets[recepient].recv_sock
					recv_sock.send(packet)

				#case when there is error packet
				else:
					continue

			#when there is some error in header
			except:
				packet = "ERROR 103 Header incomplete\n\n".encode()
				recv_sock = client_sockets[sender_name].recv_sock
				recv_sock.send(packet)

def broadcast(client):

	global broadcast_packet
	global broadcast_sender
	global b_count

	while True:

		if broadcast_packet and broadcast_sender:

			receiver = get_username(client)
			if receiver != broadcast_sender and client.broadcast == False:
				
				client.recv_sock.send(broadcast_packet)
				client.broadcast = True
				b_count += 1

			if b_count == num_of_user-1:
				for user in client_sockets:
					client_sockets[user].broadcast = False
					broadcast_packet = bytes()
					broadcast_sender = ""
					b_count = 0

while True:

	send_conn, addr1 = server.accept()
	packet = send_conn.recv(1024)
	packet = packet.decode("utf-8")
	try:
		match = re.match(r'REGISTER TOSEND (.*?)\n \n', packet)
		username = match.group(1)

		if username.isalnum():
			packet = "REGISTERED TOSEND {}\n \n".format(username)
			send_conn.send(packet.encode()) 
		    
			recv_conn, addr2 = server.accept()
			packet = recv_conn.recv(1024)
			packet = packet.decode("utf-8")

			try:
				match = re.match(r'REGISTER TORECV (.*?)\n \n', packet)
				username = match.group(1)

				if username.isalnum():
					packet = "REGISTERED TORECV {}\n \n".format(username)
					recv_conn.send(packet.encode())  

					client = Client_socket(send_conn, recv_conn, username, False)
					start_new_thread(get_sending_req, (client, ))
					start_new_thread(broadcast, (client, )) 

					client_sockets[username] = client
					num_of_user += 1
				else:
					packet = "ERROR 100 Malformed username\n \n"
					send_conn.send(packet.encode())
					
			except:
				packet = "ERROR 101 No user registered \n \n"
				send_conn.send(packet.encode())

		else:
			packet = "ERROR 100 Malformed username\n \n"
			send_conn.send(packet.encode())
	except:
		packet = "ERROR 101 No user registered \n \n"
		send_conn.send(packet.encode())
