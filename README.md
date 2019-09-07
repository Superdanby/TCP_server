# TCP_server

This is a single-thread asynchronize tcp server.
There's a dummy command line execution to imitate a real api call.

## Execution

Run the server with:
`python3 server.py [server ip address] [port]`

Run the client with:
`python3 client.py [server ip address] [port]`

## Benchmark
Benchmark the server with `make -j`

## Performance
The server processes around 450 requests per second on Fedora 30, i7-8705g 
