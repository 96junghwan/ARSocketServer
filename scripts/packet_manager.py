import socket
import numpy as np
import datetime
import struct
import socket
import cv2
from typing import NamedTuple
from packet_struct import *
from packet_constants import *


# 클라 담당 Thread가 다 하나씩 갖고 있음
# 클라에서 보낸 쪼개진 이미지 패킷들 조립해서 각각의 InputQ에 집어넣는 클래스
class ImagePacketMerger:
    # 내부 패킷 클래스
    class MergedPacket:
        def __init__(self):
            self.frameID = 0
            self.nnType = 0
            self.imageWholeSize = 0
            self.imageByte = bytearray()
            self.isProcessing = False

    def __init__(self):
        self.mergedPacketList = []
        for i in range(5):
            mergedPacket = self.MergedPacket()
            self.mergedPacketList.append(mergedPacket)

    # 패킷 리스트에서 알맞은 인덱스 찾아주는 함수
    def find_index(self, order, frameID):
        index = -1

        # 첫 패킷인 경우 : 리스트의 빈 인덱스 찾아서 반환함
        if ((order & Order.First) == Order.First):
            for i in range(5):
                if not self.mergedPacketList[i].isProcessing:
                    index = i
                    break

        # 중간/끝 패킷인 경우 : 입력된 frameID 기반으로 검색해서 인덱스 반환
        else:
            for i in range(5):
                if (self.mergedPacketList[i].frameID == frameID):
                    index = i
                    break

        return index

    # 분리된 패킷 입력하는 함수
    def put_packet(self, packetStruct, imageByte):
        index = self.find_index(packetStruct.order, packetStruct.frameID)

        # 인덱스 못찾았을 경우
        if (index == -1):
            # print('Cannot find index')
            return (None, None, None)

        # 리스트에 패킷 첫 데이터 입력
        if ((packetStruct.order & Order.First) == Order.First):
            self.mergedPacketList[index].frameID = packetStruct.frameID
            self.mergedPacketList[index].nnType = packetStruct.nnType
            self.mergedPacketList[index].imageWholeSize = packetStruct.imageWholeSize
            self.mergedPacketList[index].imageByte = bytearray(packetStruct.imageWholeSize)
            self.mergedPacketList[index].isProcessing = True
            # print('Image Byte Size : ' + str(self.mergedPacketList[index].imageWholeSize))

        # 이미지 데이터 입력
        self.mergedPacketList[index].imageByte[
        packetStruct.offset:packetStruct.offset + packetStruct.dataSize] = imageByte

        # 마지막 이미지 패킷이었을 경우 : 이미지 빼서 처리 큐에 넣자~
        if ((packetStruct.order & Order.End) == Order.End):
            data = np.frombuffer(self.mergedPacketList[index].imageByte, dtype='uint8')
            img = cv2.imdecode(data, 1)

            # cv2.imshow('dsf', img)
            # cv2.waitKey(1)

            self.mergedPacketList[index].isProcessing = False

            # 인덱스는 무조건 0에서 놀아야 하는게 맞기 때문에, 만약 0이 아니라면 비워주기(끊긴 경우일 듯)
            if (index > 0):
                self.mergedPacketList[index - 1].isProcessing = False

            # 이미지가 세로로 더 길고, 이미지 해상도가 480P 이상인 경우 전처리
            if (img.shape[0] > img.shape[1]):
                if (img.shape[1] > 480):
                    result = cv2.resize(img, (480, 640), interpolation=cv2.INTER_AREA)
                    return (self.mergedPacketList[index].frameID, self.mergedPacketList[index].nnType, result)

                else:
                    return (self.mergedPacketList[index].frameID, self.mergedPacketList[index].nnType, img)

            # 이미지가 가로가 더 길고, 이미지 해상도가 480P 이상인 경우 전처리
            elif (img.shape[0] > 480):
                result = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)
                return (self.mergedPacketList[index].frameID, self.mergedPacketList[index].nnType, result)

            # 아무것도 포함되지 않는 경우 : 전처리 수행 안함
            else:
                return (self.mergedPacketList[index].frameID, self.mergedPacketList[index].nnType, img)

        # 이미지 마무리가 안된 경우 : 나머지 올 때 까지 기다리셈
        else:
            return (None, None, None)


