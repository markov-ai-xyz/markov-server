### Server side code for Markov AI

#### Author: Anant Chandra
#### Company: ACN E-Commerce Private Limited ©

#### Python Startup (Dev Only -- Optional)
```
python wsgi.py
```

#### Build Docker Image (Dev Only)
```
docker build -f docker/Dockerfile -t anantchandra/markov:latest .
```

#### Install Docker (EC2 Only)
```
sudo yum update -y
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
exit
```

#### Pull Docker Image (EC2 Only)
```
docker login
docker pull anantchandra/markov:latest
```

#### Run Docker Image
```
docker run -p 80:8000 anantchandra/markov
```
