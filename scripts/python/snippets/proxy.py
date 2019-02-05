#!/usr/bin/python3
import sys
import socket
import threading


def request_handler(buff):
    """modify any requests destined for the remote host"""
    return buff


def response_handler(buff):
    """modify any responses destined for the local host"""
    return buff


def hexdump(src, length=16):
    result = []
    digits = 4
    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join(["{:0{d}X}".format(x, d=digits) for x in s])
        text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.' for x in s])
        result.append("{:08X}: {:{wid}}  {}".format(i, hexa, text,
                                                    wid=length*(digits + 1)))
    return '\n'.join(result)


def receive_from(connection):
    buff = b""
    connection.settimeout(10)
    try:
        while True:
            data = connection.recv(4096)
            buff += data
            if not data:
                break
    except Exception:
        pass
    return buff


def proxy_handler(client_socket, remotehost, remoteport, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remotehost, remoteport))
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        print(hexdump(remote_buffer))
        remote_buffer = response_handler(remote_buffer)
        if len(remote_buffer):
            print("[<-] Sending {} bytes to localhost.".format(len(remote_buffer)))
            client_socket.send(remote_buffer)

    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print("[->] Received {} bytes from localhost.".format(len(local_buffer)))
            print(hexdump(local_buffer))
            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[->] Sent to remote.")

        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<-] Received {} bytes from remote.".format(len(remote_buffer)))
            print(hexdump(remote_buffer))
            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<-] Sent to localhost.")

        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


def server_loop(localhost, localport, remotehost, remoteport, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((localhost, localport))
    except Exception as err:
        print("[!] Failed to listen on {}:{}\r\n{}".format(localhost,
                                                           localport, err))
        sys.exit(0)

    server.listen(5)
    print("Listening on {}:{}".format(localhost, localport))

    while True:
        client_socket, addr = server.accept()
        print("[->] Recieved incoming connection from {}:{}".format(addr[0],
                                                                    addr[1]))
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remotehost, remoteport, receive_first)
        )
        proxy_thread.start()


def main():
    if len(sys.argv[1:]) != 5:
        print(("Usage: ./proxy.py [localhost] [localport] "
               "[remotehost] [remoteport] [receive_first]\r\n"
               "Example: ./proxy.py 127.0.0.1 9000 1.2.3.4 9000 True"))
        sys.exit(0)

    assert sys.argv[2].isdigit()
    assert sys.argv[4].isdigit()
    assert sys.argv[5] in "True False"

    localhost = sys.argv[1]
    localport = int(sys.argv[2])
    remotehost = sys.argv[3]
    remoteport = int(sys.argv[4])
    receive_first = bool(sys.argv[5])

    server_loop(localhost, localport, remotehost, remoteport, receive_first)


if __name__ == "__main__":
    main()
