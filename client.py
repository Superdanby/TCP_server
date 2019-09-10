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

async def get_response(reader):
    global rcnt
    while True:
        reader._eof = False
        data = await reader.readline()
        print(f'Received: {data.decode()!r}')
        rcnt = rcnt + 1

async def tcp_echo_client_persistent(message, server=None, port=None):
    global tcnt
    reader, writer = await asyncio.open_connection(server, port)
    asyncio.create_task(get_response(reader))

    while True:
        # print(f'Send: {message!r}')
        writer.write(message.encode())
        await writer.drain()
        tcnt = tcnt + 1

    # print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def main(server='127.0.0.1', port=8888):
    asyncio.create_task(statistics())
    while True:
        await tcp_echo_client_persistent('GET foo\n', server=server, port=port)

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')

args = parser.parse_args()

if __name__ == '__main__':
    asyncio.run(main(server=args.address[0], port=args.port[0]))
