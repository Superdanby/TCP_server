package main

import (
    "bufio"
    "container/heap"
    "crypto/tls"
    "fmt"
    "io"
    "io/ioutil"
    "encoding/json"
    "net"
    "net/http"
    "sync"
    "time"
)

// An Item is something we manage in a priority queue.
type Item struct {
	value * string // The value of the item; arbitrary.
	priority int64    // The priority of the item in the queue.
}

type APIError struct {
    Error string `json:"Error"`
}

// A PriorityQueue implements heap.Interface and holds Items.
type PriorityQueue [] * Item

func (pq PriorityQueue) Len() int { return len(pq) }

func (pq PriorityQueue) Less(i, j int) bool {
	// We want Pop to give us the highest, not lowest, priority so we use greater than here.
	return pq[i].priority < pq[j].priority
}

func (pq PriorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
}

func (pq *PriorityQueue) Push(x interface{}) {
	item := x.(*Item)
	*pq = append(*pq, item)
}

func (pq *PriorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	old[n-1] = nil  // avoid memory leak
	*pq = old[0 : n-1]
	return item
}

func respond(client_req *string, writer *bufio.Writer, api_client *(http.Client), response_queue *PriorityQueue, receive_cnt int64, transmit_cnt *int64, lock *sync.Mutex, client_semaphore chan int64) {
    // reset connection if receive_cnt is near the limit

    response := "500 SMTPD Policy Server Error, passing down the request."
    retry := 100
    for retry > 0 {
        retry -= 1
        retry += 1 // retry forever
        req := "https://localhost/api/mail/incoming/recipient?Email=" + (*client_req)[4:(len(*client_req) - 1)]
        fmt.Println(req)
        resp, err := api_client.Get(req)
        if err != nil {
            fmt.Println(err)
            if retry == 0 {
                panic("API Connection failure!")
            }
            fmt.Printf("API Connection failure! Retries left: %d\n", retry)
            time.Sleep(time.Second)
            continue
        }
        defer resp.Body.Close()
        var api_error APIError

        print(resp.StatusCode)
        if resp.StatusCode == 200 || resp.StatusCode == 204 {
            response = "200 permit\n"
        } else if resp.StatusCode == 422 {
            err = json.NewDecoder(resp.Body).Decode(&api_error)
            if err != nil {
                panic("Decode Error field failed!")
            }
            response = "200 reject " + api_error.Error + "\n"
        } else if resp.StatusCode == 400 {
            response = "400 bad request\n"
        } else {
            err = json.NewDecoder(resp.Body).Decode(&api_error)
            if err != nil {
                fmt.Println("Decode Error field failed!")
                response = "400 " + resp.Status + "\n"
            } else {
                response = "400 " + api_error.Error + "\n"
            }
        }
        io.Copy(ioutil.Discard, resp.Body)
        retry = 0
    }
    lock.Lock()
    heap.Push(response_queue, & Item{&response, receive_cnt})
    // for _, x := range *response_queue {
    //     fmt.Printf("%+v\t", x)
    // }
    // fmt.Println(*transmit_cnt)
    for len(*response_queue) > 0 && *transmit_cnt == (*response_queue)[0].priority {
        leaving := heap.Pop(response_queue).(*Item)
        _, err := writer.WriteString(*(leaving.value))
        if err != nil {
            panic("Write failed!")
        }
        writer.Flush()
        *transmit_cnt += 1
    }
    lock.Unlock()
    client_semaphore <- *transmit_cnt
}

func handleConnection(conn net.Conn, api_client *http.Client, client_semaphore chan int64) {
    defer conn.Close()
    reader := bufio.NewReader(conn)
    writer := bufio.NewWriter(conn)
    defer writer.Flush()
    var response_queue PriorityQueue
    var receive_cnt, transmit_cnt int64
    var lock sync.Mutex
    for {
        <- client_semaphore
        client_req, err := reader.ReadString('\n')
        if err == io.EOF {
            fmt.Println("Reader EOF reached")
            return
        } else if err != nil {
            panic("Holy hell")
        }

        go respond(&client_req, writer, api_client, &response_queue, receive_cnt, &transmit_cnt, &lock, client_semaphore)
        receive_cnt += 1
        fmt.Printf(client_req)
    }
}

func main() {
    ln, err := net.Listen("tcp", "127.0.0.1:8888")
    if err != nil {
    	panic("Holy hell")
    }
    tr := &http.Transport{
        MaxIdleConns: 10,
    	MaxIdleConnsPerHost: 10,
        MaxConnsPerHost: 10,
    	IdleConnTimeout: 300 * time.Second,
    	// DisableCompression: true,
        TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
        // add read timeout
    }
    api_client := &http.Client{Transport: tr}
    client_semaphore := make (chan int64, 100)
    for i := 0; i < 100; i++ {
        client_semaphore <- 0
    }
    for {
    	conn, err := ln.Accept()
        if err != nil {
        	panic("Holy hell")
        }
    	go handleConnection(conn, api_client, client_semaphore)
    }
}
