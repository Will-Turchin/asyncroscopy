# AS_server.py

"""
the real thing.
"""

from twisted.internet import reactor, protocol
import numpy as np
import time
import sys
import SciFiReaders
import json, struct


from asyncroscopy.servers.protocols.execution_protocol import ExecutionProtocol
# sys.path.insert(0, "C:\\AE_future\\autoscript_1_14\\")
sys.path.insert(0, "/Users/austin/Desktop/Projects/autoscript_tem_microscope_client")
import autoscript_tem_microscope_client as auto_script


# FACTORY — holds shared state (persistent across all connections)
class Preacquired_ASFactory(protocol.Factory):
    def __init__(self):
        # persistent states for all protocol instances
        self.dataset = None
        self.status = "Offline"


    def buildProtocol(self, addr):
        """Create a new protocol instance and attach the factory (shared state)."""
        proto = Preacquired_ASProtocol()
        proto.factory = self
        return proto


# PROTOCOL — handles per-connection command execution
class Preacquired_ASProtocol(ExecutionProtocol):
    def __init__(self):
        super().__init__()
        # Register supported commands
        self.register_command("connect_Preacquired_AS", self.connect_Preacquired_AS)
        self.register_command("get_scanned_image", self.get_scanned_image)



    # ---------------------------------------------------------------

    def connect_Preacquired_AS(self, data_source = 'test.h5'):
        ###e.g., generate the data if required at this step
        print(data_source)
        reader = SciFiReaders.NSIDReader(data_source)
        self.factory.dataset = reader.read()
        # reader.close()
        ds = self.factory.dataset
        try:
            # Attempt to access keys attribute to check if dataset is already a dictionary
            keys = list(ds.keys())
            summary = ", ".join([f"{k}: {ds[k].shape}, {ds[k].dtype}" for k in keys])

        except AttributeError:
            # AttributeError is raised because 'dataset' is a list, so convert it to a dictionary
            dataset_dict = {}
            
            for i, item in enumerate(self.dataset):
                key = f"Channel_{i:03}"  # Format key with zero-padding, e.g., 'channel_000'
                dataset_dict[key] = item
            self.factory.dataset = dataset_dict
            ds = self.factory.dataset
            keys = list(ds.keys())
            summary = ", ".join([f"{k}: {ds[k].shape}, {ds[k].dtype}" for k in keys])
        msg = f"[Preacquired_AS] Data loaded with keys :{summary} "
        return msg.encode()

    # ---------------------------------------------------------------

    def get_scanned_image(self, channel_key="Channel_000"):
        self.factory.status = "Busy"
        arr = np.asarray(self.factory.dataset[channel_key])
        header = json.dumps({"dtype": arr.dtype.str, "shape": arr.shape}).encode()
        msg = struct.pack("!I", len(header)) + header + arr.tobytes()
        self.factory.status = "Ready"
        return msg



    def get_point_data(self, spectrum_image_key, x, y):
        """emulates the data acquisition at a specific point

        Args:
            spectrum_image_key: Which index in sidpy dataset is spectrum index
            x : position in x
            y : position in y

        Returns:
            numpy array: data at that
            
        >>>spectrum = mic.datasets([1][0][0])
        >>>spectrum  is of shape 1496
        """
        return np.array(self.dataset[spectrum_image_key][x][y])


# ================================================================
if __name__ == "__main__":
    port = 9004
    print(f"[AS] Server running on port {port}...")
    reactor.listenTCP(port, Preacquired_ASFactory())
    reactor.run()