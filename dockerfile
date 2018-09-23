FROM nvidia/cuda:9.0-cudnn7-devel

RUN apt-get update && apt-get install -y apt-utils software-properties-common && \
    add-apt-repository ppa:jonathonf/python-3.6 && \
    apt-get update && apt-get -y install python3 python3-pip python3.6 python3.6-dev python3.6-venv vim ffmpeg \
    build-essential cmake git libgtk2.0-dev pkg-config libavcodec-dev \
    wget libatlas-base-dev libboost-all-dev libgflags-dev \
    libgoogle-glog-dev libhdf5-serial-dev libleveldb-dev \
    liblmdb-dev libopencv-dev libprotobuf-dev \
    libsnappy-dev protobuf-compiler \
    python-numpy python-setuptools python-scipy \
    libavformat-dev libswscale-dev && \
    python3.6 -m pip install --upgrade pip && \
    python3.6 -m pip install jupyter ipywidgets jupyterlab && \
    python3.6 -m pip install tensorflow-gpu h5py keras && \
    python3.6 -m pip install scikit-image opencv-contrib-python pyyaml

RUN mkdir /comixify
WORKDIR /comixify
COPY . /comixify
RUN python3.6 -m pip install -r requirements.txt

ENV CAFFE_ROOT=/opt/caffe
WORKDIR $CAFFE_ROOT

ENV CLONE_TAG=1.0

RUN git clone -b ${CLONE_TAG} --depth 1 https://github.com/BVLC/caffe.git . && \
    cd python && for req in $(cat requirements.txt) pydot; do python3.6 -m pip install $req; done && cd .. && \
    git clone https://github.com/NVIDIA/nccl.git && cd nccl && make -j install && cd .. && rm -rf nccl && \
    cp /comixify/Cuda.cmake ./cmake/Cuda.cmake && \
    mkdir build && cd build && \
    cmake -DUSE_CUDNN=1 -DUSE_NCCL=1 .. && \
    make -j"$(nproc)"

ENV PYCAFFE_ROOT $CAFFE_ROOT/python
ENV PYTHONPATH $PYCAFFE_ROOT:$PYTHONPATH
ENV PATH $CAFFE_ROOT/build/tools:$PYCAFFE_ROOT:$PATH
RUN echo "$CAFFE_ROOT/build/lib" >> /etc/ld.so.conf.d/caffe.conf && ldconfig
RUN python3.6 $CAFFE_ROOT/scripts/download_model_binary.py $CAFFE_ROOT/models/bvlc_googlenet

RUN python3.6 pip install markdown=="2.6.11"

# Port to expose
EXPOSE 8008

WORKDIR /comixify
ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ['start']
