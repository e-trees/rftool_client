# -*- coding : UTF-8 -*-

import sys
import socket
import threading

def init_server(port, listen_num=5):
    print("start_server port={}".format(port))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(listen_num)
    return server

def start_server(server, body):
    client, address = server.accept()
    print("[*] Connected: client={}]".format(address))
    body(client)

def ctrl_handler(client):
    global ctrl_client
    buffer_size = 1024
    bitstream = 0
    while True:
        data = client.recv(buffer_size)
        print("[CTRL] Received Data: {}".format(data))
        s = data.decode()
        if s.startswith("disconnect"):
            client.send(b' 1.4\r\n')
            return
        elif s.startswith("Version"):
            client.send(b' 1.4\r\n')
        elif s.startswith("GetBitstream"):
            client.send(b' 1 1\r\n')
        elif s.startswith("SetBitstream"):
            values = s.split(" ")
            bitstream = int(values[1])
            client.send(b' 1 1\r\n')
        elif s.startswith("GetTriggerStatus"):
            client.send(b' GetTriggerStatus 0 \r\n')
        elif s.startswith("GetIntrStatus"):
            client.send(b' GetIntrStatus 0 0 0 0\r\n')
        else:
            client.send(b' unknown \r\n')
        
def data_handler(client):
    buffer_size = 65536*2
    while True:
        data = client.recv(buffer_size)
        print("[DATA] Received Data: {}".format(data))
        try:
            if data == b'':
                return
            s = data.decode()
            if s.startswith('ReadDataFromMemory'):
                values = s.split(" ")
                reply_len = int(values[3])
                reply_dat = b'0' * reply_len
                print(reply_dat)
                client.send(reply_dat + b'\r\n')
                client.send(b' ReadDataFromMemory \r\n')
        except UnicodeDecodeError:
            if data == b'':
                return
            else:
                client.send(b' data recv \r\n')

ctrl_server = init_server(8081)
ctrl_thread = threading.Thread(target=start_server, args=(ctrl_server,ctrl_handler))

data_server = init_server(8082)
data_thread = threading.Thread(target=start_server, args=(data_server,data_handler))

ctrl_thread.start()
data_thread.start()

ctrl_thread.join()
data_thread.join()

ctrl_server.shutdown(socket.SHUT_RDWR)
data_server.shutdown(socket.SHUT_RDWR)

ctrl_server.close()
data_server.close()

ctrl_server = None
data_server = None

