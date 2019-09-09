# TCP_server

This is a single-thread asynchronize tcp server.

There's a dummy command line execution pretending to be a real api call.

[Notes](https://hackmd.io/UbJ_ZsLbT7KS1Fs6dt55Qg?both)

## Execution

Run the server with:
`python3 server.py [server ip address] [port] [--persistent(specify this option when messages per connection is not 0)]`

Run the client with:
`python3 client.py [server ip address] [port] [messages per connection, defaults to 0]`

## Benchmark

Benchmark the server with `make benchmark`, `make benchmark_persistent`, or `./benchmark.sh [server ip address] [port] [period in seconds] [messages per connection]`

## Performance

On Fedora 30, i7-8705g(4C8T, @3.10GHz):

| messages per connection | with `printf` system call | without any system call |
| :---: | :---: | :---: |
| 1 | 730 requests per second | 5250 requests per second |
| 10000 | 870 requests per second | 21000 requests per second |

Note that the number of client processes will have an impact on the number of requests received by the server.
