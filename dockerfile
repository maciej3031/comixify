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
COPY ./Makefile.config /comixify/Makefile.config

ENV CAFFE_ROOT=/opt/caffe
WORKDIR $CAFFE_ROOT

ENV CLONE_TAG=1.0

RUN git clone -b ${CLONE_TAG} --depth 1 https://github.com/BVLC/caffe.git . && \
    cp /comixify/Makefile.config ./Makefile.config && \
    cd python && for req in $(cat requirements.txt) pydot; do python3.6 -m pip install $req; done && cd .. && \
    sed -i '415s/.*/NVCCFLAGS += -D_FORCE_INLINES -ccbin=$(CXX) -Xcompiler -fPIC $(COMMON_FLAGS)/' Makefile && \
    echo "# ---[ Includes" >> CMakeLists.txt && \
    echo "set(${CMAKE_CXX_FLAGS} "-D_FORCE_INLINES ${CMAKE_CXX_FLAGS}")" >> CMakeLists.txt && \
    ls -la /usr/lib/x86_64-linux-gnu && \
    ln -s /usr/lib/x86_64-linux-gnu/libboost_python-py35.so /usr/lib/x86_64-linux-gnu/libboost_python3.so && \
    make all -j"$(nproc)" && \
    make distribute

ENV PYCAFFE_ROOT $CAFFE_ROOT/python
ENV PYTHONPATH $PYCAFFE_ROOT:$PYTHONPATH
ENV PATH $CAFFE_ROOT/build/tools:$PYCAFFE_ROOT:$PATH
RUN echo "$CAFFE_ROOT/build/lib" >> /etc/ld.so.conf.d/caffe.conf && ldconfig && \
    python3.6 $CAFFE_ROOT/scripts/download_model_binary.py $CAFFE_ROOT/models/bvlc_googlenet && \
    python3.6 -m pip install markdown=="2.6.11" && \
    python3.6 -m pip install python-dateutil --upgrade

WORKDIR /comixify
COPY . /comixify
RUN mkdir /comixify/popularity/pretrained_model && \
    wget -P /comixify/popularity/pretrained_model/ https://uc09e02e502c75a0f94502700ba8.dl.dropboxusercontent.com/cd/0/get/AS3P2Mj6bhm8o7W0VT0CRlqFCTN_WdIGCvjGNkYUA-YxsPajn3VDJiGA6tSCTRgUpgnvgktHRId0c2pCHQO5lDSxHtkpU1trsLOKa0acPxiXH95p3y6YpYnScc0b4wUarpGolZFeslLA0lSUodiqZkUpucaDJQOAaizSFNsPcbN-t_3c7RZf8qqoU3ResnhK6-M/file?_download_id=64139804958585964230187748620814832316528266695408017035927113036&_notify_domain=www.dropbox.com&dl=1 && \
    python3.6 -m pip install -r requirements.txt

# Port to expose
EXPOSE 8008

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ['start']
