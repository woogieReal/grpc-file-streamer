import grpc
import file_streamer_pb2_grpc


def run():
    with grpc.insecure_channel("server:50051") as channel:
        grpc.channel_ready_future(channel).result(timeout=10)
        print("[client] connected to server:50051")


if __name__ == "__main__":
    run()
