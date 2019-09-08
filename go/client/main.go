package main

import (
	"bufio"
	"log"
	"net"
	"net/http"
	"runtime"
)

var (
	// concurrentRequests = runtime.NumCPU()
	concurrentRequests = 10
	iteration          = 500
	addr               = "127.0.0.1:8888"
)

func main() {
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

	for i := 0; i < iteration; i++ {
		// connect to this socket
		conn, err := net.Dial("tcp", addr)
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

	// for i := 0; i < 5000; i++ {
	// 	str := "GET 200\n"
	// 	reader := strings.NewReader(str)
	// 	// resp, err := http.Get("http://127.0.0.1:8888")
	// 	// http.Post("http://127.0.0.1:8888", "text/plain", reader)
	// 	resp, err := http.Post("http://127.0.0.1:8888", "text/plain", reader)
	// 	if err != nil {
	// 		log.Fatalln(err)
	// 	}
	// 	defer resp.Body.Close()
	// 	// log.Println("Response status:", resp.Status)

	// 	scanner := bufio.NewScanner(resp.Body)
	// 	for i := 0; scanner.Scan() && i < 5; i++ {
	// 		log.Println(scanner.Text())
	// 	}

	// 	if err := scanner.Err(); err != nil {
	// 		log.Fatalln(err)
	// 	}
	// }

	blocking <- true
}
