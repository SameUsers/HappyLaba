class TCPError(Exception):
    pass


class SessionRemoteClose(TCPError):
    pass


class InvalidPeerInfo(TCPError):
    pass
