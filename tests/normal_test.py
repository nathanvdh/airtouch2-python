import socket
import errno
from airtouch2.protocol.messages import RequestState, ChangeSetTemperature
from airtouch2.protocol.constants import MessageLength

SocketClosedErrors = (errno.ECONNABORTED,  errno.ECONNRESET,
                      errno.ENOTCONN, errno.ESHUTDOWN, errno.ECONNREFUSED)


def get_response(sock: socket.socket) -> bytes:
    # taken (almost) straight from https://docs.python.org/3/howto/sockets.html
    chunks = []
    bytes_recd = 0
    while bytes_recd < MessageLength.RESPONSE:
        try:
            chunk = sock.recv(MessageLength.RESPONSE - bytes_recd)
        except OSError as e:
            if e.errno not in SocketClosedErrors:
                raise e
            chunk = b''
        if chunk == b'':
            # socket broken or closed
            break
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
    return b''.join(chunks)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(None)
    sock.connect(("192.168.1.21", 8899))
    data=RequestState().serialize()
    print(data)
    sock.sendall(data)

    resp = get_response(sock)
    print(resp)
    data=ChangeSetTemperature(0, True).serialize()
    print(data)
    sock.sendall(data)

    resp = get_response(sock)
    print(resp)


main()
