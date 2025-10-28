# central_server.py
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet.defer import Deferred
import struct

# Define backend server addresses
AS_SERVER = ("localhost", 9001)
GATAN_SERVER = ("localhost", 9002)


class BackendClient(Int32StringReceiver):
    """Handles communication with a backend server (AS, Gatan, CEOS, etc)."""

    def __init__(self, finished: Deferred):
        self.finished = finished
        self.buffer = b""

    def connectionMade(self):
        pass

    def sendCommand(self, cmd: str):
        self.transport.write(cmd.encode())

    def dataReceived(self, data):
        self.buffer += data
        # Wait until full payload received
        if len(self.buffer) >= 4:
            length = struct.unpack("!I", self.buffer[:4])[0]
            if len(self.buffer) - 4 >= length:
                payload = self.buffer[4:4 + length]
                self.finished.callback(payload)
                self.transport.loseConnection()

    def connectionLost(self, reason):
        if not self.finished.called:
            self.finished.errback(reason)


class CentralProtocol(Protocol):
    """Main entrypoint for client connections (e.g., Jupyter client)."""

    def dataReceived(self, data):
        msg = data.decode().strip()
        print(f"[Central] Received: {msg}")

        if msg.startswith("AS"):
            target_host, target_port = AS_SERVER
            backend_cmd = msg[len("AS_"):]
        elif msg.startswith("Gatan"):
            target_host, target_port = GATAN_SERVER
            backend_cmd = msg[len("Gatan_"):]
        else:
            self.transport.write(b"error unknown command")
            self.transport.loseConnection()
            return

        d = Deferred()
        d.addCallback(self.forwardResponse)
        d.addErrback(self.handleError)

        endpoint = TCP4ClientEndpoint(reactor, target_host, target_port)
        connectProtocol(endpoint, BackendClient(d)).addCallback(
            lambda proto: proto.sendCommand(msg)
        )

    def forwardResponse(self, payload):
        print("[Central] Forwarding response to client...")
        self.transport.write(struct.pack("!I", len(payload)))
        self.transport.write(payload)
        self.transport.loseConnection()

    def handleError(self, err):
        print("[Central] Error:", err)
        self.transport.write(b"error backend communication failed")
        self.transport.loseConnection()


factory = Factory()
factory.protocol = CentralProtocol

print("Central server running on port 9000...")
reactor.listenTCP(9000, factory)
reactor.run()