# -*- coding : UTF-8 -*-

import sys
import socket
import threading
import struct

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

def recv_data(client, data_len):
    rest_len = data_len
    data = b''
    while rest_len > 0:
        d = client.recv(rest_len)
        print("[DATA] recv_data: len={}".format(len(d)))
        rest_len -= len(d)
    return data

def send_data(client, data):
    rest_len = len(data)
    offset = 0
    while rest_len > 0:
        send_len = rest_len if rest_len < 65536 else 65536
        client.send(data[offset:offset+send_len])
        offset += send_len
        rest_len -= send_len

def send_reply(client, values, ctrl=True):
    s = ' '.join([str(v) for v in values]).encode('utf-8')
    if ctrl:
        print("[CTRL] reply:", s)
    else:
        print("[DATA] reply:", s)
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
            send_reply(client, ['disconnect'])
            return
        elif values[0] == "Version":
            send_reply(client, ['Version', 1.4])
        elif values[0] == "GetBitstreamStatus":
            send_reply(client, ['GetBitStreamStatus', 1])
        elif values[0] == "GetBitstream":
            send_reply(client, ['GetBitStream', bitstream])
        elif values[0] == "SetBitstream":
            bitstream = int(values[1])
            send_reply(client, ['SetBitStream', bitstream])
        elif values[0] == "GetTriggerStatus":
            send_reply(client, ['GetTriggerStatus', 0])
        elif values[0] == "GetIntrStatus":
            send_reply(client, ['GetIntrStatus', 0, 0, 0, 0])
        elif values[0] == "GetCaptureSectionInfo":
            send_reply(client, ["0,128"])
        elif values[0] == "GetAccumulateOverrange":
            send_reply(client, ['GetAccumulateOverrange', 0])
        elif values[0] == "SetExtPllClkRate":
            send_reply(client, ['SetExtPllClkRate', values[1], values[2], values[3]])
        elif values[0] == "DynamicPLLConfig":
            send_reply(client, ['DynamicPLLConfig', values[1], values[2], values[3]])
        elif values[0] == "IsWaveSequenceComplete":
            send_reply(client, [1])
        elif values[0] == "IsCaptureStepSkipped":
            send_reply(client, [0])
        elif values[0] == "IsCaptureDataFifoOverflowed":
            send_reply(client, [0])
        elif values[0] == "IsDoutStepSkipped":
            send_reply(client, [0])
        elif values[0] == "IsAccumulatedValueOverranged":
            send_reply(client, [0])
        else:
            print("[CTRL] undefined:", data)
            send_reply(client, values)

def data_handler(client):
    data_len = 0
    wave_sequence_params = {}
    while True:
        data = recv_command(client)
        if data == b'':
            return
        print("[DATA] Received Data: {}".format(data))
        values = data.decode().strip().split(" ")
        if values[0] == 'ReadDataFromMemory':
            reply_len = int(values[3])
            reply_dat = b'0' * reply_len
            send_data(client, reply_dat)
            send_reply(client, [], ctrl=False)
            send_reply(client, values, ctrl=False)
        elif values[0] == 'ReadDram':
            reply_len = int(values[2])
            reply_dat = b'0' * reply_len
            reply_mesg = "{}".format("AWG_SUCCESS") # [SA_SUCCESS/SA_FAILURE, data size]
            send_reply(client, [reply_mesg], ctrl=False)
            client.send(reply_dat)
            send_reply(client, [], ctrl=False)
            send_reply(client, values, ctrl=False)
        elif values[0] == 'ReadCaptureData':
            reply_len = 128
            reply_mesg = "{},{}".format("AWG_SUCCESS", reply_len) # [SA_SUCCESS/SA_FAILURE, data size]
            send_reply(client, [reply_mesg], ctrl=False)
            reply_dat = b'0' * reply_len
            client.send(reply_dat)
            send_reply(client, values, ctrl=False)
            send_reply(client, values, ctrl=False)
        elif values[0] == 'GetWaveSequenceParams':
            #data = wave_sequence_params[int(values[1])]
            reply_dat = struct.pack('IIdIIII',
                                    1,  # num_wave_step
                                    0,  # is_iq_data
                                    10, # sampling_rate
                                    20, # each_step_param:offset
                                    0,   # each_step_param[body]:step_id
                                    128, # each_step_param[body]:bytes
                                    0,   # each_step_param[body]:infinite_cycle_flag
                                    )
            reply_dat += b'0' * (128*2)
            reply_len = len(reply_dat)
            reply_mesg = "{},{}".format("AWG_SUCCESS", reply_len) # [SA_SUCCESS/SA_FAILURE, data size]
            send_reply(client, [reply_mesg], ctrl=False)
            client.send(reply_dat)
            send_reply(client, values, ctrl=False)
            send_reply(client, values, ctrl=False)
        elif values[0] == 'GetWaveRAM':
            reply_dat = struct.pack('IIIII', 128, 0, 0, 0, 0)
            reply_dat += b'0' * 128
            reply_len = len(reply_dat)
            reply_mesg = "{},{}".format("AWG_SUCCESS", reply_len) # [SA_SUCCESS/SA_FAILURE, data size]
            send_reply(client, [reply_mesg], ctrl=False)
            client.send(reply_dat)
            send_reply(client, values, ctrl=False)
            send_reply(client, values, ctrl=False)
        elif values[0] == 'GetSpectrum':
            reply_len = 128
            reply_mesg = "{},{}".format("SA_SUCCESS", reply_len) # [SA_SUCCESS/SA_FAILURE, data size]
            send_reply(client, [reply_mesg], ctrl=False)
            reply_dat = b'0' * reply_len
            client.send(reply_dat)
            send_reply(client, values, ctrl=False)
            send_reply(client, values, ctrl=False)
        elif values[0] == 'WriteDataToMemory':
            data_len = int(values[3])
            recv_data(client, data_len)
            send_reply(client, values, ctrl=False)
            send_reply(client, [], ctrl=False)
        elif values[0] == 'SetWaveSequence':
            data_len = int(values[4])
            send_reply(client, values, ctrl=False)
            data = recv_data(client, data_len)
            wave_sequence_params[int(values[1])] = data
        elif values[0] == 'SetCaptureConfig':
            data_len = int(values[1])
            send_reply(client, values, ctrl=False)
            recv_data(client, data_len)
        elif values[0] == 'SetDoutSequence':
            data_len = int(values[2])
            send_reply(client, values, ctrl=False)
            recv_data(client, data_len)



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
