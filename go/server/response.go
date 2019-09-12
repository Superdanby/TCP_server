package main

import (
	"bytes"
	"net"
	"sync/atomic"
)

type connection struct {
	id uint64

	*net.TCPConn // inheritence
}

func newConnection(c *net.TCPConn) *connection {
	return &connection{
		id:      atomic.AddUint64(&counter, 1),
		TCPConn: c,
	}
}

func (c *connection) getID() uint64 {
	return c.id
}

func (c *connection) send200Response(msg string) (int, error) {
	var buf = bytes.NewBufferString("200 " + msg + "\n")

	return c.Write(buf.Bytes())
}

func (c *connection) send400Response(msg string) (int, error) {
	var buf = bytes.NewBufferString("400 " + msg + "\n")

	return c.Write(buf.Bytes())
}

func (c *connection) send500Response(msg string) (int, error) {
	var buf = bytes.NewBufferString("500 " + msg + "\n")

	return c.Write(buf.Bytes())
}
