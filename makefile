.PHONY: benchmark server client
benchmark:
	python3 client.py 127.0.0.1 8888 1000000 100
server:
	python3 server.py 127.0.0.1 8888
client:
	python3 client.py 127.0.0.1 8888
