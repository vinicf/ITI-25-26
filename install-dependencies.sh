# Install dependencies for UM Drive demo app

# Update package list
apt-get update

# Install required packages
apt-get install -y python3.12-venv python3-pip nfs-common tmux

# You could git clone your repo here, and proceed.

# Install UM Drive's python requirements
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r /home/vagrant/um_drive/requirements.txt

