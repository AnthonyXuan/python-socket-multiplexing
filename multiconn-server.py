import sys
import socket
import selectors
import types

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events=events, data=data)
    
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

if __name__ == '__main__':
    sel = selectors.DefaultSelector()

    host, port = sys.argv[1], int(sys.argv[2])
    # this socket is used for listening for new connections
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind this socket to the host and port 
    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {(host, port)}")
    # non-blocking
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    try:
        while True:
            # ! 'key' is the namedtuple returned from .select() that contains the socket object(key.fileobj) and the data object(key.data)
            events = sel.select(timeout=None)
            for key, mask in events:
                # lsock differs the conn socks that it don't have data registered in selector
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()