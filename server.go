package main

import (
    "bufio"
    "container/heap"
    "fmt"
    "io"
    "net"
    "sync"
)

// An Item is something we manage in a priority queue.
type Item struct {
	value * string // The value of the item; arbitrary.
	priority int64    // The priority of the item in the queue.
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
    // fmt.Printf("%+v\t", item)
	return item
}

func respond(client_req *string, writer *bufio.Writer, response_queue *PriorityQueue, receive_cnt int64, transmit_cnt *int64, lock *sync.Mutex) {
    // reset connection if receive_cnt is near the limit
    lock.Lock()
    heap.Push(response_queue, & Item{client_req, receive_cnt})
    for _, x := range *response_queue {
        fmt.Printf("%+v\t", x)
    }
    fmt.Println(*transmit_cnt)
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
}

func handleConnection(conn net.Conn) {
    defer conn.Close()
    reader := bufio.NewReader(conn)
    writer := bufio.NewWriter(conn)
    var response_queue PriorityQueue
    var receive_cnt, transmit_cnt int64
    var lock sync.Mutex
    for {
        client_req, err := reader.ReadString('\n')
        if err == io.EOF {
            fmt.Println("Reader EOF reached")
            return
        } else if err != nil {
            panic("Holy hell")
        }

        go respond(&client_req, writer, &response_queue, receive_cnt, &transmit_cnt, &lock)
        receive_cnt += 1
        fmt.Printf(client_req)
    }
}

func main() {
    ln, err := net.Listen("tcp", "127.0.0.1:8888")
    if err != nil {
    	panic("Holy hell")
    }
    for {
    	conn, err := ln.Accept()
        if err != nil {
        	panic("Holy hell")
        }
    	go handleConnection(conn)
    }
}
