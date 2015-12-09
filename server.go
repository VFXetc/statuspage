package main

import (
    "fmt"
    "log"
    "net"
    "net/http"
)


type Message struct {

    IP      net.IP
    Content []byte

}


type Broker struct {

    // Events are pushed to this channel by the main events-gathering routine
    Notifier chan Message

    // New client connections
    newClients chan chan Message

    // Closed client connections
    closingClients chan chan Message

    // Client connections registry
    clients map[chan Message]bool
}

func NewServer() (broker *Broker) {
    // Instantiate a broker
    broker = &Broker{
        Notifier:       make(chan Message, 1),
        newClients:     make(chan chan Message),
        closingClients: make(chan chan Message),
        clients:        make(map[chan Message]bool),
    }

    // Set it running - listening and broadcasting events
    go broker.listen()

    return
}

func (broker *Broker) ServeHTTP(rw http.ResponseWriter, req *http.Request) {

    // Make sure that the writer supports flushing.
    //
    flusher, ok := rw.(http.Flusher)

    if !ok {
        http.Error(rw, "Streaming unsupported!", http.StatusInternalServerError)
        return
    }

    rw.Header().Set("Content-Type", "text/event-stream")
    rw.Header().Set("Cache-Control", "no-cache")
    rw.Header().Set("Connection", "keep-alive")
    rw.Header().Set("Access-Control-Allow-Origin", "*")

    // Each connection registers its own message channel with the Broker's connections registry
    messageChan := make(chan Message)

    // Signal the broker that we have a new connection
    broker.newClients <- messageChan

    // Remove this client from the map of connected clients
    // when this handler exits.
    defer func() {
        broker.closingClients <- messageChan
    }()

    // Listen to connection close and un-register messageChan
    notify := rw.(http.CloseNotifier).CloseNotify()

    go func() {
        <-notify
        broker.closingClients <- messageChan
    }()

    for {

        // Write to the ResponseWriter
        // Server Sent Events compatible
        msg := <-messageChan
        fmt.Fprintf(rw, "data: %s %s\n\n", msg.IP, msg.Content)

        // Flush the data immediatly instead of buffering it for later.
        flusher.Flush()
    }

}

func (broker *Broker) listen() {
    for {
        select {
        case s := <-broker.newClients:

            // A new client has connected.
            // Register their message channel
            broker.clients[s] = true
            log.Printf("Client added. %d registered clients", len(broker.clients))
        case s := <-broker.closingClients:

            // A client has dettached and we want to
            // stop sending them messages.
            delete(broker.clients, s)
            log.Printf("Removed client. %d registered clients", len(broker.clients))
        case event := <-broker.Notifier:

            // We got a new event from the outside!
            // Send event to all connected clients
            for clientMessageChan, _ := range broker.clients {
                clientMessageChan <- event
            }
        }
    }

}

func main() {

    static := http.FileServer(http.Dir("static"))
    http.Handle("/", static)

    broker := NewServer()
    http.Handle("/events", broker)

    go func() {

        addr := net.UDPAddr{
            Port: 12345,
            IP: net.ParseIP("0.0.0.0"),
        }
        conn, err := net.ListenUDP("udp", &addr)
        if err != nil {
            log.Fatal("FATAL ERROR while opening UDP socket:", err)
        }
        defer conn.Close()

        buf := make([]byte, 8192)
        for {
            n, addr, err := conn.ReadFromUDP(buf)
            if err != nil {
                log.Println("ERROR while reading UDP socket:", err)
                continue
            }
            msg := Message{addr.IP, buf[0:n]}
            broker.Notifier <- msg
        }

    }()

    log.Println("Starting server...")

    err := http.ListenAndServe("0.0.0.0:8100", nil)
    log.Fatal("FATAL ERROR while serving HTTP:", err)

}
