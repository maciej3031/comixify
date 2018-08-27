#!/bin/bash

# BASIC STUFF
sudo apt-get update
sudo apt-get -y dist-upgrade
sudo apt-get -y install apt-utils software-properties-common
sudo add-apt-repository -y ppa:jonathonf/python-3.6
sudo apt-get update
sudo apt-get -y install python3 python3-dev python3-pip libcupti-dev python3.6 python3.6-dev python3.6-venv vim ffmpeg build-essential cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev httpie


# CUDA
echo "Checking for CUDA and installing."
# Check for CUDA and try to install.
if ! dpkg-query -W cuda-9-0; then
  # The 16.04 installer works with 16.10.
  curl -O http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
  sudo dpkg -i ./cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
  sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
  sudo apt-get update
  sudo apt-get install cuda-9-0 -y
fi
# Enable persistence mode
sudo nvidia-smi -pm 1


# DOCKER
sudo apt-get -y remove docker docker-engine docker.io
sudo apt-get update
sudo apt-get -y install apt-transport-https ca-certificates curl
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get -y install docker-ce


# NVIDIA-DOCKER
# Add the package repositories
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update

# Install nvidia-docker2 and reload the Docker daemon configuration
sudo apt-get install -y nvidia-docker2
sudo pkill -SIGHUP dockerd

# Test nvidia-smi with the latest official CUDA image
sudo docker run --runtime=nvidia --rm nvidia/cuda nvidia-smi


# DOCKER-COMPOSE
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose


# CUDNN
wget https://developer.download.nvidia.com/compute/machine-learning/cudnn/secure/v7.2.1/prod/9.0_20180806/Ubuntu16_04-x64/libcudnn7_7.2.1.38-1%2Bcuda9.0_amd64.deb
wget https://developer.download.nvidia.com/compute/machine-learning/cudnn/secure/v7.2.1/prod/9.0_20180806/Ubuntu16_04-x64/libcudnn7-dev_7.2.1.38-1%2Bcuda9.0_amd64.deb
wget https://developer.download.nvidia.com/compute/machine-learning/cudnn/secure/v7.2.1/prod/9.0_20180806/Ubuntu16_04-x64/libcudnn7-doc_7.2.1.38-1%2Bcuda9.0_amd64.deb

sudo dpkg -i libcudnn7_7.2.1.38-1+cuda9.0_amd64.deb
sudo dpkg -i libcudnn7-dev_7.2.1.38-1+cuda9.0_amd64.deb
sudo dpkg -i libcudnn7-doc_7.2.1.38-1+cuda9.0_amd64.deb

echo 'export CUDA_HOME=/usr/local/cuda' >> ~/.bashrc
echo 'export PATH=$PATH:$CUDA_HOME/bin' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc

source ~/.bashrc


# INSTALL PACKAGES
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
sudo python3.6 -m pip install --upgrade pip
sudo python3.6 -m pip install tensorflow-gpu h5py keras torch torchvision
sudo python3.6 -m pip install scikit-image opencv-contrib-python


# REMOVE UNNECESSARY FILES
sudo rm libcudnn7*.deb
sudo rm cuda-repo-ubuntu1604*.deb


# CLONE REPO
git clone https://github.com/maciej3031/comixify.git


# BUILD AND RUN CONTAINERS
cd comixify/
sudo docker-compose build
sudo docker-compose up -d

# ASSURE THAT PORT 80 is open
sudo iptables -w -A INPUT -p tcp --dport 80 -j ACCEPT