# Pose SendThread가 얘 들고 있어서 RequestQ에서 하나씩 뽑아서 나눠서 바로바로 보내는 방식
# 2D Pose 결과 관절 받아서 분할하여 해당하는 SendQ에 하나씩 집어넣는 클래스
class Pose2DPacketSpliter:
    # 내부 패킷 클래스
    class MergedPacket:
        def __init__(self):
            self.client_socket = socket
            self.frameID = 0
            self.jointWholeSize = 0
            self.result = 0
            self.jointNumbers = 0
            self.jointBytes = bytearray()
            self.nextOffset = 0

    def __init__(self, nnType, jointNumbers):
        self.nnType = nnType
        self.jointNumbers = jointNumbers
        self.isSplitEnd = True
        self.mergedPacket = self.MergedPacket()

    # 데이터 입력 받는 함수
    def put_data(self, client_socket, frameID, joints):
        # 0번은 초기화 용
        if (frameID == 0):
            return

        self.mergedPacket.client_socket = client_socket
        self.mergedPacket.frameID = frameID
        self.mergedPacket.nextOffset = 0
        self.mergedPacket.result = 0
        self.mergedPacket.jointNumbers = self.jointNumbers
        self.isSplitEnd = False
        self.mergedPacket.jointBytes = joints.tostring()
        self.mergedPacket.jointWholeSize = len(self.mergedPacket.jointBytes)

    # 현존하는 멤버를 가지고 패킷 쪼개서 bytes로 넘겨주는 함수
    def get_packet_byte(self):
        # 이번 분리 패킷의 data Size 결정
        dataSize = self.mergedPacket.jointWholeSize - self.mergedPacket.nextOffset
        if (dataSize > NetworkInfo.PACKET_DATA_SIZE_LIMIT):
            dataSize = NetworkInfo.PACKET_DATA_SIZE_LIMIT

        # 이번 분리 패킷의 order 결정
        order = 0
        if (self.mergedPacket.nextOffset == 0):
            order = order + Order.First
        if ((self.mergedPacket.nextOffset + dataSize) >= self.mergedPacket.jointWholeSize):
            order = order + Order.End

        # packet {header, struct, data} 생성 : 역순으로 생성
        packetData = self.mergedPacket.jointBytes[
                     self.mergedPacket.nextOffset: (self.mergedPacket.nextOffset + dataSize)]
        packetStructByte = Response2DPosePacketStruct(self.mergedPacket.frameID, self.mergedPacket.jointWholeSize,
                                                      dataSize, self.mergedPacket.result, self.nnType,
                                                      self.mergedPacket.nextOffset, order, self.jointNumbers).to_bytes()

        header = PacketHeader(MsgType.RESPONSE_2DPOSE, len(packetStructByte), len(packetData))
        headerBytes = header.to_bytes()

        # 결과 패킷 바이트 제작
        packetByte = bytearray(NetworkInfo.HEADER_SIZE + header.packetStructSize + header.packetDataSize)
        packetByte[0:] = headerBytes
        packetByte[NetworkInfo.HEADER_SIZE:] = packetStructByte
        packetByte[NetworkInfo.HEADER_SIZE + header.packetStructSize:] = packetData

        # 다음 패킷 분리 사이클을 위한 후처리
        self.mergedPacket.nextOffset = self.mergedPacket.nextOffset + dataSize
        if ((order & Order.End) == Order.End):
            self.isSplitEnd = True

        return (self.mergedPacket.client_socket, packetByte)


