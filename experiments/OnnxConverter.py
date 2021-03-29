import torch
import tensorflow as tf
import AlphaPose.Server_AlphaPose
import YOLACT.Server_YOLACT

def convert_pth_2_onnx():
    ONNX_FILE_PATH = '1.onnx'
    torch.onnx.export()

if __name__ == "__main__":
    convert_pth_2_onnx()