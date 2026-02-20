# ===============================
# BASE IMAGE
# ===============================
FROM python:3.10-slim

# ===============================
# SYSTEM DEPENDENCIES
# (dibutuhkan sklearn & Sastrawi)
# ===============================
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ===============================
# WORKDIR
# ===============================
WORKDIR /app

# ===============================
# COPY & INSTALL PYTHON LIBS
# ===============================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===============================
# COPY SOURCE CODE
# ===============================
COPY . .

# ===============================
# EXPOSE FLASK PORT
# ===============================
EXPOSE 5000

# ===============================
# RUN FLASK APP
# ===============================
CMD ["python", "app.py"]
