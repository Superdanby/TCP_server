import asyncio
import argparse

tcnt = 0
rcnt = 0

async def statistics():
    cnt = 0
    while True:
        print(f"Sent: {tcnt}\n")
        print(f"Received: {rcnt}\n")
        if cnt is not 0:
            print(f"Received per second: {rcnt / cnt}\n")
        await asyncio.sleep(1)
        cnt = cnt + 1

async def tcp_echo_client(message, server=None, port=None):
    global tcnt, rcnt
    reader, writer = await asyncio.open_connection(
        server, port)

    # print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()
    tcnt = tcnt + 1

    data = await reader.read(100000000000)
    # print(f'Received: {data.decode()!r}')
    rcnt = rcnt + 1

    # print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def main(server='127.0.0.1', port=8888):
    asyncio.create_task(statistics())
    while True:
        await tcp_echo_client('GET foo\n', server=server, port=port)

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')
parser.add_argument('limit', default=[-1], type=int, nargs='?', help='stream reader reads up to n bytes, default has no limit')
args = parser.parse_args()

if __name__ == '__main__':
    asyncio.run(main(server=args.address[0], port=args.port[0]))
