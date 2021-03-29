
class ServerCfg:

    def __init__(self):
        # 서버 신경망 사용 여부 세팅
        self.UseFastPose = False
        self.UseAlphaPose = True
        self.UseYolact = False

        # 각 신경망 별 프로세스 할당 개수 세팅
        self.FastPoseProcessNum = 1
        self.AlphaPoseProcessNum = 1
        self.YolactProcessNum = 1

        # 큐 사이즈 세팅
        self.Q_MAX_SIZE = 10
        self.FPS = 10       # 추후에는 직접 계산해서 사용

        # 서버 IP, Port 주소 세팅 : 포트포워딩 시 내부 IP 및 포워딩한 포트로 설정
        self.Server_IP = '127.0.0.1'
        self.Server_Port = 9999

        # 서버 최대 접속 인원
        self.CLIENT_MAX = 100

        # 서버 접속 코드
        self.developer_code = "99.99.99"
        self.standard_code = "01.04.01"
