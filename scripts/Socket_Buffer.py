from multiprocessing import Queue
import ServerConfig
import cv2

class buffer:
    def __init__(self, config):

        # 버퍼 프로세스 개수만큼 생성하는 내부 함수
        def create_buffers(proc_num, Q_MAX_SIZE):
            buffers = []
            
            for i in range(proc_num):
                buffer = Queue(maxsize=Q_MAX_SIZE)
                init_buffer(buffer)
                buffers.append(buffer)

            return buffers
        
        # 버퍼에 이미지 한 장 넣어놔서 Init하는 함수
        def init_buffer(buffer):
            init_img = cv2.imread('init.jpg')

            buffer.put({
                'client_socket': 0,
                'frame_id': 0,
                'frame': init_img,
                'option': 0})


        self.FastBuffers = create_buffers(config.FastPoseProcessNum, config.Q_MAX_SIZE)
        self.AlphaBuffers = create_buffers(config.AlphaPoseProcessNum, config.Q_MAX_SIZE)
        self.YOLACTBuffers = create_buffers(config.YOLACTProcessNum, config.Q_MAX_SIZE)

    # 버퍼 닫는 함수
    def close(self, config):

        def closeEachBuffers(buffers, proc_num, Q_MAX_SIZE):
            for i in range(proc_num):
                buffers[i].close()
                buffers[i].joint_thread()

        closeEachBuffers(self.FastBuffers, config.FastPoseProcessNum, config.Q_MAX_SIZE)
        closeEachBuffers(self.AlphaBuffers, config.FastPoseProcessNum, config.Q_MAX_SIZE)
        closeEachBuffers(self.YOLACTBuffers, config.FastPoseProcessNum, config.Q_MAX_SIZE)