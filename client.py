import asyncio
import argparse
import multiprocessing as mp
import time

async def get_response(reader, writer, N=1):
    """Retrieve N responses from the server."""
    rcnt = 0
    while rcnt < N:
        # print(f'rcnt: {rcnt}, N: {N}')
        data = await reader.readline()
        # print(f'Received: {data.decode()!r}')
        rcnt = rcnt + 1

async def tcp_client(message, server=None, port=None, N=1):
    """Send N requests to the server and get the responses asynchronously."""
    tcnt = 0
    reader, writer = await asyncio.open_connection(server, port)

    # create an async task to get all the responses
    non_blocking = asyncio.create_task(get_response(reader, writer, N))

    while tcnt < N:
        # print(f'Send: {message!r}')
        # send requests
        writer.write(message.encode())
        await writer.drain()
        tcnt = tcnt + 1

    # wait for all the responses to be read
    done, pending = await asyncio.wait({non_blocking})
    while non_blocking not in done:
        done, pending = await asyncio.wait({non_blocking})

    # print('Close the connection')
    writer.close()
    await writer.wait_closed()

def async_entry(message, server=None, port=None, N=1):
    """Start async execution in current process"""
    asyncio.run(tcp_client(message, server=server, port=port, N=N))

def main(server='127.0.0.1', port=8888, messages=1, concurrency=None):
    """Calculate the requests needed to be sent in each process, and start the processes. The processes are started with multiprocessing library. The multiprocessing library will sidestep Python's global intepreter lock to achieve true concurrent execution."""

    messages_per_task = messages // concurrency
    messages_per_task = messages_per_task + 1
    decrement = messages % concurrency

    # create 'concurrency' number of processes
    process_queue = []
    for i in range(concurrency):
        if i == decrement:
            messages_per_task = messages_per_task - 1
        # print(f'assigned: {messages_per_task}')
        process_queue.append(mp.Process(target=async_entry, args=('GET foo@bar\n',), kwargs={'server': server, 'port': port, 'N': messages_per_task}))
        process_queue[i].start()


    # wait for all processes to finish
    messages_per_task = messages_per_task + 1
    finished = 0
    for i, p in enumerate(process_queue):
        p.join()
        if i == decrement:
            messages_per_task = messages_per_task - 1
        finished = finished + messages_per_task
        print(f'{finished} requests done.')

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')
parser.add_argument('messages', type=int, default=1, nargs='?', help='total number of messages to send, defaults to 1')
parser.add_argument('concurrency', type=int, default=1, nargs='?', help='number of messages to send at a time, defaults to 1')

args = parser.parse_args()

if __name__ == '__main__':
    start_time = time.time()
    main(server=args.address[0], port=args.port[0], messages=args.messages, concurrency=args.concurrency)
    stop_time = time.time()
    elapsed = stop_time - start_time
    print(f'Time elapsed: {elapsed}s, requests per second: {args.messages / elapsed}')
