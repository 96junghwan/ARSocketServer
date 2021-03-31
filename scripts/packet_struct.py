import socket
import numpy as np
import datetime
import struct
from typing import NamedTuple
from packet_constants import *



class PacketHeader(NamedTuple):
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


class WarningPacketStruct(NamedTuple):
    warningType: np.uint16

    # static variable
    form_str = '<H'

    def to_bytes(self):
        return struct.pack(self.form_str, self.warningType)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class ErrorPacketStruct(NamedTuple):
    errorType: np.uint16

    # static variable
    form_str = '<H'

    def to_bytes(self):
        return struct.pack(self.form_str, self.errorType)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class NotifyPacketStruct(NamedTuple):
    notifyType: np.uint16

    # static variable
    form_str = '<H'

    def to_bytes(self):
        return struct.pack(self.form_str, self.notifyType)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))


class RequestAccessPacketStruct(NamedTuple):
    accessCode: str

    # static variable
    form_str = '<11s'

    def to_bytes(self):
        return struct.pack(self.form_str, self.accessCode)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class RequestServerStatusPacketStruct(NamedTuple):
    temp: int

class RequestNNCalPacketStruct(NamedTuple):
    frameID: np.int32
    imageWholeSize: np.uint32
    dataSize: np.uint16
    offset: np.uint32
    order: np.int32
    nnType: np.int32

    # static variable
    form_str = '<iIHIii'

    def to_bytes(self):
        return struct.pack(self.form_str, self.frameID, self.imageWholeSize, self.dataSize, self.offset, self.order, self.nnType)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))


class ResponseAccessPacketStruct(NamedTuple):
    accessResult: np.uint16

    # static variable
    form_str = '<H'

    def to_bytes(self):
        return struct.pack(self.form_str, self.accessResult)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class ResponseServerStatusPacketStruct(NamedTuple):
    ccu: np.uint32
    serverBufferStatus: np.uint16

    # static variable
    form_str = '<IH'

    def to_bytes(self):
        return struct.pack(self.form_str, self.ccu, self.serverBufferStatus)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class ResponseSegmentationPacketStruct(NamedTuple):
    frameID: np.int32
    maskWholeSize: np.uint32
    dataSize: np.uint16
    result: np.uint16
    nnType: np.int32
    offset: np.uint32
    order: np.int32
    width: np.uint16
    height: np.uint16

    # static variable
    form_str = '<iIHHiIiHH'

    def to_bytes(self):
        return struct.pack(self.form_str, self.frameID, self.maskWholeSize, self.dataSize, self.result,
                           self.nnType, self.offset, self.order, self.width, self.height)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))

class Response2DPosePacketStruct(NamedTuple):
    frameID: np.int32
    jointWholeSize: np.uint32
    dataSize: np.uint16
    result: np.uint16
    nnType: np.int32
    offset: np.uint32
    order: np.int32
    jointNumbers: np.uint16

    # static variable
    form_str = '<iIHHiIiH'

    def to_bytes(self):
        return struct.pack(self.form_str, self.frameID, self.jointWholeSize, self.dataSize,
                           self.result, self.nnType, self.offset, self.order, self.jointNumbers)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))


# 추가 필요 : C# 측과 협의
class Response3DPosePacketStruct(NamedTuple):
    frameID: np.int32
    jointWholeSize: np.uint32
    dataSize: np.uint16
    result: np.uint16
    nnType: np.int32
    offset: np.uint32
    order: np.int32
    people: np.uint16

    # static variable
    form_str = '<iIHHiIiH'

    def to_bytes(self):
        return struct.pack(self.form_str, self.frameID, self.jointWholeSize, self.dataSize,
                           self.result, self.nnType, self.offset, self.order, self.people)

    @classmethod
    def from_bytes(cls, bytes):
        return cls._make(struct.unpack(cls.form_str, bytes))


packetStructDict = {
        MsgType.WARNING: WarningPacketStruct,
        MsgType.ERROR: ErrorPacketStruct,
        MsgType.NOTIFY: NotifyPacketStruct,

        MsgType.REQUEST_ACCESS: RequestAccessPacketStruct,
        MsgType.REQUEST_SERVER_STATUS: RequestServerStatusPacketStruct,
        MsgType.REQUEST_NNCAL: RequestNNCalPacketStruct,

        MsgType.RESPONSE_ACCESS: ResponseAccessPacketStruct,
        MsgType.RESPONSE_SERVER_STATUS: ResponseServerStatusPacketStruct,
        MsgType.RESPONSE_SEGMENTATION: ResponseSegmentationPacketStruct,
        MsgType.RESPONSE_2DPOSE: Response2DPosePacketStruct,
        MsgType.RESPONSE_3DPOSE: Response3DPosePacketStruct
}
