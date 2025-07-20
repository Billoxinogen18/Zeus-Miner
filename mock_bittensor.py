
class MockWallet:
    def __init__(self, name=None, hotkey=None):
        self.name = name
        self.hotkey = hotkey

class MockSubtensor:
    def __init__(self, network=None):
        self.network = network
    
    def metagraph(self, netuid):
        return MockMetagraph()

class MockMetagraph:
    def __init__(self):
        self.S = [1000, 800, 600, 400, 200] * 10  # Mock stakes

def wallet(name=None, hotkey=None):
    return MockWallet(name, hotkey)

def subtensor(network=None):
    return MockSubtensor(network)

def metagraph(netuid):
    return MockMetagraph()

__version__ = "7.3.0"
