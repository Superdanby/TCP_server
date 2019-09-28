import asyncio
import argparse
import multiprocessing as mp
import time
import random

async def get_response(reader, writer, N=1):
    """Retrieve N responses from the server."""
    rcnt = 0
    ret = []
    while rcnt < N:
        print(f'rcnt: {rcnt}, N: {N}')
        data = await reader.readline()
        ret.append(data)
        while data == b'':
            print(f'Received empty raw: {data}')
            data = await reader.readline()
        print(f'Received raw: {data}')
        # print(f'Received: {data.decode()!r}')
        rcnt = rcnt + 1
    return ret

async def tcp_client(message=None, server=None, port=None, N=1, validate=False, return_response=False):
    """Send N requests to the server and get the responses asynchronously."""
    rangen = False
    if message is None or validate:
        rangen = True
    tcnt = 0
    reader, writer = await asyncio.open_connection(server, port)

    queries = ['GET bart@protonmail.dev\n', 'GET foo@bar\n']
    replies = ['200 permit\n'.encode(), '200 reject\n'.encode()]
    answers = []

    # create an async task to get all the responses
    non_blocking = asyncio.create_task(get_response(reader, writer, N))

    while tcnt < N:
        # print(f'Send: {message!r}')
        # send requests
        if rangen:
            ranidx = random.randint(0, 1)
            message = queries[ranidx]
            answers.append(replies[ranidx])
            # if tcnt % 60 == 59:
            #     message = 'GET bad request\n'
        print(f"{tcnt}: {message.encode()}")
        writer.write(message.encode())
        await writer.drain()
        tcnt = tcnt + 1

    # wait for all the responses to be read
    done, pending = await asyncio.wait([non_blocking])
    while len(pending) != 0:
        done, pending = await asyncio.wait(pending)

    if return_response:
        done = done.pop()
        answers = [x.decode() for x in done.result()]

    if validate:
        done = done.pop()
        done = done.result()
        assert(answers == done)
        print("All replies are correct!")

    if writer.can_write_eof():
        writer.write_eof()
        # await writer.drain()
        print("eof sent")
    print("finish writing")

    received_all = time.time()
    print("wait for server to clean up")
    while writer.can_write_eof() and not reader.at_eof():
        await reader.read()

    # print('Close the connection')
    # await asyncio.sleep(1)
    writer.close()
    await writer.wait_closed()
    if return_response:
        return answers
    return received_all

def async_entry(message=None, server=None, port=None, N=1, queue=None, validate=False):
    """Start async execution in current process"""
    if queue:
        queue.put(asyncio.run(tcp_client(message, server=server, port=port, N=N, validate=validate)))
    else:
        asyncio.run(tcp_client(message, server=server, port=port, N=N, validate=validate))

def main(server='127.0.0.1', port=8888, messages=1, concurrency=None, validate=False):
    """Calculate the requests needed to be sent in each process, and start the processes. The processes are started with multiprocessing library. The multiprocessing library will sidestep Python's global intepreter lock to achieve true concurrent execution."""

    messages_per_task = messages // concurrency
    messages_per_task = messages_per_task + 1
    decrement = messages % concurrency
    random.seed()

    finish_times = mp.Queue()

    # create 'concurrency' number of processes
    process_queue = []
    for i in range(concurrency):
        if i == decrement:
            messages_per_task = messages_per_task - 1
        # print(f'assigned: {messages_per_task}')

        process_queue.append(mp.Process(target=async_entry, kwargs={'server': server, 'port': port, 'N': messages_per_task, 'queue': finish_times, 'validate': validate}))
        process_queue[i].start()


    # wait for all processes to finish
    messages_per_task = messages_per_task + 1
    finished = 0
    for i, p in enumerate(process_queue):
        received_all = finish_times.get()
        p.join()
        if i == decrement:
            messages_per_task = messages_per_task - 1
        finished = finished + messages_per_task
        print(f'{finished} requests done.')
    return received_all

# get server address and port
parser = argparse.ArgumentParser(description='Specify server address and port')
parser.add_argument('address', type=str, nargs=1, help='server address')
parser.add_argument('port', type=int, nargs=1, help='server port')
parser.add_argument('messages', type=int, default=1, nargs='?', help='total number of messages to send, defaults to 1')
parser.add_argument('concurrency', type=int, default=1, nargs='?', help='number of messages to send at a time, defaults to 1')
parser.add_argument('--validate', action='store_true', help='validate the responses from server, will affect performance metrics')


if __name__ == '__main__':
    args = parser.parse_args()
    start_time = time.time()
    received_all = main(server=args.address[0], port=args.port[0], messages=args.messages, concurrency=args.concurrency, validate=args.validate)
    stop_time = time.time()
    print(f'Process time: {received_all - start_time}s, requests per second: {args.messages / (received_all - start_time)}, server clean up time: {stop_time - received_all}s, total time elapsed: {stop_time - start_time}s')
