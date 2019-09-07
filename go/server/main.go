package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	http.DefaultTransport.(*http.Transport).MaxIdleConnsPerHost = 100 // connect: can't assign requested address
	// runtime.GOMAXPROCS(1)

	http.HandleFunc("/", requestHandler)

	log.Println("Ready to start")
	log.Println(http.ListenAndServe(":8888", nil))
}

func requestHandler(w http.ResponseWriter, r *http.Request) {
	// log.Println("Start")
	fmt.Fprintf(w, "200 foo\n")
	// defer log.Println("Done")
}
