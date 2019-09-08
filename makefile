.PHONY: benchmark server client
benchmark:
	./benchmark.sh 127.0.0.1 8888 30
benchmark_persistant:
	./benchmark.sh 127.0.0.1 8888 50 10000
server:
	python3 server.py 127.0.0.1 8888 > /dev/null
client:
	python3 client.py 127.0.0.1 8888 > /dev/null
