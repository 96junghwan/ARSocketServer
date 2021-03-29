import torch

def notepad():
    torch.cuda.is_available()       # True
    torch.cuda.current_device()     # 0 : 현재 선택된 장치의 번호를 리턴
    torch.cuda.device_count()       # 1 : 현재 가능한 GPU의 수를 리턴
    torch.cuda.get_device_name(0)   # 'GeForce GTX 1060' : 해당 번호의 장치 이름을 리턴
    torch.cuda.device(0)            # 입력된 번호의 장치를 사용하도록 설정

    cuda = torch.device('cuda')                     # Default CUDA device
    a = torch.tensor([1., 2.], device=cuda)         # allocates a tensor on default GPU
    b = torch.tensor([1., 2.]).cuda()               # transfer a tensor from 'C'PU to 'G'PU
    b2 = torch.tensor([1., 2.]).to(device=cuda)     # Same with .cuda()

    #model = Model()                                # Loading model
    #model = model.cuda()                           # Loading parameters of model to GPU

    # GPU에 load한 tensor는 동일하게 GPU에 load된 tensor끼리만 연산이 가능하다.
    # model 또한 parameter를 cuda로 설정한 뒤 CPU에 loading된 tensor를 넣으면 error가 발생한다.
    # 사용하지 않는 tensor를 GPU에서 release하고 싶다면 torch.cuda.empty_cache()
    # .cuda()는 optimizer를 설정하기 전에 실행되어야 함. 잊어버리지 않으려면 모델을 생성하자마자 쓰는 것이 좋다.
    # GPU를 쓰기 위해 .cuda()를 call할 때 : 모든 input batch 또는 tensor, 그리고 모델

    # torch.no_grad()는 해당 범위 안에서 gradient 계산을 중지시킴. 학습을 제외하고는 이 방식으로 수행한다.