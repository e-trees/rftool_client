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

def recv_command(client):
    data = b''
    while data[-1:] != b'\n':
        d = client.recv(1)
        if d == b'':
            return b''
        data += d
    return data

def recv_data(client, len):
    data = b''
    for i in range(len):
        d = client.recv(1)
        if d == b'':
            return b''
        data += d
    return data

def reply_command(client, values):
    s = ' '.join([str(v) for v in values]).encode('utf-8')
    print("[CTRL] reply:", s)
    client.send(s + b'\r\n')

def ctrl_handler(client):
    bitstream = 0
    while True:
        data = recv_command(client)
        if data == b'':
            return
        print("[CTRL] Received Data: {}".format(data))
        values = data.decode().strip().split(" ")
        if values[0] == "disconnect":
            reply_command(client, ['disconnect'])
            return
        elif values[0] == "Version":
            reply_command(client, ['Version', 1.4])
        elif values[0] == "GetBitstreamStatus":
            reply_command(client, ['GetBitStreamStatus', 1])
        elif values[0] == "GetBitstream":
            reply_command(client, ['GetBitStream', bitstream])
        elif values[0] == "SetBitstream":
            bitstream = int(values[1])
            reply_command(client, ['SetBitStream', bitstream])
        elif values[0] == "GetTriggerStatus":
            reply_command(client, ['GetTriggerStatus', 0])
        elif values[0] == "GetIntrStatus":
            reply_command(client, ['GetIntrStatus', 0, 0, 0, 0])
        elif values[0] == "SetExtPllClkRate":
            reply_command(client, ['SetExtPllClkRate', values[1], values[2], values[3]])
        elif values[0] == "DynamicPLLConfig":
            reply_command(client, ['DynamicPLLConfig', values[1], values[2], values[3]])
        else:
            reply_command(client, ['unknown'])

def data_handler(client):
    data_len = 0
    data_mode = False
    while True:
        if data_mode == False:
            data = recv_command(client)
            if data == b'':
                return
            print("[DATA] Received Data: {}".format(data))
            s = data.decode()
            if s.startswith('ReadDataFromMemory'):
                values = s.split(" ")
                reply_len = int(values[3])
                reply_dat = b'0' * reply_len
                print(reply_dat)
                client.send(reply_dat + b'\r\n')
                client.send(b'ReadDataFromMemory\r\n')
            elif s.startswith('WriteDataToMemory'):
                values = s.split(" ")
                data_len = int(values[3])
                data_mode = True
                client.send(b'WriteDataToMemory\r\n')
        else:
            if data == b'':
                return
            recv_data(client, data_len)
            data_mode = False
            client.send(b'\r\n')


def main():
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

if __name__ == '__main__':
    while True:
        main()
