import cv2
import socket
import time
import numpy as np
import Socket_Buffer
from _thread import *
from multiprocessing import Queue
import datetime
import threading
import struct

import ServerConfig
from packet_manager import *


# 접속한 클라이언트 수 관리
class Client_Manager:
    def __init__(self, client_number_max):
        self.client_number_max = client_number_max
        self.curr_client_number = 0
        self.accu_client_number = 0
        self.lock = threading.Lock()

    def get_client_number(self):
        return self.curr_client_number

    # 서버 상태 계산 함수 : 지금은 야매임. 처리 큐 수를 가지고 해야 하는데..
    def get_availability(self):
        client_number = self.get_client_number()

        if (client_number < (self.client_number_max / 10)):
            return ServerStatus.IDLE
        elif (client_number < (self.client_number_max / 5)):
            return ServerStatus.NORMAL
        elif (client_number < (self.client_number_max / 2)):
            return ServerStatus.BUSY
        else:
            return ServerStatus.JAMMED

    # 이모 여기 1인분만 주세요~
    def add_client(self, addr):
        print('Connected by :', addr[0], ':', addr[1], 'Log time : ', datetime.datetime.now())

        self.lock.acquire()
        self.curr_client_number = self.curr_client_number + 1
        self.accu_client_number = self.accu_client_number + 1
        print('Curr Client Numbers : ' + str(self.curr_client_number))
        print('Accu Client Numbers : ' + str(self.accu_client_number))
        self.lock.release()

    # 이모 계산이요~
    def remove_client(self, addr):
        print('Disconnected by ' + addr[0], ':', addr[1], ', Log time : ', datetime.datetime.now())

        self.lock.acquire()
        self.curr_client_number = self.curr_client_number - 1
        print('Curr Client numbers : ' + str(self.curr_client_number))
        self.lock.release()


# 서버 소켓 세팅
def init_server(config):
    # 기본 송수신 버퍼 사이즈 : 65536
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((config.Server_IP, config.Server_Port))
    server_socket.listen(config.CLIENT_MAX)

    return server_socket


# 메인 소켓 서버 쓰레드 함수
def accept_client(server_socket, socketQ, config):
    client_manager = Client_Manager(config.CLIENT_MAX)

    while (True):
        time.sleep(0.1)
        client_socket, addr = server_socket.accept()  # 클라이언트 접속 accept
        client_manager.add_client(addr)
        start_new_thread(recv_thread, (client_socket, addr, socketQ, client_manager, config,))


# 서버 소켓 종료 함수
def close_server(server_socket):
    server_socket.close()  # 서버 소켓 연결 종료


# 전체 클라이언트 소켓 종료 함수
def close_clients(clients):
    for i in range(clients.len):
        clients[i].close()


# 특정 클라이언트 소켓 종료 함수
def close_client(client):
    client.close()


# 딥러닝 서비스 접근 권한 검사하는 함수
def access_check(config, input_code, curr_client_number):
    # 입력된 키 코드 변환
    input_code = input_code.decode('utf-8')
    extract_code = int(input_code[3] + input_code[4])

    # 서버에 설정된 키 코드 변환
    standard_key = config.standard_code[3] + config.standard_code[4]
    standard_key = int(standard_key)

    # 개발자 코드일 경우
    if (config.developer_code[0:8] == input_code[0:8]):
        print('Developer Accessed')

    # 상용화 코드일 경우
    elif (standard_key <= extract_code):
        print('Normal Client Accessed')

    # 적절하지 않은 코드일 경우
    else:
        return AccessResult.REJECT_UNSUITABLE_ACCESS_CODE

    # 현재 클라이언트 수 검사 : 설정한 클라이언트 수 이상이면 접속 거절함
    if (config.CLIENT_MAX <= curr_client_number):
        return AccessResult.REJECT_FULL_CCU

    # 모든 검사 절차 통과
    else:
        return AccessResult.ACCEPT


