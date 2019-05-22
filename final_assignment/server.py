import socket
import threading
import ipaddress

import fileprocess
from packet import Packet

# client
send_buffer = []
timeout = 10

window_size = 8

# server

receive_buffer = {}
receive_record = []

# router
router_add = 'localhost'
router_port = 3000

# packet

MAX_LEN = 811
MIN_LEN = 11

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


def run_server(is_v, port, dir_path):
    global receive_buffer
    global receive_record

    client_receive = 0
    is_access = False
    check_integrate = True

    start_seq = 0
    end_seq = 0
    # to make sure all message is received (deal with message splite into different packets)
    flag = 2

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print('========== server is running ==========')
    try:
        conn.bind(('127.0.0.1', port))

        print('Server is listening at ' + str(port))

        while True:
            data, sender = conn.recvfrom(1500)
            packet = Packet.from_bytes(data)
            sender_add = packet.peer_ip_addr
            sender_port = packet.peer_port
            sender_seq = packet.seq_num

            # handshake response, syn-syn_ack, #
            if packet.packet_type == PACKET_SYN:  # receive the first hand shake
                client_receive = int(packet.payload.decode("utf-8"))

                print('Receive first handshake message PACKET_SYN, ' + str(client_receive))
                # second handshake, send PACKET_SYN_ACK
                packet_syn_ack = Packet(packet_type=PACKET_SYN_ACK,
                                        seq_num=0,
                                        peer_ip_addr=sender_add,
                                        peer_port=sender_port,
                                        payload='ACK_SYN'.encode("utf-8"))
                # here sender is router not client
                conn.sendto(packet_syn_ack.to_bytes(), sender)
                print('second handshake:(PACKET_SYN_ack) send to router')

            elif packet.packet_type == PACKET_SYN_ACKACK:
                is_access = True
                print('receive third handshake essage PACKET_SYN_ACKACK, FINISH ')

            elif is_access:  # is_access is true, connection is built
                packet_ack = Packet(packet_type=PACKET_ACK,
                                    seq_num=sender_seq,
                                    peer_ip_addr=sender_add,
                                    peer_port=sender_port,
                                    payload='ACK'.encode("utf-8"))

                conn.sendto(packet_ack.to_bytes(), sender)

                if sender_seq in receive_record:
                    print('repeat  packet' + str(sender_seq))
                    packet_ack = Packet(packet_type=PACKET_ACK,
                                        seq_num=packet.seq_num,
                                        peer_ip_addr=packet.peer_ip_addr,
                                        peer_port=packet.peer_port,
                                        payload=''.encode("utf-8"))

                    conn.sendto(packet_ack.to_bytes(), sender)

                else:
                    receive_record.append(packet.seq_num)
                    print('Receive packet from sender, No.' + str(sender_seq))
                    # ONLY ONE PACKET IS ALL MESSAGE
                    if packet.packet_type == PACKET_ONE:
                        request = packet.payload.decode("utf-8")
                        thread = threading.Thread(target=handle_client, args=(request, client_receive, is_v, dir_path))
                        thread.start()

                        receive_buffer.clear()
                        start_seq = 0
                        end_seq = 0
                    elif packet.packet_type == PACKET_FIN:
                        print('connection finished ....')
                        break

                    else:
                        receive_buffer[sender_seq] = packet
                        if packet.packet_type == PACKET_START:
                            start_seq = sender_seq
                            flag = flag - 1
                        if packet.packet_type == PACKET_END:
                            end_seq = sender_seq
                            flag = flag - 1
                        if flag > 0:
                            continue

                        if check_integrate(start_seq, end_seq, receive_buffer):
                            content = ''
                            for i in range(start_seq, end_seq + 1):
                                content += receive_buffer[i].payload.decode("utf-8")

                            thread = threading.Thread(target=handle_client,
                                                      args=(request, client_receive, is_v, dir_path))
                            thread.start()
                            receive_buffer.clear()
                            start_seq = 0
                            end_seq = 0
                            flag = 2
                            break

    finally:
        conn.close()


def check_integrate(start_seq, end_seq, receive_buffer):
    flag = True
    for i in range(start_seq, end_seq + 1):
        if i not in receive_buffer.keys():
            flag = False
    return flag


