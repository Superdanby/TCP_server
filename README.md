# TCP_server

This is a single-thread asynchronize tcp server.

There's a dummy command line execution pretending to be a real api call.

[Notes](https://hackmd.io/UbJ_ZsLbT7KS1Fs6dt55Qg?both)

## Execution and Benchmarking

Run the server with:
`python3 server.py [server ip address] [port]`

Run the client to benchmark the server:
```
usage: client.py [-h] address port [messages] [concurrency]

positional arguments:
  address      server address
  port         server port
  messages     total number of messages to send, defaults to 1
  concurrency  number of messages to send at a time, defaults to 1
```

## Performance

On Fedora 30, i7-8705g(4C8T, @3.10GHz):

47k ~ 50k requests per second
