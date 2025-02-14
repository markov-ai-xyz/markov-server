FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip

RUN apt-get update && \
    apt-get install -y curl build-essential libgl1 libglib2.0-0 \
    libgtk-3-0 libjpeg-dev libpng-dev libtiff-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN curl --create-dirs -o $HOME/.postgresql/root.crt 'https://cockroachlabs.cloud/clusters/23a6127e-594b-46ab-99d9-e263be7a0bf4/cert'

EXPOSE 8000

CMD ["gunicorn", "--config", "./config/gunicorn_config.py", "wsgi:markov"]
