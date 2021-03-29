import socket
import numpy as np
import datetime
import struct
from typing import NamedTuple


class TestPacketHeader(NamedTuple):
    msgType: np.uint16
    packetStructSize: np.uint16
    packetDataSize: np.uint16

    # static variable
    form_str = '<3H10x'

    def to_bytes(self):
        return struct.pack(self.form_str, self.msgType, self.packetStructSize, self.packetDataSize)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class TestPacketStruct(NamedTuple):
    nnType : int

    # static variable
    form_str = '<i'

    def to_bytes(self):
        return struct.pack(self.form_str, self.nnType)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

packet_dict = {
    1: TestPacketHeader,
    2: TestPacketStruct
}

def recv_test(client_socket):
    recv_buffer = client_socket.recv(4096)

    test_header_bytes = recv_buffer[:16]
    test_header = packet_dict[1].from_bytes(test_header_bytes)

    offset = 16 + test_header.packetStructSize

    test_struct_bytes = recv_buffer[16:offset]
    test_struct = packet_dict[2].from_bytes(test_struct_bytes)
    
    # 수신한 데이터 출력
    print('Recved packet : ' + str(len(recv_buffer)) + ' bytes, {' + str(test_header.msgType) + ', '
          + str(test_header.packetStructSize) + ', '
          + str(test_header.packetDataSize) + '}, {'
          + str(test_struct.nnType) + '}')


def send_test(client_socket):
    send_buffer = bytearray(4096)

    # 'class in dict' Test
    test_struct = packet_dict[2](128)
    test_struct_bytes = test_struct.to_bytes()
    test_header = packet_dict[1](1, len(test_struct_bytes), 0)
    test_header_bytes = test_header.to_bytes()

    # 바이트 복사 후 전송
    send_buffer[0:] = test_header_bytes
    send_buffer[16:] = test_struct_bytes
    sent = client_socket.send(send_buffer)
    
    # 전송한 데이터 출력
    print('Sended packet : ' + str(sent) + ' bytes, {' + str(test_header.msgType) + ', '
          + str(test_header.packetStructSize) + ', '
          + str(test_header.packetDataSize) + '}, {'
          + str(test_struct.nnType) + '}')

def server_init():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('127.0.0.1', 9999))
    server_socket.listen(1)
    return server_socket

def accept_client():
    print('Waiting for client')
    client_socket, addr = server_socket.accept()  # 클라이언트 접속 accept
    print('Connected by :', addr[0], ':', addr[1], 'Log time : ', datetime.datetime.now())
    return client_socket

if __name__ == "__main__":
    server_socket = server_init()
    client_socket = accept_client()
    recv_test(client_socket)
    send_test(client_socket)



