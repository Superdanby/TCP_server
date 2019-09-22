import asyncio
import argparse
import cProfile, pstats, io
from pstats import SortKey
import ssl
# import time

# Semaphore locks should use this form to prevent deadlocks:
# while semaphore == 0:
#     await asyncio.sleep(0)
client_semaphore = 3e4 # limit number of requests from client
api_semaphore = 25 # limit simultaneous connections to API
connection_lock = None # establish a connection to API one at a time

# disable certificate check
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

async def api_connect(client_writer=None):
    """Create connections to API"""
    global api_semaphore
    api_reader, api_writer = None, None
    retry_api = True
    # establish a connection to API one at a time
    async with connection_lock:
        while api_semaphore == 0:
            await asyncio.sleep(0)
        while retry_api:
            if client_writer and client_writer.transport.is_closing():
                print("Client connection lost. Abort API connection establishment.")
                break
            retry_api = False
            try:
                api_reader, api_writer = await asyncio.open_connection('localhost', 443, ssl=ctx)
                print("API connection established!")
                api_semaphore = api_semaphore - 1
            except Exception as e:
                print("Failed to connect to API!")
                print(e)
                retry_api = True
                await asyncio.sleep(5)
    return [api_reader, api_writer]

async def api_disconnect(api_writer):
    """Close connections to API"""
    global api_semaphore
    print("API connection closed.")
    api_writer.close()
    api_semaphore = api_semaphore + 1
    await api_writer.wait_closed()
    print("API connection closed done.")

async def respond(writer, message, api_connection, lock):
    """Wait for the results from proton_api and send it to the client, writes and reads with Proton API is protected with a lock to ensure FIFO order"""
    global client_semaphore
    # writer.write("200 permit\n".encode())
    # await writer.drain()
    # client_semaphore = client_semaphore + 1
    # return

    query = (
        f"GET {'/api/mail/incoming/recipient?Email=' + message[4:-1]} HTTP/1.1\r\n"
        f"Host: localhost\r\n"
        f"Accept: */*\r\n"
        f"\r\n"
    ).encode('utf-8')

    # start_time = time.time()

    # make sure requests to proton api are FIFO
    async with lock:
        if writer.transport.is_closing():
            return # client connection lost
        resend = True
        while resend:
            api_reader, api_writer = api_connection
            resend = False
            api_writer.write(query)
            # prevent the server from outputing too much error caused by connection failure, thus not serving new requests
            try:
                await api_writer.drain()
            except:
                pass

            # get response form API
            line = await api_reader.read(20000)
            api_response = line.decode('utf-8')
            if api_response == '':
                print("API connection interrupted!")
                await api_disconnect(api_writer)
                api_connection[0], api_connection[1] = await api_connect(writer)
                if writer.transport.is_closing():
                    return # client connection lost
                print("Reconnected to API!")
                resend = True

        status_code = api_response[9:12] # HTTP/1.1 xxx
        # permit
        if status_code[0] == '2':
            response = "200 permit\n"
        # reject
        else:
            try:
                Error = api_response.split('"Error": "', 1)[1].split('"', 1)[0]
                if status_code == '422':
                    await api_reader.read(100) # Remove the weird additional message
                    response = "200 reject\n"
                else: # temporary rejects
                    response = "400 " + status_code + " " + Error + "\n"
            except IndexError:
                if status_code == '400':
                    print("Bad request! Reseting connection...")
                    await api_disconnect(api_writer)
                    api_connection[0], api_connection[1] = await api_connect(writer)
                    if writer.transport.is_closing():
                        return # client connection lost
                    print("Reconnected to API!")
                    response = "500 bad request\n"
                else: # temporary rejects
                    response = "400 " + api_response.split('\r\n', 1)[0] + "\n"

        # reply to client
        writer.write(response.encode())
    # prevent the server from outputing too much error caused by connection failure, thus not serving new requests
    try:
        await writer.drain()
    except:
        pass
    client_semaphore = client_semaphore + 1
    # print(time.time() - start_time)

async def handle_query(reader, writer):
    """This function reads request data from the client after a connection is established. After reading one request, it will initiate the respond() function to process the request and send it back, but instead of waiting respond() to finish its task, this function will continue to read the next request immediately."""
    # enable profiler
    # pr = cProfile.Profile()
    # pr.enable()
    global client_semaphore

    lock = asyncio.Lock()
    api_connection = await api_connect(writer) # connect to API; api_connection is a list so that the underlying connection to API can be swapped for all requests already in respond() if must
    if writer.transport.is_closing():
        return # client connection lost
    while True:
        # read data from client
        data = await reader.readline()
        message = data.decode()

        # the server can handle only around 20k requests per second, creating too many tasks will slow down the asyncio scheduler
        while client_semaphore == 0:
            # client_semaphore is initialized with 30k, which takes about 1.5s to process all requests, sleep for 1 second have a smaller impact on performance compared to sleep for 0 seconds
            await asyncio.sleep(1)
        # non blocking function call to respond()
        non_blocking = asyncio.create_task(respond(writer, message, api_connection, lock))
        client_semaphore = client_semaphore - 1

        # reset connection when EOF reached
        if reader.at_eof():
            break

    # wait for the last response to be read by client
    done, pending = await asyncio.wait({non_blocking})
    while non_blocking not in done:
        done, pending = await asyncio.wait({non_blocking})

    # close the connection gracefully
    if writer.can_write_eof():
        writer.write_eof()
    writer.close()
    print("Client connection closed.")
    if api_connection[1]:
        await api_disconnect(api_connection[1])
    # disable profiler
    # pr.disable()
    # s = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print(s.getvalue())

async def main(address='127.0.0.1', port=8888):
    global connection_lock
    connection_lock = asyncio.Lock()
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
