FROM quay.io/oatakan/nvidia-cuda-tensorflow:latest

WORKDIR /usr/src/app

COPY requirements.txt risk-assessment.py pneumonia_model.h5 FreeMono.ttf ./

RUN pip install -r requirements.txt

CMD ["python", "-u", "risk-assessment.py"]
