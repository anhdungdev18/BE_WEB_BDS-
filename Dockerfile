# Dockerfile - build image cho Django backend

FROM python:3.13-slim

# Cài các thư viện cần thiết để build mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Thư mục làm việc trong container
WORKDIR /app

# Copy requirements và cài lib
COPY requirements.web.txt .
RUN pip install --no-cache-dir -r requirements.web.txt


# Copy toàn bộ code project vào container
COPY . .

# Không buffer stdout của Python
ENV PYTHONUNBUFFERED=1

# Mở port 8000 (trong container)
EXPOSE 8000

# Lệnh mặc định: chạy migrate rồi runserver
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
