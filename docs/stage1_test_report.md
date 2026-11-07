# Stage 1 - TCP Client-Server Testing Report

## 1. Objective

To verify TCP communication between multiple WhiteBoard clients
and the central server using the shared JSON message protocol.

## 2. Test Environment

- Language: Python
- Communication: TCP sockets
- Message format: UTF-8 JSON
- Message framing: 4-byte big-endian length prefix
- Testing framework: pytest

## 3. Unit Tests

| Test                     | Expected result                | Actual result |
| ------------------------ | ------------------------------ | ------------- |
| Message creation         | Correct protocol envelope      | Pending       |
| Message send and receive | Original message received      | Pending       |
| Fragmented message       | Complete message reconstructed | Pending       |
| Oversized message        | Message rejected               | Pending       |
| Invalid JSON             | Message rejected               | Pending       |
| Clean disconnect         | Receiver returns None          | Pending       |

## 4. Integration Tests

| Test                 | Expected result               | Actual result |
| -------------------- | ----------------------------- | ------------- |
| Client connection    | Client connects successfully  | Pending       |
| Multiple clients     | Both clients connect          | Pending       |
| Message broadcast    | Other clients receive message | Pending       |
| Client disconnection | USER_LEFT event received      | Pending       |
| Heartbeat            | PONG received after PING      | Pending       |
| LAN communication    | Remote client connects        | Pending       |

## 5. Issues Encountered

Record errors, their causes and the fixes applied.

## 6. Final Result

Status: Pending

All tests must pass before Stage 1 is marked complete.
