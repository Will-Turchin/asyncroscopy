# Ceos_server.py

"""
the real thing.
not async yet (socket)
"""

import logging
import json
from typing import Tuple, List, Optional, Union, Sequence
import traceback
import socket
from twisted.internet import reactor,defer, protocol
from asyncroscopy.servers.protocols.execution_protocol import ExecutionProtocol


logging.basicConfig()
log = logging.getLogger('CEOS_acquisition')
log.setLevel(logging.INFO)


# FACTORY — holds shared state (persistent across all connections)
class CeosFactory(protocol.Factory):
    def __init__(self):
        # persistent states for all protocol instances
        self.microscope = None
        self.detectors = {}
        self.status = "Offline"

    def buildProtocol(self, addr):
        """Create a new protocol instance and attach the factory (shared state)."""
        proto = CeosProtocol()
        proto.factory = self
        return proto


# PROTOCOL — handles per-connection command execution
# eventually, I want to move this into Execution protcol
# and move all function defs to the servers
class CeosProtocol(ExecutionProtocol):
    def __init__(self):
        super().__init__()
        self.host = "127.0.0.1"
        self.port = 7072
        self._nextMessageID = 1
        self._pendingCommands = {}

    # Override stringReceived for special case of Ceos commands
    def stringReceived(self, data: bytes):
        msg = data.decode().strip()
        print(f"[Exec] Received: {msg}")
        parts = msg.split()
        cmd, *args_parts = parts

        args_dict = dict(arg.split('=', 1) for arg in args_parts if '=' in arg)
        payload = {
            "jsonrpc": "2.0",
            "id": self._nextMessageID,
            "method": cmd,
            "params": args_dict
        }

        # Serialize dict to JSON bytes
        payload_bytes = json.dumps(payload).encode("utf-8")
        netstring = f"{len(payload_bytes)}:".encode("ascii") + payload_bytes + b","

        self._nextMessageID += 1

        with socket.create_connection((self.host, self.port), timeout=3000) as sock:
            sock.sendall(netstring)

            # Read until we hit a complete netstring (ends with b",")
            buffer = b""
            while not buffer.endswith(b","):
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk

        # Parse netstring: "length:payload,"
        try:
            length_str, rest = buffer.split(b":", 1)
            length = int(length_str)
            payload = rest[:length]
            return json.loads(payload.decode("utf-8"))
        except Exception as e:
            print("Malformed netstring or response:", buffer)
            raise e


if __name__ == "__main__":
    port = 9003
    print(f"[Ceos] Server running on port {port}...")
    reactor.listenTCP(port, CeosFactory())
    reactor.run()