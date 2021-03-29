from multiprocessing import Queue
import cv2

class SocketQ:
    def __init__(self, config):
        self.QList = []

        # 큐에 이미지 미리 넣어놓는 함수
        def InitQ(Q, count):
            init_img = cv2.imread('init.jpg')
            
            # 프로세스 개수만큼 초기화용 이미 넣어둠. 정확하지는 않음
            for i in range(count):
                Q.put({
                    'client_socket': 0,
                    'frame_id': 0,
                    'frame': init_img,
                    'option': 0})
        
        # 소켓 I/O 큐 생성
        self.FastPoseInputQ = Queue(maxsize=config.Q_MAX_SIZE)
        self.FastPoseOutputQ = Queue(maxsize=config.Q_MAX_SIZE)
        self.AlphaPoseInputQ = Queue(maxsize=config.Q_MAX_SIZE)
        self.AlphaPoseOutputQ = Queue(maxsize=config.Q_MAX_SIZE)
        self.YolactInputQ = Queue(maxsize=config.Q_MAX_SIZE)
        self.YolactOutputQ = Queue(maxsize=config.Q_MAX_SIZE)
    
        # 각 프로세스 개수만큼 초기화 이미지 입력
        InitQ(self.FastPoseInputQ, config.FastPoseProcessNum)
        InitQ(self.AlphaPoseInputQ, config.AlphaPoseProcessNum)
        InitQ(self.YolactInputQ, config.YolactProcessNum)

        # 임시 관리를 위해 리스트에 큐 전체 추가
        self.QList.append(self.FastPoseInputQ)
        self.QList.append(self.FastPoseOutputQ)
        self.QList.append(self.AlphaPoseInputQ)
        self.QList.append(self.AlphaPoseOutputQ)
        self.QList.append(self.YolactInputQ)
        self.QList.append(self.YolactOutputQ)

    # 소켓 큐 전체 닫는 함수
    def close(self, config):
        # 전체 큐 리스트 해제
        for i in range(len(self.QList)):
            self.QList[i].close()
            self.QList[i].join_thread()