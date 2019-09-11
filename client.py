import asyncio
import argparse
import multiprocessing as mp

async def get_response(reader, writer, N=1):
    rcnt = 0
    while rcnt < N:
        print(f'rcnt: {rcnt}, N: {N}')
        data = await reader.readline()
        print(f'Received: {data.decode()!r}')
        rcnt = rcnt + 1

async def tcp_client(message, server=None, port=None, N=1):
    # global tcnt
    tcnt = 0
    reader, writer = await asyncio.open_connection(server, port)
    print(N)
    blocking = asyncio.create_task(get_response(reader, writer, N))

    while tcnt < N:
        print(f'Send: {message!r}')
        writer.write(message.encode())
        await writer.drain()
        tcnt = tcnt + 1
    done, pending = await asyncio.wait({blocking})
    while blocking not in done:
        done, pending = await asyncio.wait({blocking})

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

def async_entry(message, server=None, port=None, N=1):
    asyncio.run(tcp_client(message, server=server, port=port, N=N))

def main(server='127.0.0.1', port=8888, messages=1, concurrency=None):
    messages_per_task = messages // concurrency
    messages_per_task = messages_per_task + 1
    decrement = messages % concurrency

    process_queue = []
    for i in range(concurrency):
        if i == decrement:
            messages_per_task = messages_per_task - 1
        print(f'assigned: {messages_per_task}')
        process_queue.append(mp.Process(target=async_entry, args=('GET foo\n',), kwargs={'server': server, 'port': port, 'N': messages_per_task}))
        process_queue[i].start()

    for p in process_queue:
        p.join()

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')
parser.add_argument('messages', type=int, default=1, nargs='?', help='total number of messages to send')
parser.add_argument('concurrency', type=int, default=1, nargs='?', help='number of messages to send at a time')

args = parser.parse_args()

if __name__ == '__main__':
    main(server=args.address[0], port=args.port[0], messages=args.messages, concurrency=args.concurrency)
