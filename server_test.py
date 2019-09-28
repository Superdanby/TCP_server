import asyncio
import server
import client
import functools
import server_aiohttp
import unittest
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class TestServer(unittest.TestCase):
    address = '127.0.0.1'
    port_0 = 5555
    port_1 = 5556
    connection_limit = 1
    permit_req = 'GET bart@protonmail.dev\n'
    reject_req = 'GET yeee@yee\n'
    bad_request = 'GET bad request\n'

    def test_permit(self):
        self.assertEqual(asyncio.run(client.tcp_client(message=self.permit_req, server=self.address, port=self.port_0, return_response=True)), ['200 permit\n'])
        self.assertEqual(asyncio.run(client.tcp_client(message=self.permit_req, server=self.address, port=self.port_1, return_response=True)), ['200 permit\n'])

    def test_reject(self):
        resp_0 = asyncio.run(client.tcp_client(message=self.reject_req, server=self.address, port=self.port_0, return_response=True))[0]
        self.assertEqual(resp_0[:10], '200 reject')
        self.assertEqual(resp_0[-1], '\n')
        resp_1 = asyncio.run(client.tcp_client(message=self.reject_req, server=self.address, port=self.port_1, return_response=True))[0]
        self.assertEqual(resp_1[:10], '200 reject')
        self.assertEqual(resp_1[-1], '\n')

    def test_bad_request(self):
        self.assertEqual(asyncio.run(client.tcp_client(message=self.bad_request, server=self.address, port=self.port_0, return_response=True)), ['400 bad request\n'])
        self.assertEqual(asyncio.run(client.tcp_client(message=self.bad_request, server=self.address, port=self.port_1, return_response=True)), ['400 bad request\n'])

if __name__ == '__main__':
    unittest.main()
