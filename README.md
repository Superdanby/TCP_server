# TCP_server

This is a single-thread asynchronize tcp server.
There's a dummy command line execution pretending to be a real api call.

## Execution

Run the server with:
`python3 server.py [server ip address] [port]`

Run the client with:
`python3 client.py [server ip address] [port]`

## Benchmark

Benchmark the server with `make` or `./benchmark.sh [server ip address] [port] [period in seconds]`

## Performance

### With a `printf` system call:
The server processes around 700 requests per second on Fedora 30, i7-8705g.

### Without doing anything:
The server processes around 4400 requests per second on Fedora 30, i7-8705g.

Note that the number of client processes will have an impact on the number of requests received by the server.
