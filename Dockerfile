FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cach-dir -r requirements.txt
