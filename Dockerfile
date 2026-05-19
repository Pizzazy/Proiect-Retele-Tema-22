FROM python:3.11-slim

WORKDIR /app
COPY src ./src
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/tunnel_local.py"]
