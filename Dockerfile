FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY academic_research/ ./academic_research/

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Ejecutar ADK web interface (equivalente a comando: adk web)
CMD ["adk", "web", "--port", "8080", "--host", "0.0.0.0"]
