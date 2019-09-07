import asyncio
import argparse

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

async def main(address='127.0.0.1', port=8888):
    server = await asyncio.start_server(
        handle_query, address, port)


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
