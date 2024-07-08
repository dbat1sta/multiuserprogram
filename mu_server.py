import socket
import os
import signal
import selectors
import time

sel = selectors.DefaultSelector()
clients = {}

def cleanup_server(sock, socket_file):
    print("Cleaning up the server...")
    sel.close()
    sock.close()
    if os.path.exists(socket_file):
        os.unlink(socket_file)

def signal_handler(sig, frame, server_sock, socket_file):
    cleanup_server(server_sock, socket_file)
    print("Server terminated.")
    exit(0)

def accept(sock):
    conn, addr = sock.accept() 
    print(f"New client {conn.fileno()}")
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)
    conn.sendall(b"HELLO")

def read(conn):
    data = conn.recv(1024)
    if data:
        msg = data.decode().strip()
        if msg == "quit":
            print(f"Client {conn.fileno()} quit, see ya.")
            sel.unregister(conn)
            conn.close()
        else:
            print(f"Client {conn.fileno()} says '{msg}'")
            conn.sendall(b"ENTERCMD")
    else:
        print(f"Client {conn.fileno()} disconnected.")
        sel.unregister(conn)
        conn.close()

def main(socket_file):
    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_sock.bind(socket_file)
    server_sock.listen()
    server_sock.setblocking(False)
    sel.register(server_sock, selectors.EVENT_READ, accept)

    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, server_sock, socket_file))

    print("Server started, waiting for connections...")

    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
            if not events:
                time.sleep(0.001)  
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup_server(server_sock, socket_file)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 mu_server.py <socket_file>")
        sys.exit(1)
    socket_file = sys.argv[1]
    main(socket_file)
