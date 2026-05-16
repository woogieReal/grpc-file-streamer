import grpc
import hashlib
import os

import file_streamer_pb2
import file_streamer_pb2_grpc

INPUT_DIR = "/shared/input"
CHUNK_SIZE = 1 * 1024 * 1024  # 1MB


def compute_sha256(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_requests(file_path):
    file_name = os.path.basename(file_path)
    total_size = os.path.getsize(file_path)
    original_hash = compute_sha256(file_path)

    print(f"[client] file: {file_name} ({total_size} bytes)")
    print(f"[client] sha256: {original_hash}")

    yield file_streamer_pb2.UploadRequest(
        metadata=file_streamer_pb2.FileMetadata(
            file_name=file_name,
            total_size=total_size,
            original_hash=original_hash,
        )
    )

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            yield file_streamer_pb2.UploadRequest(chunk=chunk)


def run():
    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
    if not files:
        print("[client] no files found in /shared/input")
        return

    file_path = os.path.join(INPUT_DIR, files[0])
    print(f"[client] uploading: {file_path}")

    with grpc.insecure_channel("server:50051") as channel:
        stub = file_streamer_pb2_grpc.FileStreamerStub(channel)
        responses = stub.Upload(generate_requests(file_path))

        for response in responses:
            kind = response.WhichOneof("response")
            if kind == "progress":
                print(f"[client] progress: {response.progress}%")
            elif kind == "result":
                result = response.result
                if result.success:
                    print(f"[client] success: {result.message}")
                else:
                    print(f"[client] failed: {result.message}")


if __name__ == "__main__":
    run()
