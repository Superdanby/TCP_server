import asyncio
import argparse
import sys
import queue
import heapq

response_queue = []
rq_size = 0 # size of response queue
tcnt = 0
receive_cnt = 0

async def statistics():
    """Outputs the total transmitted response"""
    global tcnt
    while True:
        print(f"Total processed: {tcnt}\n", file=sys.stderr)
        await asyncio.sleep(1)

async def proton_api(message, cmd='printf') -> str:
    """Dummy Proton API, returns 200 permit, 200 reject, 400 REASON, or 500 REASON"""
    # Check out the ENCODING section of www.postfix.org/tcp_table.5.html
    return "200 permit\n"
    return "200 reject\n"
    return "500 permit\n"
    return "400 permit\n"
    proc = await asyncio.create_subprocess_shell(
        cmd + ' "200 permit\n"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    return stdout.decode()
    # return stdout

async def respond(writer, message, receive_cnt):
    """Wait for the results from proton_api and send it to the client, this function maintains a min-heap to ensure the outgoing order is the same as the incoming order"""
    # wait for response from Proton API
    response = await proton_api(message)

    global tcnt, cnt, rq_size
    # insert an element: [incoming order, encoded response]
    heapq.heappush(response_queue, [receive_cnt, response.encode()])
    rq_size = rq_size + 1

    # If response_queue is not empty and the element on top of min-heap has the smallest receive_cnt of all elements not yet sent, send the element. Repeat this step until the condition is not met.
    while rq_size != 0 and response_queue[0][0] == tcnt:
        _, leaving = heapq.heappop(response_queue)
        tcnt = tcnt + 1
        rq_size = rq_size - 1
        writer.write(leaving)
        await writer.drain()

async def handle_query(reader, writer):
    """This function reads request data from the client after a connection is established. After reading one request, it will initiate the respond() function to process the request and send it back, but instead of waiting respond() to finish its task, this function will continue to read the next request immediately."""
    global receive_cnt
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
        asyncio.create_task(respond(writer, message, receive_cnt))
        receive_cnt = receive_cnt + 1

    print("Close the connection")
    writer.close()

async def main(address='127.0.0.1', port=8888):
    server = await asyncio.start_server(handle_query, address, port)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    # real-time counter
    asyncio.create_task(statistics())

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
