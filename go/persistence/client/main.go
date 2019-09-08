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
	concurrentRequests = runtime.NumCPU() - 1
	// concurrentRequests = 5
	iteration = 20000

	serverIPAddress = "127.0.0.1"
	serverPort      = ":8888"

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
			// iteration
			tmp, err := strconv.Atoi(arg)
			if err != nil {
				log.Fatalln(err)
			}
			iteration = tmp
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

func hit(blocking chan bool) {
	log.Println("Start")
	runtime.LockOSThread()

	if isPersistenceMode {
		persistence()
	} else {
		nonPersistence()
	}

	blocking <- true
}

func persistence() {
	// connect to this socket
	conn, err := net.Dial("tcp", serverIPAddress+serverPort)
	if err != nil {
		log.Fatalln(err)
	}
	reader := bufio.NewReader(conn)

	for i := 0; i < iteration; i++ {
		// send to socket
		str := "GET 200\n"
		// n, err := conn.Write([]byte(str))
		_, err = conn.Write([]byte(str))
		if err != nil {
			log.Fatalln(err)
		}
		// log.Println("Write byte", n)

		// listen for reply
		message, err := reader.ReadString('\n')
		if err != nil {
			log.Fatalln(err)
		}
		fmt.Print(message)
	}

	err = conn.Close()
	if err != nil {
		log.Fatalln(err)
	}
}

func nonPersistence() {
	for i := 0; i < iteration; i++ {
		// connect to this socket
		conn, err := net.Dial("tcp", serverIPAddress+serverPort)
		if err != nil {
			log.Fatalln(err)
		}

		str := "GET 200\n"
		// send to socket
		// n, err := conn.Write([]byte(str))
		_, err = conn.Write([]byte(str))
		if err != nil {
			log.Fatalln(err)
		}
		// log.Println("Write byte", n)

		// listen for reply
		message, err := bufio.NewReader(conn).ReadString('\n')
		if err != nil {
			log.Fatalln(err)
		}
		log.Print(message)

		err = conn.Close()
		if err != nil {
			log.Fatalln(err)
		}
	}
}
