FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY proxy.py .
COPY config.example.json config.json

EXPOSE 8887
CMD ["python", "proxy.py"]
