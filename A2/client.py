import socket
import select
import sys
from tkinter import *
from _thread import *

send_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
recv_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#acknowledgement for the server that the 
#message has been received successfully
def make_ack_packet(sender_name):
    packet = "RECEIVED {}\n\n".format(sender_name)
    return packet.encode()

#packet for error 103 (header incomplete)
def make_error_packet():
    packet = "ERROR 103 Header Incomplete\n\n"
    return packet.encode()


class ChatBox():
    def __init__(self, top):
        self.top = top
        self.frame = Frame(self.top)
        self.frame.grid()
        self.messages = Text(self.frame)
        self.messages.pack()
        self.input_user = StringVar()
        self.input_field = Entry(self.frame, text=self.input_user)
        self.input_field.pack(side=BOTTOM, fill=X)
        self.input_field.bind("<Return>", self.Enter_pressed)
        return

    def encapsulate(self, message):
    
        msg_arr = message.split(" ", 1)
        recepient = msg_arr[0][1:]

        message = msg_arr[1]
        self.addMessage("You: {}".format(message))

        length = sys.getsizeof(message)
        packet = "SEND {}\nContent-length: {}\n\n{}".format(recepient, length, message)
        return packet.encode()

    def Enter_pressed(self,event):
        input_get = self.input_field.get()
        packet = self.encapsulate(input_get)
        self.input_user.set('')
        send_client.send(packet)
        return "break"
        
    def addMessage(self, message):
        self.messages.insert(INSERT, '%s\n' % message)

class MakeFrame():
    def __init__(self, top):
        self.top=top
        self.top.geometry("+15+15")
        self.frame=Frame(self.top)
        self.frame.grid()
        self.lbl_title = Label(self.frame, text = "Welcome to Chatty", font = ("Arial Bold",20))
        self.lbl_title.grid(column = 0, row = 0, columnspan = 2, ipadx = 30)

        self.lbl_ip = Label(self.frame, text = "Server IP")
        self.lbl_ip.grid(column = 0, row = 1, sticky='W', pady = 20, padx = 3)
        self.txt_ip = Entry(self.frame, width = 15)
        self.txt_ip.grid(column = 1, row = 1, sticky='W', pady = 20)

        self.lbl_port = Label(self.frame, text = "Server port")
        self.lbl_port.grid(column = 0, row = 2, sticky='W', padx = 3)
        self.txt_port = Entry(self.frame, width = 5)
        self.txt_port.grid(column = 1, row = 2, sticky='W')

        self.user = Label(self.frame, text = "Username")
        self.user.grid(column = 0, row = 3, sticky='W', pady = 20, padx = 3)
        self.user_txt = Entry(self.frame, width = 15)
        self.user_txt.grid(column = 1, row = 3, sticky='W', pady = 20)

        self.btn = Button(self.frame, text = "Connect", bg = "black", fg = "white", command = self.connect, font = ("Arial",14))
        self.btn.grid(column = 0, row = 4, columnspan = 2, pady = 20)

    def destroy(self):
        self.frame.destroy()
        self.chat_frame=ChatBox(self.top)
        start_new_thread(self.listen,())

    def connect(self):
        ip = self.txt_ip.get()
        port = int(self.txt_port.get())
  
        send_client.connect((ip,port))
        packet = "REGISTER TOSEND {}\n \n".format(self.user_txt.get())
        send_client.send(packet.encode())
        message = send_client.recv(1024)
        message = message.decode("utf-8")

        if message[0] == "R":
            recv_client.connect((ip, port))
            packet = "REGISTER TORECV {}\n \n".format(self.user_txt.get())
            recv_client.send(packet.encode())
            message = recv_client.recv(1024)
            message = message.decode("utf-8")
            self.destroy()  
        else:
            match = re.match(r'ERROR ([0-9]+) (.*)', message)
            error_num = int(match.group(1))
            print(message)
            if error_num == 100:
                exit()      
        
    def listen(self):
        while True:
            sockets_list = [sys.stdin, recv_client]
            read_sockets,write_socket, error_socket = select.select(sockets_list,[],[]) 
            for socks in read_sockets: 
                if socks == recv_client: 
                    packet = recv_client.recv(1024) 
                    packet = packet.decode("utf-8")

                    if packet:
                        try:
                            if packet[0] == 'F':
                                match = re.match(r'FORWARD ([a-zA-Z0-9]+)\nContent-length: ([0-9]+)\n\n(.*)', packet)
                                sender = match.group(1)
                                content_length = int(match.group(2))
                                message = match.group(3)
                                
                                if content_length == sys.getsizeof(message):
                                    self.chat_frame.addMessage("{}: {}".format(sender, message))
                                    packet = "RECEIVED {}\n\n".format(sender)
                                    packet = packet.encode()
                                    send_client.send(packet)
                                else:
                                    packet = "ERROR 103 Header incomplete\n\n".encode()
                                    send_client.send(packet)

                            elif packet[0] == 'S':
                                continue

                            else:
                                print(packet)
                                continue
                        except:
                            packet = "ERROR 103 Header incomplete\n\n".encode()
                            send_client.send(packet)

root = Tk()
root.title("ChatBox")
user_frame = MakeFrame(root)
root.mainloop()
