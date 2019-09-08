package main

import (
	"bufio"
	"bytes"
	"log"
	"net"
	"net/http"
	"os/exec"
	"sync/atomic"
	"time"
)

var (
	counter uint64
	active  int64
)

const (
	maxConcurrentRequests = 1
	doSystemCall          = true
)

func main() {
	// init
	counter = 0
	active = 0
	maxConcurrencyLimit := make(chan bool, maxConcurrentRequests)

	http.DefaultTransport.(*http.Transport).MaxIdleConnsPerHost = 100 // connect: can't assign requested address
	// runtime.GOMAXPROCS(1)

	// setup stat thread
	go stat()

	// setup server
	server, err := newServer(":8888")
	if err != nil {
		log.Fatalln(err)
	}
	defer func() {
		// TODO: gracefully stop the server

		err := server.Close()
		if err != nil {
			log.Fatalln(err)
		}
		log.Println("Server stops")
	}()

	// start taking connections
	log.Println("Server starts")
	for {
		log.Println("Waiting for chan...")
		maxConcurrencyLimit <- true
		log.Println("Waiting for TCP...")
		conn, err := server.AcceptTCP()
		if err != nil {
			log.Fatalln(err)
		}

		go handler(conn, maxConcurrencyLimit)
	}
}

func stat() {
	for {
		log.Printf("Request received %d, active %d\n", counter, atomic.LoadInt64(&active))
		time.Sleep(1 * time.Second)
	}
}

func newServer(address string) (server *net.TCPListener, err error) {
	addr, err := net.ResolveTCPAddr("tcp", address)
	if err != nil {
		return nil, err
	}

	tcpListener, err := net.ListenTCP("tcp", addr)
	if err != nil {
		return nil, err
	}

	return tcpListener, nil
}

func systemCall() {
	log.Println("system call")
	// binary, err := exec.LookPath("ls")
	// if err != nil {
	// 	log.Fatalln(err)
	// }
	// log.Println(binary)
	// args := []string{"-a", "-l", "-h"}
	// env := os.Environ()
	// err = syscall.Exec(binary, args, env)
	// if err != nil {
	// 	log.Fatalln(err)
	// }

	args := []string{"-a", "-l", "-h"}
	cmd := exec.Command("ls", args...)
	err := cmd.Start()
	if err != nil {
		log.Fatalln(err)
	}
	err = cmd.Wait()
	if err != nil {
		log.Fatalln(err)
	}
}

func handler(_conn *net.TCPConn, maxConcurrencyLimit <-chan bool) {
	atomic.AddInt64(&active, 1)
	conn := newConnection(_conn)
	log.Printf("new connection id %d, remote %s, local %s\n", conn.getID(), conn.RemoteAddr(), conn.LocalAddr().String())

	defer func(conn *connection) {
		id := conn.getID()
		remoteAddr := conn.RemoteAddr()
		log.Printf("closing connection %d, %s\n", id, remoteAddr)
		err := conn.Close()
		if err != nil {
			log.Fatalln("closing connection error", err)
		}
		log.Printf("connection %d, %s closed\n", id, remoteAddr)
		log.Println("channel freed", <-maxConcurrencyLimit)
		atomic.AddInt64(&active, -1)
	}(conn)

	err := conn.decodeConnection()
	if err != nil {
		log.Printf("connection %d, %s has error\n", conn.getID(), err.Error())
	}
}

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

func (c *connection) send(code, msg string) (int, error) {
	var buf = bytes.NewBufferString(code + " " + msg + "\n")

	return c.Write(buf.Bytes())
}

func (c *connection) decodeConnection() error {
	scanner := bufio.NewScanner(c.TCPConn)

	// Read from connection with line split
	for scanner.Scan() {
		buf := scanner.Bytes()
		log.Printf("decoded = %s", string(buf))

		if doSystemCall {
			systemCall()
		}

		// send out reply
		// n, err := c.send("200", "foo")
		_, err := c.send("200", "foo")
		if err != nil {
			log.Fatalln("send response error", err)
		}
		// log.Println("Response count", n)
	}
	if scanner.Err() != nil {
		log.Fatalln("scanner error", scanner.Err())
	}

	return nil
}
