
import ServerConfig
import SocketQ
import AR_Socket
from multiprocessing import Process
from packet_constants import *
import numpy as np


# 신경망 로드 함수
def init_NNs(socketQ, config):

    procs = []

    # FastPose 신경망 시작
    if config.UseFastPose:
        # 데이터 소켓 전송 프로세스 생성 및 시작
        import FastPose.Server_FastPose
        proc = Process(target=AR_Socket.SendResultProcess, args=(socketQ.FastPoseOutputQ, NNType.FASTPOSE,))
        proc.daemon = False
        procs.append(proc)
        proc.start()
        
        for i in range(config.FastPoseProcessNum):
            proc = Process(target=FastPose.Server_FastPose.run_server, args=(socketQ.FastPoseInputQ, socketQ.FastPoseOutputQ,))
            proc.daemon = False
            procs.append(proc)
            proc.start()

    # AlphaPose 신경망 시작
    if config.UseAlphaPose:
        import AlphaPose.Server_AlphaPose
        # 데이터 소켓 전송 프로세스 생성 및 시작
        proc = Process(target=AR_Socket.SendResultProcess, args=(socketQ.AlphaPoseOutputQ, NNType.ALPHAPOSE,))
        proc.daemon = False
        procs.append(proc)
        proc.start()

        for i in range(config.AlphaPoseProcessNum):
            proc = Process(target=AlphaPose.Server_AlphaPose.run_server, args=(socketQ.AlphaPoseInputQ, socketQ.AlphaPoseOutputQ,))
            proc.daemon = False
            procs.append(proc)
            proc.start()

    # Yolact 신경망 시작
    if config.UseYolact:
        # 데이터 소켓 전송 프로세스 생성 및 시작
        import YOLACT.Server_YOLACT
        proc = Process(target=AR_Socket.SendResultProcess, args=(socketQ.YolactOutputQ, NNType.YOLACT,))
        proc.daemon = False
        procs.append(proc)
        proc.start()

        for i in range(config.YolactProcessNum):
            proc = Process(target=YOLACT.Server_YOLACT.run_server, args=(socketQ.YolactInputQ, socketQ.YolactOutputQ,))
            proc.daemon = False
            procs.append(proc)
            proc.start()

    # Yolact 신경망 시작
    if config.UseBMC:
        # 데이터 소켓 전송 프로세스 생성 및 시작
        import BMC.Server_BMC
        proc = Process(target=AR_Socket.SendResultProcess, args=(socketQ.BMCOutputQ, NNType.YOLACT,))
        proc.daemon = False
        procs.append(proc)
        proc.start()

        for i in range(config.YolactProcessNum):
            proc = Process(target=YOLACT.Server_YOLACT.run_server,
                            args=(socketQ.YolactInputQ, socketQ.YolactOutputQ,))
            proc.daemon = False
            procs.append(proc)
            proc.start()

    return procs

def run_server(config):
    socketQ = SocketQ.SocketQ(config)
    server_socket = AR_Socket.init_server(config)
    procs = init_NNs(socketQ, config)
    AR_Socket.accept_client(server_socket, socketQ, config)

if __name__ == "__main__":
    config = ServerConfig.ServerCfg()
    run_server(config)
