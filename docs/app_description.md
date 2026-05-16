# High-Performance Binary File Streamer Spec

## 1. Project Overview
본 프로젝트는 gRPC의 양방향 스트리밍(Bidirectional Streaming)과 바이너리 데이터(`bytes`) 처리 역량을 활용하여, 로컬의 대용량 파일(1GB 이상)을 빠르고 안정적으로 업로드하고 무결성을 검증하는 고성능 파일 전송 시스템이다.

## 2. Technical Stack
* **Infrastructure**: Docker, Docker Compose
* **Protocol**: gRPC, Protocol Buffers v3
* **Communication Pattern**: Bidirectional Streaming RPC
* **Data Format**: Binary (`bytes`)
* **Integrity Algorithm**: SHA-256

## 3. Container Architecture & Shared Volume
멀티 컨테이너 환경에서 클라이언트가 서버로 실제 대용량 파일을 전송하고, 서버가 이를 온전히 조립하여 저장하는 독립된 가상 네트워크를 구축한다.

* **gRPC Server Container**: `50051` 포트를 열고 클라이언트의 파일 스트림 요청을 대기한다. 업로드 완료 후 내부 디렉토리에 파일을 최종 저장한다.
* **gRPC Client Container**: 로컬 디렉토리의 대용량 파일을 인식하여 서버 컨테이너로 스트리밍 전송을 수행한다.
* **Shared Storage Volume**: 호스트 디렉토리 마운트 방식을 사용한다. 원본 파일과 서버가 수신하여 저장한 복구 파일 모두 호스트의 단일 디렉토리에 위치하며, 클라이언트/서버 컨테이너가 각각 해당 경로를 마운트하여 접근한다.

## 4. Proto Message Design

### UploadRequest (Client → Server)
스트림 내에서 메타데이터 패킷과 청크 패킷을 하나의 메시지 타입으로 구분하기 위해 `oneof`를 사용한다.

```protobuf
message UploadRequest {
  oneof data {
    FileMetadata metadata = 1;
    bytes chunk = 2;
  }
}

message FileMetadata {
  string file_name = 1;
  int64 total_size = 2;
  string original_hash = 3;  // SHA-256 hex string
}
```

### UploadResponse (Server → Client)
진행률 피드백과 최종 검증 결과를 하나의 스트림으로 반환하기 위해 `oneof`를 사용한다.

```protobuf
message UploadResponse {
  oneof response {
    int32 progress = 1;          // 수신 완료 퍼센트 (0~100)
    VerificationResult result = 2;
  }
}

message VerificationResult {
  bool success = 1;
  string message = 2;
}
```

## 5. Detailed Data Workflow
1. **Client** -> **Server** (Initial Packet)
   * `UploadRequest.metadata` 형태로 파일 이름, 총 크기, 원본 SHA-256 해시를 전송.
2. **Client** -> **Server** (Streaming Phase)
   * 파일을 1MB 단위의 청크로 분할하여 `UploadRequest.chunk` 패킷을 연속적으로 전송.
3. **Server** -> **Client** (Real-time Feedback)
   * 청크가 디스크에 기록될 때마다 누적 수신량을 계산하여 `UploadResponse.progress`(퍼센트, 0~100)를 실시간 반환.
4. **Server** -> **Client** (Final Packet)
   * 스트림 종료(End of Stream) 신호 수신 시 서버는 파일 조립을 마감하고 SHA-256 검증을 수행.
   * `UploadResponse.result`로 검증 성공 여부와 메시지를 반환 후 세션 종료.

## 6. Verification & Testing
* **OOM 검증**: 1GB 이상의 파일을 업로드하는 동안 클라이언트와 서버 프로세스의 메모리 점유율이 일정하게 유지되는지 확인 (Stream I/O 정상 작동 여부).
* **무결성 테스트**: 전송이 완료된 파일(예: 대용량 .zip 파일)을 로컬에서 직접 압축 해제하여 파일이 단 1비트도 깨지지 않고 온전히 전송되었는지 검증.
