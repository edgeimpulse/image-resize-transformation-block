
FROM ubuntu:20.04

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y python3 python3-distutils wget
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.8 get-pip.py "pip==21.3.1" && \
    rm get-pip.py
RUN apt-get install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y
RUN apt-get install gcc -y
RUN apt-get install python3-pyaudio -y
# Python dependencies
COPY requirements.txt ./
RUN pip3 --no-cache-dir install -r requirements.txt

COPY . ./

ENTRYPOINT [ "python3",  "transform.py" ]