# 클라이언트 하나 담당해서 데이터 받고 알맞은 신경망의 버퍼에 계속 넣어주는 함수 : 버전 2
def recv_thread(client_socket, addr, socketQ, client_manager, config):
    # 이미지 패킷 조립 클래스 인스턴스
    imagePacketMerger = ImagePacketMerger()

    # 패킷 반응하는 내부 함수
    def packet_react(header, struct, data):

        # 이미지 연산 패킷일 경우 : ImagePacketMerger에 입력
        if (header.msgType == MsgType.REQUEST_NNCAL):
            (frameID, nnType, img) = imagePacketMerger.put_packet(struct, data)

            # 이미지 조립 끝나서 데이터 나온 경우
            if (frameID is not None):

                # Segmentation : YOLACT 요청
                if ((nnType & NNType.YOLACT) == NNType.YOLACT):
                    if not config.UseYolact:
                        quick_response_packet_byte = quick_create_packet(MsgType.ERROR, (ErrorType.UnOpen_NN))
                        sendall(client_socket, quick_response_packet_byte)
                    elif (socketQ.YolactInputQ.full()):
                        # print('one get, one put')
                        socketQ.YolactInputQ.get()
                        socketQ.YolactInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})
                        '''
                        quick_response_packet_byte = quick_create_packet(MsgType.RESPONSE_SEGMENTATION,
                                                                         (frameID, 0, 0, NNCalReulst.FAIL_SERVER_BUSY,
                                                                          NNType.YOLACT, 0, 0, 0, 0))
                        sendall(client_socket, quick_response_packet_byte)
                        '''
                    else:
                        socketQ.YolactInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})

                # Pose2D : FastPose 요청
                if ((nnType & NNType.FASTPOSE) == NNType.FASTPOSE):
                    if not config.UseFastPose:
                        quick_response_packet_byte = quick_create_packet(MsgType.ERROR, (ErrorType.UnOpen_NN))
                        sendall(client_socket, quick_response_packet_byte)
                    elif (socketQ.FastPoseInputQ.full()):
                        # print('one get, one put')
                        socketQ.FastPoseInputQ.get()
                        socketQ.FastPoseInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})
                        '''
                        quick_response_packet_byte = quick_create_packet(MsgType.RESPONSE_2DPOSE,
                                                                         (frameID, 0, 0, NNCalReulst.FAIL_SERVER_BUSY,
                                                                          NNType.FASTPOSE, 0, 0, 0))
                        sendall(client_socket, quick_response_packet_byte)
                        '''
                    else:
                        socketQ.FastPoseInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})

                # Pose2D : AlphaPose 요청
                if ((nnType & NNType.ALPHAPOSE) == NNType.ALPHAPOSE):
                    if not config.UseAlphaPose:
                        quick_response_packet_byte = quick_create_packet(MsgType.ERROR, (ErrorType.UnOpen_NN))
                        sendall(client_socket, quick_response_packet_byte)
                    elif (socketQ.AlphaPoseInputQ.full()):
                        # print('one get, one put')
                        socketQ.AlphaPoseInputQ.get()
                        socketQ.AlphaPoseInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})
                        '''
                        quick_response_packet_byte = quick_create_packet(MsgType.RESPONSE_2DPOSE,
                                                                         (frameID, 0, 0, NNCalReulst.FAIL_SERVER_BUSY,
                                                                          NNType.ALPHAPOSE, 0, 0, 0))
                        sendall(client_socket, quick_response_packet_byte)
                        '''
                    else:
                        socketQ.AlphaPoseInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})

                # Pose2D : AlphaPose 요청
                if ((nnType & NNType.BMC) == NNType.BMC):
                    if not config.UseBMC:
                        quick_response_packet_byte = quick_create_packet(MsgType.ERROR, (ErrorType.UnOpen_NN))
                        sendall(client_socket, quick_response_packet_byte)
                    elif (socketQ.BMCInputQ.full()):
                        # print('one get, one put')
                        socketQ.BMCInputQ.get()
                        socketQ.BMCInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})
                    else:
                        socketQ.BMCInputQ.put({
                            'client_socket': client_socket,
                            'frame_id': frameID,
                            'frame': img,
                            'option': nnType})

        # 이미지 연산 패킷이 아닐 경우 : 바로 대응함
        else:
            # 딥러닝 서비스 접속 요청 패킷 반응
            if (header.msgType == MsgType.REQUEST_ACCESS):
                result = access_check(config, struct.accessCode, client_manager.get_client_number())
                quick_response_packet_byte = quick_create_packet(MsgType.RESPONSE_ACCESS, (result))
                sendall(client_socket, quick_response_packet_byte)
                if (result != AccessResult.ACCEPT):
                    client_socket.close()
                    client_manager.remove_client(addr)
                    return False

            # 서버 상태 요청 패킷 반응
            elif (header.msgType == MsgType.REQUEST_SERVER_STATUS):
                quick_response_packet_byte = quick_create_packet(MsgType.RESPONSE_SERVER_STATUS,
                                                                 (client_manager.get_client_number(),
                                                                  client_manager.get_availability()))
                sendall(client_socket, quick_response_packet_byte)

            # 경고 패킷 반응
            elif (header.msgType == MsgType.WARNING):
                # 경고 메세지 대응
                return True

            # 경고 패킷 반응
            elif (header.msgType == MsgType.ERROR):
                # 에러 메세지 대응
                return True

            # Notify 패킷 반응
            elif (header.msgType == MsgType.NOTIFY):
                if (packetStruct.notifyType == NotifyType.CLIENT_CLOSE):
                    client_socket.shutdown(socket.SHUT_RDWR)
                    client_socket.close()
                    client_manager.remove_client(addr)
                    return False

            # 이상 패킷 : 에러, 정상적인 방법으로 올 리 없는 상황. 부정적인 접근으로 일단 판단하여 쓰레드 종료
            else:
                quick_response_packet_byte = quick_create_packet(MsgType.ERROR, (ErrorType.UNSUITABLE_PACKET_TYPE))
                sendall(client_socket, quick_response_packet_byte)
                client_socket.close()
                client_manager.remove_client(addr)
                print('Packet React Error')
                return False

        return True

    while (True):
        time.sleep(0.01)

        # 데이터 수신
        try:
            recv_buffer = client_socket.recv(65535)
        # 에러 발생 시 연결 종료로 간주, Notify Packet will come...? need Exception processing
        except (Exception, OSError) as e:
            # client_socket.shutdown(socket.SHUT_RDWR)
            # quick_response_packet_byte = quick_create_packet(MsgType.NOTIFY, (NotifyType.SERVER_CLOSE))
            # sendall(client_socket, quick_response_packet_byte)
            # client_socket.close()
            # client_manager.remove_client(addr)
            break

        # 이번에 받은 데이터 정보 기록
        recv_buffer_size = len(recv_buffer)
        recv_buffer_offset = 0
        packetData = bytearray()

        # 수신한 데이터 다 처리할 때 까지 반복
        while (recv_buffer_offset < recv_buffer_size):
            try:
                # packet 헤더 까기
                headerByte = recv_buffer[recv_buffer_offset: recv_buffer_offset + NetworkInfo.HEADER_SIZE]
                header = read_header(headerByte)
                recv_buffer_offset = recv_buffer_offset + NetworkInfo.HEADER_SIZE

                # packet struct 까기
                packetStruct = packetStructDict[header.msgType].from_bytes(
                    recv_buffer[recv_buffer_offset: recv_buffer_offset + header.packetStructSize])
                recv_buffer_offset = recv_buffer_offset + header.packetStructSize

                # packet data 까기
                if (header.packetDataSize > 0):
                    packetData = recv_buffer[recv_buffer_offset: recv_buffer_offset + header.packetDataSize]
                    recv_buffer_offset = recv_buffer_offset + header.packetDataSize

                react_normal = packet_react(header, packetStruct, packetData)

                # 수신한 패킷을 반응할 때 에러가 발생한 경우
                if not react_normal:
                    break

            except (Exception, OSError) as e:
                break


