import grpc
from concurrent import futures
import file_streamer_pb2_grpc


class FileStreamerServicer(file_streamer_pb2_grpc.FileStreamerServicer):
    def Upload(self, request_iterator, context):
        return iter([])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_streamer_pb2_grpc.add_FileStreamerServicer_to_server(FileStreamerServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("[server] listening on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
