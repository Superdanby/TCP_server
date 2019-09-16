import asyncio
import argparse
import sys
import queue
import heapq

async def respond(writer, message, api_reader, api_writer, lock):
    """Wait for the results from proton_api and send it to the client, this function maintains a min-heap to ensure the outgoing order is the same as the incoming order"""
    writer.write("200 permit\n".encode())
    # async with lock:
    await writer.drain()
    return

    # check string format, messages from postfix probably don't need this
    # if message[0:4] != 'GET ' and len(message) != 4:
    #     return '500 Wrong format: ' + message + '\n'
    query = (
        f"GET {'localhost/mail/incoming/rcpt?Email=' + message[4:]} HTTP/1.1\n"
        f"\n"
    )
    writer.write(query.encode('utf-8'))
    async with lock:
        await writer.drain()

        # get status code
        line = await reader.readline()
        status_code = line.decode('utf-8').split(' ')[1]

        response = '400 Proton API responds with empty string'

        if status_code[0] == '2':
            response = "200 permit\n"

        Error = ''
        # get Error field
        while True:
            line = await reader.readline()
            if not line:
                break
            response = line.decode('utf-8').rstrip()
            if not response:
                break
            if response[0:7] == 'Error: ':
                Error = response[7:]
            # print(f'HTTP header> {line}')

    # reject user
    if status_code == '422':
        response =  "200 reject\n"
    else: # temporary rejects
        response = "400 " + Error + "\n"

    writer.write(leaving)
    await writer.drain()

async def handle_query(reader, writer):
    """This function reads request data from the client after a connection is established. After reading one request, it will initiate the respond() function to process the request and send it back, but instead of waiting respond() to finish its task, this function will continue to read the next request immediately."""
    # open tcp connection to localhost:443
    api_reader, api_writer = None, None
    # api_reader, api_writer = await asyncio.open_connection('localhost', 443, ssl=True)
    lock = asyncio.Lock()
    while True:
        # read data
        data = await reader.readline()
        message = data.decode()
        # addr = writer.get_extra_info('peername')
        # cmprs = writer.get_extra_info('compression')
        # print(f"Received {message!r} from {addr!r}, compression: {cmprs}, ateof: {reader.at_eof()}")

        # prevent reader from stucking in EOF state resolves issue #2
        if reader.at_eof():
            reader._eof = False
            continue

        # non blocking function call to respond()
        asyncio.create_task(respond(writer, message, api_reader, api_writer, lock))

    print("Close the connection")
    writer.close()

async def main(address='127.0.0.1', port=8888):
    server = await asyncio.start_server(handle_query, address, port)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')
args = parser.parse_args()
# print(args)

if __name__ == '__main__':
    asyncio.run(main(address=args.address[0], port=args.port[0]))
