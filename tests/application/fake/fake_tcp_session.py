


class FakeTCPSession:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 8000
    
    async def run(self)->str:
        return 'ok'