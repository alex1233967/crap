#!/usr/bin/python
import ssl
import thread
from socket import *
from datetime import datetime


def logger(string, lock=thread.allocate_lock()):
    with lock:
        with open(LOGFILE, 'a') as f:
            f.write(string)


def handler(clientsock, addr):
    clientsock.settimeout(3)
    try:
        while 1:
            data = clientsock.recv(BUFF)
            if not data:
                break
            time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            string = "{0} {1}\n{2}\n".format(str(addr[0]), time, str(data))
            logger(string, LOGFILE)
            clientsock.close()
    except:
        clientsock.close()


if __name__ == '__main__':
    BUFF = 1024
    HOST = '0.0.0.0'
    PORT = 13371
    LOGFILE = '/tmp/log.txt'
    KEYFILE = './server.key'
    CERTFILE = './server.crt'
    ADDR = (HOST, PORT)

    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(5)

    serversock_ssl = ssl.wrap_socket(serversock,
                                     keyfile=KEYFILE,
                                     certfile=CERTFILE,
                                     server_side=True)

    serversock_ssl.ciphers = ['TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA']

    print('waiting for connections...')
    while 1:
        try:
            clientsock, addr = serversock_ssl.accept()
            print('...connected from: ' + str(addr[0]))
            thread.start_new_thread(handler, (clientsock, addr))
        except KeyboardInterrupt:
            print("\nshutting down...")
            break
        except:
            continue
