FROM nvidia/cuda:9.0-cudnn7-runtime

RUN apt-get update && apt-get install -y apt-utils software-properties-common && \
    add-apt-repository ppa:jonathonf/python-3.6 && \
    apt-get update && apt-get -y install python3 python3-pip python3.6 python3.6-dev python3-pip python3.6-venv vim ffmpeg \
    build-essential cmake git libgtk2.0-dev pkg-config libavcodec-dev \
    libavformat-dev libswscale-dev && \
    python3.6 -m pip install --upgrade pip && \
    python3.6 -m pip install jupyter ipywidgets jupyterlab && \
    python3.6 -m pip install tensorflow-gpu h5py keras && \
    python3.6 -m pip install scikit-image opencv-contrib-python

RUN mkdir /comixify
WORKDIR /comixify
COPY . /comixify
RUN python3.6 -m pip install -r requirements.txt

# Port to expose
EXPOSE 8080

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ['start']
