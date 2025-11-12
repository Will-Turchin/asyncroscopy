from twisted.protocols.basic import Int32StringReceiver
import traceback
import logging
import json
logging.basicConfig()
log = logging.getLogger('CEOS_acquisition')
log.setLevel(logging.INFO)

class ExecutionProtocol(Int32StringReceiver):
    """
    Executes locally registered commands.
    Used by backend servers (AS, Gatan, CEOS).
    """

    def __init__(self):
        super().__init__()
        self.commands = {}
        self._pendingCommands = {}

    def connectionMade(self):
        # log.info('[Exec] Connection from {self.transport.getPeer()}')
        print(f"[Exec] Connection from {self.transport.getPeer()}")

    def connectionLost(self, reason):
        """
        Called by twisted after the connection to the server has been
        interrupted.
        """
        log.info('Client disconnected: %s', reason.getErrorMessage())

        for d in self._pendingCommands.values():
            d.errback(reason)
        self._pendingCommands.clear()
        
    def disconnect(self):
        """
        Disconnect from server.
        """
        self.transport.loseConnection()

    def register_command(self, name, func):
        """Register a callable command."""
        self.commands[name] = func

    def stringReceived(self, data: bytes):
        msg = data.decode().strip()
        print(f"[Exec] Received: {msg}")
        parts = msg.split()
        cmd, *args = parts

        try:
            if cmd not in self.commands:
                raise ValueError(f"Unknown command: {cmd}")

            handler = self.commands[cmd]
            result = handler(*args)
            if not isinstance(result, (bytes, bytearray)):
                result = str(result).encode()

            self.sendString(result)

        except Exception:
            err = traceback.format_exc()
            print(f"[Exec] Error executing '{msg}':\n{err}")
            self.sendString(err.encode())