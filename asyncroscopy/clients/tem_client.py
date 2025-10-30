# tem_client.py
import socket, struct, numpy as np
from concurrent.futures import ThreadPoolExecutor

# still needs a lot of work
class TEMClient:
    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port
        self.executor = ThreadPoolExecutor(max_workers=8) # arbitrary for now

    @classmethod
    def connect(cls,  host="127.0.0.1", port=9000):
        """Try to connect briefly to verify central server is up.
        Returns TEMClient(host, port) on success, or None on failure.
        """
        print(f"Connecting to central server {host}:{port}...")
        try:
            with socket.create_connection((host, port), timeout=5) as s:
                print("Connected :)")
            return cls(host, port)
        except (ConnectionRefusedError, socket.timeout):
            print(f"Could not connect to central server at {host}:{port}")
            return None

    def send_command(self, command: str, timeout: float | None = None) -> bytes:
        """Send a command string to the central server and return the raw payload bytes.
        Optionally specify a timeout in seconds.
        """
        try:
            with socket.create_connection((self.host, self.port), timeout=timeout) as s:
                s.sendall(command.encode())
                hdr = self._recv_exact(s, 4)
                nbytes = struct.unpack("!I", hdr)[0]
                data = self._recv_exact(s, nbytes)
            return data

        except (ConnectionRefusedError, socket.timeout):
            print(f"Could not connect to central server at {host}:{port} after {timeout} seconds")
            return None

    # -------------------------------------------------------
    def connect_AS(self, host, port):
        """Request a connection from this TEMClient to the AS server at (host, port).
        """
        cmd = f"AS_connect_AS {host} {port}"
        data = self.send_command(cmd, timeout=5)
        return data.decode()

    def get_status(self):
        """
        Confirms/denies if the AS server is connected to the microscope.
        """
        cmd = "AS_get_status"
        data = self.send_command(cmd)
        return data.decode()

    def get_image(self, size):
        cmd = f"AS_get_image {size}"
        data = self.send_command(cmd)
        img = np.frombuffer(data, dtype=np.uint8).reshape(size, size)
        return img

    def get_spectrum(self, size):
        cmd = f"Gatan_get_spectrum {size}"
        data = self.send_command(cmd)
        spectrum = np.frombuffer(data, dtype=np.float32)
        return spectrum

    def get_image_and_spectrum(self, image_size, spectrum_size):
        """Run both acquisitions concurrently and return results."""
        future_img = self.executor.submit(self.get_image, image_size)
        future_spec = self.executor.submit(self.get_spectrum, spectrum_size)
        img = future_img.result()
        spec = future_spec.result()
        return img, spec

    def _recv_exact(self, sock, n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Socket closed early")
            buf += chunk
        return buf