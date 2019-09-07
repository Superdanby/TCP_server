.PHONY: benchmark server client
benchmark: server client
server:
	python3 server.py 127.0.0.1 8888 > /dev/null
client:
	python3 client.py 127.0.0.1 8888 &
