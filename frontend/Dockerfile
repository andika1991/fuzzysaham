FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Supaya log langsung tampil
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependency system minimum
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dulu (biar cache efisien)
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port Flask
EXPOSE 5000

# Jalankan dengan gunicorn (lebih hemat dari flask run)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
