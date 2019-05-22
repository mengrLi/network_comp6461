import socket
import sys
import threading

import ipaddress
from urllib.parse import urlparse
from packet import Packet

# parameter
# CLIENT


send_buffer = []
timeout = 10
receive_port = 8001
window_size = 8

# server
server_port = 9988
receive_buffer = {}
receive_record = []

# router
router_add = 'localhost'
router_port = 3000

# packet

MAX_LEN = 811
MIN_LEN = 11
is_handshake_success = False

sequence_num = 1

# THREE HANDSAHKE
PACKET_SYN = 0
PACKET_SYN_ACK = 1
PACKET_SYN_ACKACK = 2
# DATA CONTENT
PACKET_ACK = 3
# ONE PACKET IS ENOUGH
PACKET_ONE = 4
# SPLITE DATA INTO MULTI PACKETS
PACKET_DATA = 5
PACKET_START = 6
PACKET_END = 7
PACKET_FIN = 8


def send_packet(data, server_address, server_port):
    global sequence_num
    global send_buffer

    while not is_handshake_success:
        handshake(server_address, server_port)

    ip = ipaddress.ip_address(socket.gethostbyname(server_address))

    if len(data) < MAX_LEN - MIN_LEN:
        packet = Packet(packet_type=PACKET_ONE,
                        seq_num=sequence_num,
                        peer_ip_addr=ip,
                        peer_port=server_port,
                        payload=data.encode("utf-8")
                        )
        sequence_num = (sequence_num + 1) % (2 ** (4 * 8))  #
        send_buffer.append(packet)

    else:

        first_packet = data[:MAX_LEN - 1]
        packet = Packet(packet_type=PACKET_START,
                        seq_num=sequence_num,
                        peer_ip_addr=ip,
                        peer_port=server_port,
                        payload=first_packet.encode("utf-8")
                        )
        sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
        send_buffer.append(packet)
        data = data[MAX_LEN:]

        while len(data) > MAX_LEN - MIN_LEN:
            medium_packet = data[:MAX_LEN - 1]
            packet = Packet(packet_type=PACKET_DATA,
                            seq_num=sequence_num,
                            peer_ip_addr=ip,
                            peer_port=server_port,
                            payload=medium_packet.encode("utf-8")
                            )
            sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
            send_buffer.append(packet)
            data = data[MAX_LEN:]

        # last packet size <maxlen
        packet = Packet(packet_type=PACKET_END,
                        seq_num=sequence_num,
                        peer_ip_addr=ip,
                        peer_port=server_port,
                        payload=data.encode("utf-8")
                        )
        sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
        send_buffer.append(packet)

    if window_size > len(send_buffer):
        window_packs = []
        for packet in send_buffer:
            window_packs.append(packet)
        send_window(window_packs)

    else:
        while len(send_buffer) > window_size:
            window_packs = []
            for i in range(0, window_size):
                window_packs.append(send_buffer[i])
            send_window(window_packs)

            send_buffer = send_buffer[window_size:]
        # left send_buffer size < window size
        window_packs = []
        for packet in send_buffer:
            window_packs.append(packet)
        send_window(window_packs)

    send_buffer.clear()


def send_window(window_packs):
    global timeout

    for packet in window_packs:
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:

            conn.sendto(packet.to_bytes(), (router_add, router_port))
            print('=========send PACKET:' + str(packet.seq_num) + '=========')

            thread = threading.Thread(target=listen_conn, args=(conn, packet))
            thread.start()
            thread.join()
        except Exception as e:
            print("Error: ", e)


def listen_conn(conn, packet):
    global timeout

    try:
        conn.settimeout(timeout)
        response, sender = conn.recvfrom(1024)
        packet = Packet.from_bytes(response)
        # server get the correct msg
        if packet.packet_type == PACKET_ACK:
            print('packet: ' + str(packet.seq_num) + 'send to server successful,receive ack')
    except socket.timeout:
        print(' - Timeout, RESEND- ')

        while packet.packet_type != PACKET_ACK:

            # resend packet
            connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:

                connection.sendto(packet.to_bytes(), (router_add, router_port))
                print('=========timeout,resend PACKET:' + str(packet.seq_num) + '=========')
                connection.settimeout(timeout)
                response, sender = connection.recvfrom(1024)
                packet = Packet.from_bytes(response)
                if packet.packet_type == PACKET_ACK:
                    print('packet: ' + str(packet.seq_num) + 'send to server successful,receive ack')
            except socket.timeout:
                print('- Timeout,RESEND -')

            finally:
                connection.close()

    finally:
        conn.close()


def handshake(server_address, server_port):
    global timeout
    global is_handshake_success

    ip = ipaddress.ip_address(socket.gethostbyname(server_address))
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        data = str(receive_port)
        packet = Packet(packet_type=PACKET_SYN,
                        seq_num=0,
                        peer_ip_addr=ip,
                        peer_port=server_port,
                        payload=data.encode("utf-8"))
        conn.sendto(packet.to_bytes(), (router_add, router_port))
        print('First handshake:(PACKET_SYN) send to server')

        # Try to receive a response within timeout
        conn.settimeout(timeout)
        print('=========Waiting for a response=========')
        response, sender = conn.recvfrom(1024)
        packet = Packet.from_bytes(response)

        if packet.packet_type == PACKET_SYN_ACK:
            print('Second handshake: receive response (SYN_ACK) from server')
            packet = Packet(packet_type=PACKET_SYN_ACKACK,
                            seq_num=0,
                            peer_ip_addr=ip,
                            peer_port=server_port,
                            payload=''.encode("utf-8"))
            conn.sendto(packet.to_bytes(), (router_add, router_port))
            is_handshake_success = True
            print('Third handshake:(PACKET_SYN_ACKACK) send to server, handshake succeed')

    except socket.timeout:
        print('---- Handshake fail ----')
        is_handshake_success = False

    finally:
        conn.close()


