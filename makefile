.PHONY: benchmark server client client1 client2 client3 client4 client5 client6 client7
benchmark: server client client1 client2 client3 client4 client5 client6 client7
server:
	python3 server.py 127.0.0.1 8888 > /dev/null
client:
	python3 client.py 127.0.0.1 8888 > /dev/null
client1:
	python3 client.py 127.0.0.1 8888 > /dev/null
client2:
	python3 client.py 127.0.0.1 8888 > /dev/null
client3:
	python3 client.py 127.0.0.1 8888 > /dev/null
client4:
	python3 client.py 127.0.0.1 8888 > /dev/null
client5:
	python3 client.py 127.0.0.1 8888 > /dev/null
client6:
	python3 client.py 127.0.0.1 8888 > /dev/null
client7:
	python3 client.py 127.0.0.1 8888 > /dev/null
