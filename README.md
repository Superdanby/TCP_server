# TCP_server

This is a single-thread asynchronize tcp server.

There's a dummy command line execution pretending to be a real api call.

[Notes](https://hackmd.io/UbJ_ZsLbT7KS1Fs6dt55Qg?both)

## Execution

Run the server with:
`python3 server.py [server ip address] [port]`

Run the client with:
`python3 client.py [server ip address] [port]`

## Benchmark

Benchmark the server with `make benchmark` or `./benchmark.sh [server ip address] [port] [period in seconds] [number of clients]`

## Performance

On Fedora 30, i7-8705g(4C8T, @3.10GHz):

45k ~ 47k requests per second
