FROM python:3.9.11-slim

WORKDIR /app

COPY requirements.txt /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies and clean up
RUN apt update && \
    apt install -y tesseract-ocr tesseract-ocr-spa && \
    rm -rf /var/lib/apt/lists/*

COPY . /app


# Database Configuration
ENV DATABASE_PATH=DATABSE.xlsx
ENV MATERIALS_LIST_PATH=materials_list.txt




# Flask Configuration (optional)
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Server Configuration (optional)
ENV HOST=0.0.0.0
ENV PORT=5001
EXPOSE 5001

ENV FLASK_APP=api.py

ENV FLASK_ENV=production