def handle_client(data, port, is_v, dir_path):
    # global method, path, recv_header, content_type, recv_body
    receive_addr = 'localhost'
    print('New client from', port)

    if True:
        if not data:
            return
        if is_v:  # print debugging message
            print('----------- Request Message ----------')
            recv_list = data.split('\r\n')
            request_line = recv_list[0].split(' ')
            method = request_line[0]
            path = request_line[1]
            if data.find('Content-Type') >= 0:
                recv_header = ''
                for h in recv_list:
                    if h.find('Content-Type:') != -1:
                        recv_header = h
                recv_header = recv_header[recv_header.find(':') + 1:]
            else:
                # default content-type is text/plain
                recv_header = 'Text/Plain'
            recv_body = ''
            if method == 'POST':
                recv_body_index = data.find('\r\n\r\n') + 4
                recv_body = data[recv_body_index:]
            print('request method: ' + method + '\n' + 'request path: ' + path + '\n' + 'request content type :'
                  + recv_header + '\n' + 'request body: ' + recv_body)

        # separate the path
        respond_message = ''
        status_num = 0
        if method == 'GET':
            if path == '/':
                respond_message, status_num, content_type = fileprocess.Get_file_list(dir_path, recv_header)

            else:
                respond_message, status_num, content_type = fileprocess.Get_file_content(dir_path, path, recv_header)

        if method == 'POST':
            respond_message, status_num, content_type = fileprocess.Post_file(dir_path, path, recv_header, recv_body)

        respond = 'HTTP/1.1 ' + str(status_num) + ' ' + str(status(status_num)) + '\r\n'
        respond = respond + 'Connection: close' + '\r\n' + 'Content-length: ' + str(len(respond_message)) + '\r\n'
        respond = respond + 'Content-Type: ' + content_type
        respond = respond + '\r\n\r\n'
        respond = respond + str(respond_message)
        if is_v:
            print('----------- Respond Message ----------')
            print(respond + '\n')
        send_packet(respond, receive_addr, port)


def status(status_namber):
    status_message = ''
    if status_namber is 200:
        status_message = 'OK'
    elif status_namber is 301:
        status_message = 'Moved Permanently'
    elif status_namber is 400:
        status_message = 'Bad Request'
    elif status_namber is 404:
        status_message = 'Not Found'
    elif status_namber is 505:
        status_message = 'HTTP Version Not Supported'
    return status_message


#  send func#


def send_packet(data, receive_address, receive_port):
    # print("*********************get into send_packet********************")
    global sequence_num
    global send_buffer

    ip = ipaddress.ip_address(socket.gethostbyname(receive_address))

    if len(data) < MAX_LEN - MIN_LEN:
        packet = Packet(packet_type=PACKET_ONE,
                        seq_num=sequence_num,
                        peer_ip_addr=ip,
                        peer_port=receive_port,
                        payload=data.encode("utf-8")
                        )
        sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
        # print("********************len(data)< MAX_LEN-MIN_LEN*********************")
        send_buffer.append(packet)

    else:
        # print("********************len(data)> MAX_LEN-MIN_LEN*********************")
        first_packet = data[:MAX_LEN - 1]
        packet = Packet(packet_type=PACKET_START,
                        seq_num=sequence_num,
                        peer_ip_addr=ip,
                        peer_port=receive_port,
                        payload=first_packet.encode("utf-8")
                        )
        sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
        send_buffer.append(packet)
        data = data[MAX_LEN:]

        while len(data) > MAX_LEN - MIN_LEN:
            # print("********************len(data)> MAX_LEN-MIN_LEN*********************")
            medium_packet = data[:MAX_LEN - 1]
            packet = Packet(packet_type=PACKET_DATA,
                            seq_num=sequence_num,
                            peer_ip_addr=ip,
                            peer_port=receive_port,
                            payload=medium_packet.encode("utf-8")
                            )
            sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
            send_buffer.append(packet)
            data = data[MAX_LEN:]

        # last packet size <maxlen
        packet = Packet(packet_type=PACKET_END,
                        seq_num=sequence_num,
                        peer_ip_addr=ip,
                        peer_port=receive_port,
                        payload=data.encode("utf-8")
                        )
        sequence_num = (sequence_num + 1) % (2 ** (4 * 8))
        # print("********************before send*********************")
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
    # print("********************get into send_window*********************")
    # global timeout

    for packet in window_packs:
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:

            conn.sendto(packet.to_bytes(), (router_add, router_port))
            print('=========send PACKET:' + str(packet.seq_num) + 'to client=========')

            thread = threading.Thread(target=listen_conn, args=(conn, packet))
            thread.start()
            print(packet)

        except Exception as e:
            print("Error: ", e)


def resend_package(packet):
    global timeout
    connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        connection.sendto(packet.to_bytes(), (router_add, router_port))
        print('=========timeout,resend PACKET:' + str(packet.seq_num) + '=========')
        connection.settimeout(timeout)
        response, sender = connection.recvfrom(1500)
        packet = Packet.from_bytes(response)

        if packet.packet_type == PACKET_ACK:
            print('packet: ' + str(packet.seq_num) + 'receive successful, ack')
        elif packet.packet_type == PACKET_FIN:
            print('connection finished......#')
            connection.close()


    except socket.timeout:
        print('- Timeout,RESEND -')
        resend_package(packet)

    finally:
        connection.close()


def listen_conn(conn, packet):
    global timeout
    resend_time = 3
    conn.settimeout(timeout)
    try:

        response, sender = conn.recvfrom(1500)
        packet = Packet.from_bytes(response)
        # server get the correct msg
        if packet.packet_type == PACKET_ACK:
            print('packet: ' + str(packet.seq_num) + 'send to server successful,receive ack')
        elif packet.packet_type == PACKET_FIN:
            print('connection finished')
            conn.close()
    except socket.timeout:
        print(' - Timeout, RESEND- ')

        resend_package(packet)

    finally:
        conn.close()
