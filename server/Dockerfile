FROM python:3.12-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/file_streamer.proto ./proto/file_streamer.proto
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=. \
    --grpc_python_out=. \
    ./proto/file_streamer.proto

COPY server/main.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
