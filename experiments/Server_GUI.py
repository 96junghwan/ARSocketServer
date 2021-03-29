from PyQt5.QtWidgets import *
import sys
import psutil
import os

# pip install pyqt5
# pip install psutil
# pid = proc.pid
# py = psutil.Process(pid)
# memoryUse = py.memory_info()[0]/2.**30    # memory use in GB... maybe
# print(memoryUse)

# 프로세스의 CPU 사용량 및 Memory 사용량 출력
#pid = os.getpid()
#py = psutil.Process(pid)
#cpu_usage = os.popen("ps aux | grep " + str(pid) + " | grep -v grep | awk '{print $3}'").read()
#cpu_usage = cpu_usage.replace("\n", "")
#memory_usage = round(py.memory_info()[0] / 2. ** 30, 2)
#print("cpu usage\t\t:", cpu_usage, "%")
#print("memory usage\t\t:", memory_usage, "%")

# GPU 사용량 체크 코드
# https://github.com/alwynmathew/nvidia-smi-python/blob/master/gpu_stat.py

# 사용자 정의 폰트 설정 코드
# https://www.programcreek.com/python/example/81324/PyQt5.QtGui.QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("HumanAR Server")
        self.setGeometry(500, 300, 500, 300)

        btn = QPushButton("Click me", self)
        btn.move(20, 20)
        btn.clicked.connect(self.btn_clicked)

        self.label = QLabel()
        self.label.setGeometry(120, 220, 71, 31)
        self.label.setObjectName("label1")
        self.label.setText("Text of label1")
        self.label.setFont(QWidget.QtGu)

    def btn_clicked(self):
        QMessageBox.about(self, "Message~", "clicked")

def clicked_slot_1():
    print("Clicked")

def run_server_GUI():
    app = QApplication(sys.argv)    # QApplication 객체 app 생성
    main_window = MainWindow()      # 해당 객체 생성
    main_window.show()              # 호출 시 해당 객체 보이게 함
    app.exec_()                     # 호출 시 이벤트 루프 생성함

if __name__ == "__main__":
    run_server_GUI()