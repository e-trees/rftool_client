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
    buffer_size = 1024
    while True:
        data = client.recv(buffer_size)
        print("[CTRL] Received Data: {}".format(data))
        if data == b'Version\r\n':
            print("send verstion")
            client.send(b" 1.4\r\n")
        elif data == b'disconnect\r\n':
            print("disconnect")
            client.send(b" 1.4\r\n")
            return
        else:
            client.send(b"\r\n")
        
def data_handler(client):
    buffer_size = 1024
    while True:
        data = client.recv(buffer_size)
        print("[CTRL] Received Data: {}".format(data))
        if data == b'':
            return

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

