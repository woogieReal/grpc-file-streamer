# gRPC File Streamer

> 로컬 학습용 프로젝트입니다. gRPC Bidirectional Streaming과 대용량 바이너리 처리를 실습하기 위해 제작했습니다.

gRPC Bidirectional Streaming을 활용한 고성능 대용량 파일 전송 시스템.
1GB 이상의 파일을 메모리 부담 없이 스트리밍 전송하고, SHA-256으로 무결성을 검증한다.

## 기술 스택

| 항목 | 내용 |
|---|---|
| Infrastructure | Docker, Docker Compose |
| Protocol | gRPC, Protocol Buffers v3 |
| Communication | Bidirectional Streaming RPC |
| Language | Python 3.12 |
| Integrity | SHA-256 |

## 프로젝트 구조

```
grpc-file-streamer/
├── proto/
│   └── file_streamer.proto   # 서비스 및 메시지 정의
├── server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py               # Upload RPC 핸들러
├── client/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py               # 파일 스트리밍 전송
├── shared/
│   ├── input/                # 전송할 원본 파일 위치
│   └── output/               # 서버가 수신한 파일 저장 위치
└── docker-compose.yml
```

## 동작 방식

```
Client                              Server
  │                                   │
  │── metadata (파일명, 크기, 해시) ─────>│
  │                                   │ 파일 오픈
  │── chunk (1MB) ──────────────────> │ 디스크 기록
  │ <─────────────── progress (10%) ──│
  │── chunk (1MB) ──────────────────> │ 디스크 기록
  │ <─────────────── progress (20%) ──│
  │         ...                       │     ...
  │── chunk (1MB) ──────────────────> │ 디스크 기록
  │ <─────────────── progress (100%) ─│
  │                                   │ SHA-256 검증
  │ <──────────── VerificationResult ─│
```

1. 클라이언트가 `metadata` 패킷(파일명, 총 크기, SHA-256 해시)을 먼저 전송
2. 파일을 1MB 단위로 분할해 `chunk` 패킷으로 연속 전송
3. 서버는 청크 수신 시마다 디스크에 기록하고 진행률(0~100%)을 실시간 반환
4. 전송 완료 후 서버에서 SHA-256 검증 수행 → `VerificationResult` 반환

## 실행 방법

**1. 전송할 파일을 `shared/input/`에 배치**

```bash
cp /path/to/your/file shared/input/
```

**2. 컨테이너 빌드 및 실행**

```bash
docker compose up --build
```

**3. 로그 확인**

```
grpc-file-streamer-server-1  | [server] listening on port 50051
grpc-file-streamer-client-1  | [client] uploading: /shared/input/sample.bin
grpc-file-streamer-client-1  | [client] sha256: 9472540f...
grpc-file-streamer-server-1  | [server] receiving: sample.bin (1073741824 bytes)
grpc-file-streamer-server-1  | [server] progress: 10% (...)
grpc-file-streamer-client-1  | [client] progress: 10%
...
grpc-file-streamer-server-1  | [server] verification: OK
grpc-file-streamer-client-1  | [client] success: integrity verified
```

전송 완료 후 `shared/output/`에 수신 파일이 저장된다.

## 검증 결과

1GB 파일 기준 테스트 결과 (`docs/3_verification-test/테스트결과.md` 참고):

| 항목 | 결과 |
|---|---|
| OOM 검증 | 서버 메모리 53MB로 일정 유지 (파일 크기와 무관) |
| 무결성 검증 | 원본/수신본 SHA-256 완전 일치 |
