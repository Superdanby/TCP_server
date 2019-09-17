import asyncio
import argparse

semaphore = 5e4

async def respond(writer, message, api_reader, api_writer, lock):
    """Wait for the results from proton_api and send it to the client, writes and reads with Proton API is protected with a lock to ensure FIFO order"""
    global semaphore
    # writer.write("200 permit\n".encode())
    # await writer.drain()
    # return

    query = (
        f"GET {'/mail/incoming/rcpt?Email=' + message[4:-1]} HTTP/1.1\r\n"
        f"\r\n"
    )
    # print(query.encode())
    api_writer.write(query.encode('utf-8'))
    Error = None

    # make sure requests to proton api are FIFO
    async with lock:
        # prevent the server from outputing too much error caused by connection failure, thus not serving new requests
        try:
            await writer.drain()
        except:
            pass

        # get status code
        line = await api_reader.readline()
        status_code = line
        # print(line)


        # get Error field
        while True:
            line = await api_reader.readline()
            if not line:
                break
            # print(line)
            response = line.decode('utf-8').rstrip()
            if not response:
                break
            if response[0:7] == 'Error: ':
                Error = response[7:]
            # print(f'HTTP header> {line}')

    if Error:
        status_code = status_code.decode('utf-8').split(' ', 2)[1]
    else:
        status_code, Error = status_code.decode('utf-8').split(' ', 1)[1].split(' ', 1)

    # permit
    if status_code[0] == '2':
        response = "200 permit\n"
    # reject
    if status_code == '422':
        response = "200 reject\n"
    else: # temporary rejects
        response = "400 Proton API: " + status_code + " " + Error + "\n"

    # print(response)
    writer.write(response.encode())
    # prevent the server from outputing too much error caused by connection failure, thus not serving new requests
    try:
        await writer.drain()
    except:
        pass
    semaphore = semaphore + 1

async def handle_query(reader, writer):
    """This function reads request data from the client after a connection is established. After reading one request, it will initiate the respond() function to process the request and send it back, but instead of waiting respond() to finish its task, this function will continue to read the next request immediately."""
    global semaphore
    retry_api = True
    # open tcp connection to localhost:443
    # api_reader, api_writer = await asyncio.open_connection('localhost', 443, ssl=True)
    while retry_api:
        retry_api = False
        try:
            api_reader, api_writer = await asyncio.open_connection('localhost', 80)
        except:
            print("API connection failure!")
            retry_api = True
            await asyncio.sleep(0.1)
    lock = asyncio.Lock()
    while True:
        # read data
        data = await reader.readline()
        message = data.decode()

        # reset connection when EOF reached
        if reader.at_eof():
            break

        # the server can handle only around 20k requests per second, creating too many tasks will slow down the asyncio scheduler
        while semaphore == 0:
            # semaphore is initialized with 50k, which takes about 2.5s to process all requests, sleep for 1 second have a smaller impact on performance compared to sleep for 0 seconds
            await asyncio.sleep(1)
        # non blocking function call to respond()
        non_blocking = asyncio.create_task(respond(writer, message, api_reader, api_writer, lock))
        semaphore = semaphore - 1

    # wait for the last response to be read by client
    done, pending = await asyncio.wait({non_blocking})
    while non_blocking not in done:
        done, pending = await asyncio.wait({non_blocking})

    # close the connection gracefully
    if writer.can_write_eof():
        writer.write_eof()
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