# 출력 큐 하나 잡아서 계속 송신하는 프로세스 : Alpha/Fast/Yolact 각각 하나씩 배당됨
def SendResultProcess(sendQ, nnType):
    # 결과 데이터 분리기 nnType에 맞게 할당
    if (nnType == NNType.YOLACT):
        dataSpliter = SegPacketSpliter(nnType)
    elif (nnType == NNType.FASTPOSE):
        dataSpliter = Pose2DPacketSpliter(nnType, JointNumber.FASTPOSE)
    elif (nnType == NNType.ALPHAPOSE):
        dataSpliter = Pose2DPacketSpliter(nnType, JointNumber.ALPHAPOSE)
    else:
        dataSpliter = None

    # sendQ에서 꺼내서 데이터 분리기에 넣고 다 보낼 때 까지가 한 사이클
    while (True):
        if not sendQ.empty():
            input = sendQ.get()
            dataSpliter.put_data(input['client_socket'], input['frame_id'], input['result_data'])

            # 결과 데이터 다 쪼개서 보낼 동안 반복함
            while (not dataSpliter.isSplitEnd):
                (client_socket, packetByte) = dataSpliter.get_packet_byte()
                try:
                    sendall(client_socket, packetByte)
                except (Exception, OSError) as e:
                    # print(e)
                    break  # 절대로 멈춰서는 안됨

        else:
            time.sleep(0.01)


