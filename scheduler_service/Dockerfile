FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Default: run scheduler loop
CMD ["python", "-m", "scheduler_service.app.events.scheduler_runner"]