# Seg SendThread가 하나 갖고 있음
# 세그멘테이션 결과 마스크 받아서 분할하여 해당하는 SendQ에 하나씩 집어넣는 클래스
class SegPacketSpliter:
    # 내부 패킷 클래스
    class MergedPacket:
        def __init__(self):
            self.client_socket = socket
            self.frameID = 0
            self.maskWholeSize = 0
            self.result = 0
            self.width = 0
            self.height = 0
            self.maskBytes = bytearray()
            self.nextOffset = 0

    def __init__(self, nnType):
        self.nnType = nnType
        self.mergedPacket = self.MergedPacket()
        self.isSplitEnd = True

    # 데이터 입력 받는 함수
    def put_data(self, client_socket, frameID, mask_array):
        # 0번은 초기화 용
        if (frameID == 0):
            return

        self.mergedPacket.client_socket = client_socket
        self.mergedPacket.frameID = frameID
        # self.mergedPacket.maskBytes = mask_array.tobytes('C')
        # encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
        encode_result, mask_jpg = cv2.imencode('.jpg', mask_array, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        self.mergedPacket.maskBytes = mask_jpg.tostring()
        self.mergedPacket.maskWholeSize = len(self.mergedPacket.maskBytes)
        # print(str(self.mergedPacket.maskWholeSize))
        self.mergedPacket.nextOffset = 0
        self.mergedPacket.result = 0
        self.mergedPacket.width = mask_array.shape[1]
        self.mergedPacket.height = mask_array.shape[0]
        self.isSplitEnd = False

    # 현존하는 멤버를 가지고 패킷 쪼개서 bytes로 넘겨주는 함수
    def get_packet_byte(self):
        # 이번 분리 패킷의 data Size 결정
        dataSize = self.mergedPacket.maskWholeSize - self.mergedPacket.nextOffset
        if (dataSize > NetworkInfo.PACKET_DATA_SIZE_LIMIT):
            dataSize = NetworkInfo.PACKET_DATA_SIZE_LIMIT

        # 이번 분리 패킷의 order 결정
        order = 0
        if (self.mergedPacket.nextOffset == 0):
            order = order + Order.First
        if ((self.mergedPacket.nextOffset + dataSize) >= self.mergedPacket.maskWholeSize):
            order = order + Order.End

        # packet {header, struct, data} 생성 : 역순으로 생성
        packetData = self.mergedPacket.maskBytes[
                     self.mergedPacket.nextOffset: (self.mergedPacket.nextOffset + dataSize)]
        packetStructByte = ResponseSegmentationPacketStruct(self.mergedPacket.frameID, self.mergedPacket.maskWholeSize,
                                                            dataSize, self.mergedPacket.result, self.nnType,
                                                            self.mergedPacket.nextOffset, order,
                                                            self.mergedPacket.width,
                                                            self.mergedPacket.height).to_bytes()

        header = PacketHeader(MsgType.RESPONSE_SEGMENTATION, len(packetStructByte), len(packetData))
        headerBytes = header.to_bytes()

        # 결과 패킷 바이트 제작
        packetByte = bytearray(NetworkInfo.HEADER_SIZE + header.packetStructSize + header.packetDataSize)
        packetByte[0:] = headerBytes
        packetByte[NetworkInfo.HEADER_SIZE:] = packetStructByte
        packetByte[NetworkInfo.HEADER_SIZE + header.packetStructSize:] = packetData

        # 다음 패킷 분리 사이클을 위한 후처리
        self.mergedPacket.nextOffset = self.mergedPacket.nextOffset + dataSize
        if ((order & Order.End) == Order.End):
            self.isSplitEnd = True

        return (self.mergedPacket.client_socket, packetByte)


# bytes에서 헤더로 변환해서 넘겨주는 함수
def read_header(bytes):
    header = PacketHeader.from_bytes(bytes)
    return header


# packetData 필요 없는 packet 빠르게 만들어서 헤더까지 붙이고 bytes로 넘겨주는 함수
def quick_create_packet(msgType, input_tuple):
    packetStructByte = packetStructDict[msgType](input_tuple).to_bytes()
    # print(str(msgType) +', ' + str(len(packetStructByte))+', ' + str(0))
    packetHeaderByte = PacketHeader(msgType, len(packetStructByte), 0).to_bytes()
    return packetHeaderByte + packetStructByte
