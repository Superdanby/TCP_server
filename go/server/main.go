package main

import (
	"bufio"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"sync/atomic"
	"time"
)

var (
	counter           uint64
	active            int64
	processedRequests int64

	maxConcurrentRequests = 1000
	doSystemCall          = false

	serverIPAddress = "127.0.0.1"
	serverPort      = ":8888"
)

func parseCommandLineArguments() {
	args := os.Args
	for i, arg := range args {
		switch i {
		case 0:
			continue
		case 1:
			// server ip address
			serverIPAddress = arg
		case 2:
			// port
			serverPort = ":" + arg
		case 3:
			// is persistence enabled
			continue
		}
	}
}

func main() {
	parseCommandLineArguments()

	// init
	counter = 0
	active = 0
	processedRequests = 0
	maxConcurrencyLimit := make(chan bool, maxConcurrentRequests)

	http.DefaultTransport.(*http.Transport).MaxIdleConnsPerHost = 100 // connect: can't assign requested address
	// runtime.GOMAXPROCS(1)

	// setup stat thread
	go stat()

	// setup server
	server, err := newServer(serverPort)
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
		// log.Println("Waiting for chan...")
		maxConcurrencyLimit <- true
		// log.Println("Waiting for TCP...")
		conn, err := server.AcceptTCP()
		if err != nil {
			log.Fatalln(err)
		}

		go handler(conn, maxConcurrencyLimit)
	}
}

func stat() {
	for {
		log.Printf("Total connections since start %d, currently active connections %d, total processed requests %d\n", counter, atomic.LoadInt64(&active), atomic.LoadInt64((&processedRequests)))
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

// handle TCP connection
func handler(_conn *net.TCPConn, maxConcurrencyLimit <-chan bool) {
	atomic.AddInt64(&active, 1)
	conn := newConnection(_conn)
	log.Printf("new connection id %d, remote %s, local %s\n", conn.getID(), conn.RemoteAddr(), conn.LocalAddr().String())

	defer func(conn *connection) {
		// id := conn.getID()
		// remoteAddr := conn.RemoteAddr()
		// log.Printf("closing connection %d, %s\n", id, remoteAddr)
		err := conn.Close()
		if err != nil {
			log.Fatalln("closing connection error", err)
		}
		// log.Printf("connection %d, %s closed\n", id, remoteAddr)
		<-maxConcurrencyLimit
		// log.Println("channel freed")
		atomic.AddInt64(&active, -1)
	}(conn)

	err := conn.processConnection()
	if err != nil {
		log.Printf("connection %d, %s has error\n", conn.getID(), err.Error())
	}
}

// handle data IO for a TCP connection
func (c *connection) processConnection() error {
	scanner := bufio.NewScanner(c.TCPConn)
	inp := make(chan string, 100000) // use buffered channel
	done := make(chan bool)
	go requestProcessingQueue(c, inp, done)

	// Read from connection with line split
	// TODO: max idle time?
	for scanner.Scan() {
		buf := scanner.Bytes() // get request
		inp <- string(buf)     // push to work queue
	}
	done <- true // when the connection is closed by client, let the work queue know
	if scanner.Err() != nil {
		log.Fatalln("scanner error", scanner.Err())
	}

	<-done // wait for the work queue to finish

	return nil
}

func apiCall(req string) {

}

// Handle request
func requestProcessingQueue(c *connection, inp <-chan string, done chan bool) {
	for {
		select {
		case req := <-inp: // take requests
			// process request
			atomic.AddInt64(&processedRequests, 1)
			// fmt.Println(req)

			if doSystemCall {
				systemCall()
			} else {
				apiCall(req)
			}

			// send out reply
			// n, err := c.send("200", "foo")
			_, err := c.send200Response("foo")
			if err != nil {
				log.Fatalln("send response error", err)
			}
			// log.Println("Response count", n)

		case <-done: // when inp is empty and done is received, stop the work queue
			goto cleanup
		}
	}

cleanup:
	done <- true
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