# ===== 송수신 함수

# 클라이언트에서 온 데이터 수신하는 함수
def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)

    return buf


# 클라이언트에게 데이터 송신하는 함수
def sendall(sock, data):
    sock.send(data)
    '''
    sent_total = 0

    while sent_total < len(data):
        sent = sock.send(data[sent_total:])
        if sent == 0:
            raise RuntimeError('socket connection broken')
        sent_total = sent_total + sent
    '''


# ===== Lagacy, 이제 사용 안함

# 이미지 수신 함수
def recvImage(client_socket):
    emergencyResize = False

    # Header 수신
    frame_id_str = recvall(client_socket, NetworkInfo.HEADER_SIZE)
    frame_id = int(frame_id_str)
    option_str = recvall(client_socket, NetworkInfo.HEADER_SIZE)
    option = int(option_str)
    length = recvall(client_socket, NetworkInfo.HEADER_SIZE)

    # 이미지 수신
    stringData = recvall(client_socket, int(length))
    data = np.frombuffer(stringData, dtype='uint8')
    decimg = cv2.imdecode(data, 1)

    # 사이즈 조정 후 이미지 반환
    if (emergencyResize):
        result = cv2.resize(decimg, (640, 480), interpolation=cv2.INTER_AREA)
        # cv2.imshow('recved image', result)
        # cv2.waitKey(1)
        return (frame_id, option, result)

    # 사이즈 조정 후 이미지 반환
    elif ((option == 1 or option == 5) and decimg.shape[0] > 480):
        result = cv2.resize(decimg, (640, 480), interpolation=cv2.INTER_AREA)
        # cv2.imshow('recved image', result)
        # cv2.waitKey(1)
        return (frame_id, option, result)

    # 이미지 반환
    else:
        # cv2.imshow('recved image', decimg)
        # cv2.waitKey(1)
        return (frame_id, option, decimg)


# 리스트 송신 함수
def sendList(client_socket, option, frame_id, result_array):
    if (frame_id == 0):
        return

    result_byte = result_array.tostring()
    result_size = len(result_byte)
    end_message = 1

    sendall(client_socket, str(frame_id).ljust(NetworkInfo.HEADER_SIZE).encode() + str(option).ljust(
        NetworkInfo.HEADER_SIZE).encode() +
            str(result_size).ljust(NetworkInfo.HEADER_SIZE).encode() + result_byte + str(end_message).ljust(
        NetworkInfo.HEADER_SIZE).encode())

    # print('JointList Sended : ' + str(frame_id))


# 마스크 송신 함수
def sendMask_array(client_socket, option, frame_id, mask_array):
    if (frame_id == 0):
        return

    mask_byte = mask_array.tobytes('C')
    mask_size = len(mask_byte)
    end_message = 1

    sendall(client_socket, str(frame_id).ljust(NetworkInfo.HEADER_SIZE).encode() + str(option).ljust(
        NetworkInfo.HEADER_SIZE).encode() +
            str(mask_size).ljust(NetworkInfo.HEADER_SIZE).encode() + mask_byte + str(end_message).ljust(
        NetworkInfo.HEADER_SIZE).encode())

    # print('Sended mask')