def receive():
    global receive_buffer
    global receive_record
    global receive_port
    content = ''
    start_seq = 0
    end_seq = 0
    # to make sure all message is received (deal with message splite into different packets)
    flag = 2

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        conn.bind(('localhost', receive_port))
        print('listening response from server:' + str(receive_port))
        while True:
            data, sender = conn.recvfrom(1024)
            packet = Packet.from_bytes(data)
            packet_ack = Packet(packet_type=PACKET_ACK,
                                seq_num=packet.seq_num,
                                peer_ip_addr=packet.peer_ip_addr,
                                peer_port=packet.peer_port,
                                payload=''.encode("utf-8"))

            conn.sendto(packet_ack.to_bytes(), sender)
            conn.sendto(packet_ack.to_bytes(), sender)
            conn.sendto(packet_ack.to_bytes(), sender)

            if packet.seq_num in receive_record:
                print('repeat  response' + str(packet.seq_num))
                packet_ack = Packet(packet_type=PACKET_ACK,
                                    seq_num=packet.seq_num,
                                    peer_ip_addr=packet.peer_ip_addr,
                                    peer_port=packet.peer_port,
                                    payload=''.encode("utf-8"))

                conn.sendto(packet_ack.to_bytes(), sender)

            else:
                receive_record.append(packet.seq_num)
                print('response from server, No.' + str(packet.seq_num))
                # ONLY ONE PACKET IS ALL MESSAGE
                if packet.packet_type == PACKET_ONE:
                    content = packet.payload.decode("utf-8")

                    #  print ('content is:'+content)
                    break


                else:
                    print("Receiving multiple package .........................")
                    receive_buffer[packet.seq_num] = packet
                    if packet.packet_type == PACKET_START:
                        start_seq = packet.seq_num
                        flag -= 1
                    if packet.packet_type == PACKET_END:
                        end_seq = packet.seq_num
                        flag -= 1
                    if flag > 0:
                        continue

                    if check_integrate(start_seq, end_seq, receive_buffer):
                        content = ''
                        for i in range(start_seq, end_seq + 1):
                            content += receive_buffer[i].payload.decode("utf-8")
                            # print(content)

                        packet_fin = Packet(packet_type=PACKET_FIN,
                                            seq_num=end_seq + 1,
                                            peer_ip_addr=packet.peer_ip_addr,
                                            peer_port=packet.peer_port,
                                            payload=''.encode("utf-8"))

                        conn.sendto(packet_fin.to_bytes(), sender)



                        #  print ('content is:'+content)
                        break



    except Exception as e:
        print("Error", e)
    finally:
        conn.close()
    return content


def check_integrate(start_seq, end_seq, receive_buffer):
    flag = True
    for i in range(start_seq, end_seq + 1):
        if i not in receive_buffer.keys():
            flag = False
    return flag


# assignment 1#
def get(url, headers, is_v, o_filepath):
    # print url
    urlResult = urlparse(url)
    host_name = 'localhost'
    parameters = urlResult.query
    path = urlResult.path

    head_msg = ''
    if bool(headers):
        for k, v in headers.items():
            head_msg = head_msg + k + ': ' + v + '\r\n'

    rqst_msg = 'GET ' + path
    if len(parameters) > 0:
        rqst_msg = rqst_msg + '?' + parameters

    request = rqst_msg + ' HTTP/1.0\r\n' + 'Host: ' + host_name + '\r\n' + head_msg + '\r\n'

    print('==========request message is: ==========')
    print(request)

    send_packet(request, host_name, server_port)
    resp = receive()

    # send
    print("****************************responds message*********************", resp)
    split_index = resp.find('\r\n\r\n') + 4
    resp_content = resp[split_index:]

    if len(o_filepath) > 0:
        output_2_file(o_filepath, resp_content)

    else:
        if not is_v:
            print('==========Response message is:==========')
            sys.stdout.write(resp_content + '\r\n')
        else:
            print('==========Response message is:==========')
            sys.stdout.write(resp + '\r\n')






def post(url, headers, is_v, o_filepath, file, data):
    urlResult = urlparse(url)
    host_name = 'localhost'
    parameters = urlResult.query
    path = urlResult.path

    head_msg = ''
    if bool(headers):
        for k, v in headers.items():
            head_msg = head_msg + k + ': ' + v + '\r\n'

    rqst_msg = 'POST ' + path
    if len(parameters) > 0:
        rqst_msg = rqst_msg + '?' + parameters

    message_body = ''
    if len(data) > 0:
        # print "aaa"+data
        message_body = message_body + data
    if len(file) > 0:
        with open(file) as file_obj:
            file_content = file_obj.read().rstrip()
            message_body = message_body + file_content

    rqst_msg = rqst_msg + ' HTTP/1.0\r\n' + 'Host: ' + host_name + '\r\nContent-Length: ' + str(
        len(message_body)) + '\r\n' + head_msg + '\r\n'
    request = rqst_msg + message_body
    print('==========request message is: ==========')
    print(request)

    # send

    send_packet(request, host_name, server_port)

    resp = receive()


    split_index = resp.find('\r\n\r\n') + 4
    resp_content = resp[split_index:]
    # print resp_content
    if len(o_filepath) > 0:
        # print len(o_filepath)
        output_2_file(o_filepath, resp_content)

    else:
        if not is_v:
            print('==========Response message is:==========')
            sys.stdout.write(resp_content + '\r\n')
        else:
            print('==========Response message is:==========')
            sys.stdout.write(resp + '\r\n')


def output_2_file(file_path, content):
    with open(file_path, 'w') as file_obj:
        file_obj.write(content)
