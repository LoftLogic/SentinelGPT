FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y iputils-ping
WORKDIR /app
COPY worker.py /app/worker.py
CMD ["python", "/app/worker.py"]
