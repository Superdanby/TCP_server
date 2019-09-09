import asyncio
import argparse
import sys
import queue
import heapq


period = 10
q = queue.Queue(maxsize=period)
qsize = 0
period_cnt = 0
response_queue = []
rq_size = 0
tcnt = 0
receive_cnt = 0
cnt = 0

async def statistics():
    global cnt, period_cnt, qsize
    while True:
        if qsize == period:
            period_cnt = period_cnt - q.get()
            qsize = qsize - 1
        period_cnt = period_cnt + cnt
        qsize = qsize + 1
        q.put(cnt)
        cnt = 0
        print(f"Processed per second: {period_cnt / qsize}\n", file=sys.stderr)
        await asyncio.sleep(1)

async def proton_api(message, cmd='printf'):
    # if message[0:4] == 'GET ':
    #     return '400 format error\n'.encode()
    return "200 permit\n"
    return "200 reject\n"
    return "500 permit\n"
    return "400 permit\n"
    proc = await asyncio.create_subprocess_shell(
        cmd + ' "200 danny@mail.yohoho.localdomain\n"',
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

async def handle_query(reader, writer):
    global cnt
    data = await reader.read(512)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    cmprs = writer.get_extra_info('compression')

    # print(f"Received {message!r} from {addr!r}")
    print(f"Received {message!r} from {addr!r}, compression: {cmprs}")

    # wait for response from Proton API
    # response = await proton_api(message)
    response = "200 permit\n".encode()
    # response = "200 reject\n".encode()
    # response = "500 permit\n".encode()
    # response = "400 permit\n".encode()

    writer.write(response)
    # writer.write(response.encode())
    await writer.drain()

    print("Close the connection")
    writer.close()
    cnt = cnt + 1

async def respond(writer, message, receive_cnt):
    # wait for response from Proton API
    response = await proton_api(message)
    # response = "200 foo\n".encode()

    # Check out the ENCODING section of www.postfix.org/tcp_table.5.html
    response = response.encode()
    global tcnt, cnt, rq_size
    heapq.heappush(response_queue, [receive_cnt, response])
    rq_size = rq_size + 1
    while rq_size != 0 and response_queue[0][0] == tcnt:
        _, leaving = heapq.heappop(response_queue)
        tcnt = tcnt + 1
        cnt = cnt + 1
        rq_size = rq_size - 1
        writer.write(leaving)
        await writer.drain()

async def handle_query_persistent(reader, writer):
    global receive_cnt
    while True:
        data = await reader.read(512) # 4096 chars have 512 bytes
        message = data.decode()
        if message == "close":
            break
        addr = writer.get_extra_info('peername')
        cmprs = writer.get_extra_info('compression')
        # print(f"Received {message!r} from {addr!r}")
        print(f"Received {message!r} from {addr!r}, compression: {cmprs}")

        asyncio.create_task(respond(writer, message, receive_cnt))
        receive_cnt = receive_cnt + 1

    print("Close the connection")
    writer.close()

async def main(address='127.0.0.1', port=8888, persistent=False):
    if persistent:
        server = await asyncio.start_server(handle_query_persistent, address, port)
    else:
        server = await asyncio.start_server(handle_query, address, port)


    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    asyncio.create_task(statistics())

    async with server:
        await server.serve_forever()

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')
parser.add_argument('--persistent', action='store_true', help='open connection until client sends "close"')
args = parser.parse_args()

# print(args)

if __name__ == '__main__':
    asyncio.run(main(address=args.address[0], port=args.port[0], persistent=args.persistent))
# echo "testing body" | mail -s "Testing with Mail" -r dcl@protonmail.blue -S smtp=127.0.0.1:25 yee@mail.yohoho.localdomain
