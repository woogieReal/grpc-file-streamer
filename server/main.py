import grpc
import hashlib
import os
from concurrent import futures

import file_streamer_pb2
import file_streamer_pb2_grpc

OUTPUT_DIR = "/shared/output"


class FileStreamerServicer(file_streamer_pb2_grpc.FileStreamerServicer):
    def Upload(self, request_iterator, context):
        metadata = None
        received_bytes = 0
        hasher = hashlib.sha256()

        for request in request_iterator:
            kind = request.WhichOneof("data")

            if kind == "metadata":
                metadata = request.metadata
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                output_path = os.path.join(OUTPUT_DIR, metadata.file_name)
                f = open(output_path, "wb")
                print(f"[server] receiving: {metadata.file_name} ({metadata.total_size} bytes)")

            elif kind == "chunk":
                f.write(request.chunk)
                hasher.update(request.chunk)
                received_bytes += len(request.chunk)
                progress = int(received_bytes / metadata.total_size * 100)
                print(f"[server] progress: {progress}% ({received_bytes}/{metadata.total_size} bytes)")
                yield file_streamer_pb2.UploadResponse(progress=progress)

        f.close()

        computed_hash = hasher.hexdigest()
        success = computed_hash == metadata.original_hash
        print(f"[server] verification: {'OK' if success else 'FAIL'}")
        print(f"[server] expected: {metadata.original_hash}")
        print(f"[server] computed: {computed_hash}")

        yield file_streamer_pb2.UploadResponse(
            result=file_streamer_pb2.VerificationResult(
                success=success,
                message="integrity verified" if success else f"hash mismatch: expected {metadata.original_hash}, got {computed_hash}",
            )
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_streamer_pb2_grpc.add_FileStreamerServicer_to_server(FileStreamerServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("[server] listening on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
