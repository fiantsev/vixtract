#!/usr/bin/env bash

source .env

if [ "$EUID" -ne 0 ]
  then echo "Please run with sudo"
  exit
fi

apt update && apt install -y wget curl software-properties-common python3.6 python3-pip bzip2 ca-certificates git libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6

### Conda
wget -nc https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh -O ~/anaconda.sh
bash ~/anaconda.sh -b -p ${CONDA_DIR}
ln -s ${CONDA_DIR}/etc/profile.d/conda.sh /etc/profile.d/conda.sh
/opt/conda/bin/conda init bash
source ~/.bashrc
source /etc/profile.d/conda.sh

### Groups && Dirs
groupadd -f etl
mkdir /var/etl
mkdir /media/etl
chgrp -R etl /var/etl
chgrp -R etl /media/etl

### NodeJS
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
apt update && apt install -y nodejs

### JupyterHub && JupyterLab
/opt/conda/bin/conda create -y --prefix=/opt/jupyterhub/ wheel jupyterhub jupyterlab ipywidgets sqlalchemy psycopg2
mkdir -p /opt/jupyterhub/etc/jupyterhub/
cp jupyterhub/jupyterhub_config.py /opt/jupyterhub/etc/jupyterhub/
cp systemd/jupyterhub.service /etc/systemd/system/jupyterhub.service
systemctl daemon-reload
systemctl enable jupyterhub.service
systemctl start jupyterhub.service

### Papermill
pip3 install papermill

### Conda ENV Dev
/opt/conda/bin/conda create -y --prefix=/opt/conda/envs/dev python=3.6 petl ipykernel wheel requests pandas sqlalchemy psycopg2 openpyxl
${CONDA_DIR}/envs/dev/bin/python -m ipykernel install --prefix=/usr/local --name 'dev' --display-name "Python (Dev Env)"

### Conda ENV Prod
/opt/conda/bin/conda create -y --prefix=/opt/conda/envs/prod python=3.6 petl ipykernel wheel requests pandas sqlalchemy psycopg2 openpyxl
${CONDA_DIR}/envs/prod/bin/python -m ipykernel install --prefix=/usr/local --name 'prod' --display-name "Python (Prod Env)"

### Cronicle
curl -s https://raw.githubusercontent.com/jhuckaby/Cronicle/master/bin/install.js | node
/opt/cronicle/bin/control.sh setup
cp systemd/cronicle.service /etc/systemd/system/cronicle.service
systemctl daemon-reload
systemctl enable cronicle.service
systemctl start cronicle.service
cp cronicle_useradd.js /opt/cronicle/bin/

echo "Adding first user account..."
bash ./conf.sh -u

echo "Configuring Cronicle access..."
bash ./conf.sh -a

echo "Installation finished. Please restart the server, otherwise hostname change might not be in effect and Cronicle might not start properly."
