#!/bin/bash
# ec2 initialization setup
# user_data already launched as root (no need sudo -s)

echo 'Start ...'
apt update -y
apt upgrade -y

# docker installation
apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update -y
apt install docker-ce -y
# docker-compose installation
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
# Give docker permission to ubuntu user
usermod -aG docker ubuntu
# Install aws tools
apt install amazon-ec2-utils
# Create a workspace folder
mkdir -p /home/ubuntu/workspace
cd /home/ubuntu/workspace
# Download docker-compose.yml
git clone https://github.com/raphael-chir/transactions-st.git
# Launch containers
cd /home/ubuntu/workspace/transactions-st
public_hostname=$(ec2-metadata -p | cut -d " " -f 2)
env EC2_DNS=$public_hostname bash -c 'docker-compose up -d'
# Create a topic
sleep 20
docker exec transactions-st-kafka-1 kafka-topics.sh --create --topic test --bootstrap-server $public_hostname:9092 --partitions 1 --replication-factor 1