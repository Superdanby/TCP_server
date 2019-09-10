.PHONY: benchmark server client
benchmark:
	./benchmark.sh 127.0.0.1 8888 50
server:
	python3 server.py 127.0.0.1 8888 > /dev/null
client:
	python3 client.py 127.0.0.1 8888 > /dev/null
