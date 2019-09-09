import asyncio
import argparse
import sys
import queue

cnt = 0
period = 10
q = queue.Queue(maxsize=period)
qsize = 0
period_cnt = 0

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
    proc = await asyncio.create_subprocess_shell(
        cmd + ' "200 foo\n"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    return stdout

async def handle_query(reader, writer):
    global cnt
    data = await reader.read(100000000000)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    cmprs = writer.get_extra_info('compression')

    # print(f"Received {message!r} from {addr!r}")
    print(f"Received {message!r} from {addr!r}, compression: {cmprs}")

    # wait for response from Proton API
    response = await proton_api(message)
    # response = "yee".encode()

    writer.write(response)
    await writer.drain()

    print("Close the connection")
    writer.close()
    cnt = cnt + 1

async def handle_query_persistent(reader, writer):
    global cnt
    while True:
        data = await reader.read(100000000000)
        message = data.decode()
        if message == "close":
            break
        addr = writer.get_extra_info('peername')
        cmprs = writer.get_extra_info('compression')

        # print(f"Received {message!r} from {addr!r}")
        print(f"Received {message!r} from {addr!r}, compression: {cmprs}")

        # wait for response from Proton API
        response = await proton_api(message)
        # response = "yee".encode()

        writer.write(response)
        await writer.drain()
        cnt = cnt + 1

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
