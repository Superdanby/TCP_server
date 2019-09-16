import asyncio
import argparse
import sys
import queue
import heapq

async def proton_api(message, cmd='printf') -> str:
    """Dummy Proton API, returns 200 permit, 200 reject, 400 REASON, or 500 REASON, possible set timeout"""
    # Check out the ENCODING section of www.postfix.org/tcp_table.5.html
    return "200 permit\n"
    # return "200 reject\n"
    # return "500 permit\n"
    # return "400 permit\n"

    # check string format, messages from postfix probably don't need this
    # if message[0:4] != 'GET ' and len(message) != 4:
    #     return '500 Wrong format: ' + message + '\n'

    # open tcp connection to localhost:443
    reader, writer = await asyncio.open_connection('localhost', 443, ssl=True)

    # compose and send HTTP GET query
    query = (
        f"GET {'localhost/mail/incoming/rcpt?Email=' + message[4:]} HTTP/1.1\n"
        f"\n"
    )
    writer.write(query.encode('utf-8'))

    # get status code
    line = await reader.readline()
    status_code = line.decode('utf-8').split(' ')[1]

    if status_code[0] == '2':
        return "200 permit\n"

    Error = ''
    # get Error field
    while True:
        line = await reader.readline()
        if not line:
            break
        response = line.decode('utf-8').rstrip()
        if not response:
            break
        if response[0:7] == 'Error: ':
            Error = response[7:]
        # print(f'HTTP header> {line}')

    # reject user
    if status_code == '422':
        return "200 reject\n"
    # temporary rejects
    return "400 " + Error + "\n"

async def respond(writer, message, response_queue, receive_cnt, transmit_control):
    """Wait for the results from proton_api and send it to the client, this function maintains a min-heap to ensure the outgoing order is the same as the incoming order"""
    # wait for response from Proton API
    response = await proton_api(message)

    # insert an element: [incoming order, encoded response]
    heapq.heappush(response_queue, [receive_cnt, response.encode()])
    transmit_control[0] = transmit_control[0] + 1

    # If response_queue is not empty and the element on top of min-heap has the smallest receive_cnt of all elements not yet sent, send the element. Repeat this step until the condition is not met.
    while transmit_control[0] != 0 and response_queue[0][0] == transmit_control[1]:
        _, leaving = heapq.heappop(response_queue)
        transmit_control[1] = transmit_control[1] + 1
        transmit_control[0] = transmit_control[0] - 1
        writer.write(leaving)
        await writer.drain()

async def handle_query(reader, writer):
    """This function reads request data from the client after a connection is established. After reading one request, it will initiate the respond() function to process the request and send it back, but instead of waiting respond() to finish its task, this function will continue to read the next request immediately."""
    response_queue = []
    transmit_control = [0, 0] # size of response_queue, transmit count
    receive_cnt = 0
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
        asyncio.create_task(respond(writer, message, response_queue, receive_cnt, transmit_control))
        receive_cnt = receive_cnt + 1

    print("Close the connection")
    writer.close()

async def main(address='127.0.0.1', port=8888):
    server = await asyncio.start_server(handle_query, address, port)

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
