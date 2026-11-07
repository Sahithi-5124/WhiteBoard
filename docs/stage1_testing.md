# Stage 1 – Server and Network Integration Testing

## 1. Objective

The objective of Stage 1 testing is to verify the basic TCP communication
between the WhiteBoard server and multiple clients.

The tests verify:

- Client connection and disconnection.
- Unique participant identification.
- Multiple simultaneous connections.
- Participant join and leave notifications.
- Message broadcasting.
- PING/PONG communication.
- TCP message framing.
- Handling of invalid JSON.
- Handling of oversized messages.
- Server stability after client disconnection.

## 2. Test Environment

| Component            | Configuration                            |
| -------------------- | ---------------------------------------- |
| Programming language | Python                                   |
| Network protocol     | TCP                                      |
| Message format       | JSON                                     |
| Message framing      | 4-byte unsigned big-endian length prefix |
| Default server port  | 5000                                     |
| Maximum message size | 1 MiB                                    |
| Concurrency model    | Thread per client                        |
| Test environment     | Localhost                                |

The integration test uses an automatically assigned local port.

## 3. Test Cases

| Test ID | Test case                       | Expected result                              |
| ------- | ------------------------------- | -------------------------------------------- |
| TC01    | Connect one client              | Server accepts the connection                |
| TC02    | Connect three clients           | All clients connect simultaneously           |
| TC03    | Assign participant IDs          | Each client receives a unique ID             |
| TC04    | Participant joins               | USER_JOINED notification is broadcast        |
| TC05    | Send chat message               | All connected clients receive CHAT_BROADCAST |
| TC06    | Send PING                       | Server responds with PONG                    |
| TC07    | Send consecutive messages       | Both messages are processed independently    |
| TC08    | Send fragmented TCP message     | Server reconstructs the complete message     |
| TC09    | Disconnect one client           | Server removes the participant               |
| TC10    | Participant leaves              | Remaining clients receive USER_LEFT          |
| TC11    | Disconnect one of three clients | Other clients remain connected               |
| TC12    | Reconnect a client              | Server accepts the new connection            |
| TC13    | Send invalid JSON               | Invalid connection is rejected               |
| TC14    | Send oversized message          | Message is rejected                          |
| TC15    | Server recovery                 | Server continues accepting valid clients     |

## 4. Execution

Run the integration test from the repository root:

```powershell
python tests/stage1_integration_test.py
```

The script starts a temporary server, executes the test cases, and shuts down
the server afterward.

No external Python packages are required for this test script.

## 5. Results

Record the actual test results after execution.

| Test ID | Actual result  | Status  |
| ------- | -------------- | ------- |
| TC01    | To be recorded | Pending |
| TC02    | To be recorded | Pending |
| TC03    | To be recorded | Pending |
| TC04    | To be recorded | Pending |
| TC05    | To be recorded | Pending |
| TC06    | To be recorded | Pending |
| TC07    | To be recorded | Pending |
| TC08    | To be recorded | Pending |
| TC09    | To be recorded | Pending |
| TC10    | To be recorded | Pending |
| TC11    | To be recorded | Pending |
| TC12    | To be recorded | Pending |
| TC13    | To be recorded | Pending |
| TC14    | To be recorded | Pending |
| TC15    | To be recorded | Pending |

## 6. Conclusion

The Stage 1 integration test is designed to verify the server's basic
multi-client communication, participant tracking, message framing, and
connection handling.

The conclusion should be finalized only after executing the tests and
recording the actual results.
