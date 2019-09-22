import asyncio
import aiohttp # pip install aiohttp[speedups]
import argparse
import time
import cProfile, pstats, io
from pstats import SortKey
import ssl

semaphore = 3e4

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

async def respond(writer, message, api_session):
    """Wait for the results from proton_api and send it to the client, writes and reads with Proton API is protected with a lock to ensure FIFO order"""
    global semaphore
    # writer.write("200 permit\n".encode())
    # await writer.drain()
    # semaphore = semaphore + 1
    # return

    print('https://localhost/api/mail/incoming/recipient?Email=' + message[4:-1])
    try:
        resp = await api_session.get('https://localhost/api/mail/incoming/recipient?Email=' + message[4:-1])
        async with resp:
            if resp.status == 200 or resp.status == 204:
                response = "200 permit\n"
            elif resp.status == 422:
                dict = await resp.json()
                response = "200 reject\n"
            elif resp.status == 400:
                response = "500 bad request\n"
            else:
                response = "400 " + dict['Error'] + "\n"
    except:
        response = "500 bad request\n"

    writer.write(response.encode())
    # prevent the server from outputing too much error caused by connection failure, thus not serving new requests
    try:
        await writer.drain()
    except:
        pass
    semaphore = semaphore + 1

async def handle_query(reader, writer, api_session):
    """This function reads request data from the client after a connection is established. After reading one request, it will initiate the respond() function to process the request and send it back, but instead of waiting respond() to finish its task, this function will continue to read the next request immediately."""
    # pr = cProfile.Profile()
    # pr.enable()
    global semaphore
    cnt = 0
    tasks = []
    while True:
        # read data from client
        data = await reader.readline()
        message = data.decode()
        if message == '':
            break
        # print(data)

        # the server can handle only around 20k requests per second, creating too many tasks will slow down the asyncio scheduler
        while semaphore == 0:
            # semaphore is initialized with 30k, which takes about 1.5s to process all requests, sleep for 1 second have a smaller impact on performance compared to sleep for 0 seconds
            await asyncio.sleep(1)
        # non blocking function call to respond()
        tasks.append(asyncio.create_task(respond(writer, message, api_session)))
        semaphore = semaphore - 1

        # reset connection when EOF reached
        if reader.at_eof():
            break

    # wait for the last response to be read by client
    while len(tasks) != 0:
        done, tasks = await asyncio.wait(tasks)

    # close the connection gracefully
    if writer.can_write_eof():
        writer.write_eof()
    print("Close client connection")
    writer.close()
    # pr.disable()
    # s = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print(s.getvalue())

async def main(address='127.0.0.1', port=8888):
    api_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx, limit_per_host=25))
    server = await asyncio.start_server(lambda r, w: handle_query(r, w, api_session), address, port)

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
