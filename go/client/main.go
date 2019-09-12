package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
)

var (
	serverIPAddress    = "127.0.0.1"
	serverPort         = ":8888"
	totalMessages      = 1
	concurrentRequests = 1
	// concurrentRequests = runtime.NumCPU() - 1

	isPersistenceMode = true
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
			// total number of messages
			tmp, err := strconv.Atoi(arg)
			if err != nil {
				log.Fatalln(err)
			}
			totalMessages = tmp
		case 4:
			tmp, err := strconv.Atoi(arg)
			if err != nil {
				log.Fatalln(err)
			}
			concurrentRequests = tmp
		}
	}

}

func main() {
	parseCommandLineArguments()

	// runtime.GOMAXPROCS(1)
	http.DefaultTransport.(*http.Transport).MaxIdleConnsPerHost = 100 // connect: can't assign requested address

	blocking := make(chan bool)
	for i := 0; i < concurrentRequests; i++ {
		go hit(blocking)
	}

	for i := 0; i < concurrentRequests; i++ {
		<-blocking
		log.Println("Done")
	}
}

// start making requests to server
func hit(blocking chan<- bool) {
	log.Println("Start")
	runtime.LockOSThread()

	if isPersistenceMode {
		persistenceRequestTask(totalMessages / concurrentRequests)
	} else {
		nonPersistence()
	}

	blocking <- true
}

// use persistent connection
func persistenceRequestTask(messagesCount int) {
	// connect to this socket
	conn, err := net.Dial("tcp", serverIPAddress+serverPort)
	if err != nil {
		log.Fatalln(err)
	}

	reader := bufio.NewReader(conn)
	done := make(chan bool)
	// async, read response
	receiveResponse := func(done chan<- bool, reader *bufio.Reader) {
		for i := 0; i < messagesCount; i++ {
			// listen for reply
			message, err := reader.ReadString('\n')
			if err != nil {
				log.Fatalln(err)
			}
			fmt.Print(message)
		}
		done <- true
	}
	go receiveResponse(done, reader)

	for i := 0; i < messagesCount; i++ {
		str := sendRequest("key") // make requests
		// send to socket
		// n, err := conn.Write([]byte(str))
		_, err = conn.Write([]byte(str))
		if err != nil {
			log.Fatalln(err)
		}
		// log.Println("Write byte", n)
	}

	<-done // wait for the response reading task to finish

	err = conn.Close()
	if err != nil {
		log.Fatalln(err)
	}
}

func nonPersistence() {
	// 	for i := 0; i < totalMessages; i++ {
	// 		// connect to this socket
	// 		conn, err := net.Dial("tcp", serverIPAddress+serverPort)
	// 		if err != nil {
	// 			log.Fatalln(err)
	// 		}

	// 		str := sendRequest("key")
	// 		// send to socket
	// 		// n, err := conn.Write([]byte(str))
	// 		_, err = conn.Write([]byte(str))
	// 		if err != nil {
	// 			log.Fatalln(err)
	// 		}
	// 		// log.Println("Write byte", n)

	// 		// listen for reply
	// 		message, err := bufio.NewReader(conn).ReadString('\n')
	// 		if err != nil {
	// 			log.Fatalln(err)
	// 		}
	// 		log.Print(message)

	// 		err = conn.Close()
	// 		if err != nil {
	// 			log.Fatalln(err)
	// 		}
	// 	}
}
