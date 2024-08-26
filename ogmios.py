import json
from websockets.sync.client import connect

class Ogmios:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws     = connect(self.ws_url)
        self.queries = {
                'NextBlock':         OgmiosQuery({"method": "nextBlock"}, ws=self.ws),
                'FindIntersect':     OgmiosQuery({"method": "findIntersection"}, ws=self.ws),
                'LocalStateAcquire': OgmiosQuery({"method": "acquireLedgerState"}, ws=self.ws),
                'LocalStateQuery':   OgmiosQuery({"method": "queryLedgerState/utxo"}, ws=self.ws),
                'LocalStateRelease': OgmiosQuery({"method": "releaseLedgerState"}, ws=self.ws),
                'QueryNetworkTip':   OgmiosQuery({"method": "queryNetwork/tip"}, ws=self.ws),
                'SubmitTransaction': OgmiosQuery({"method": "submitTransaction"}, ws=self.ws),
                'EvaluateTransaction': OgmiosQuery({"method": "evaluateTransaction"}, ws=self.ws),
                'AcquireMempool': OgmiosQuery({"method": "acquireMempool"}, ws=self.ws),
                'NextTransaction': OgmiosQuery({"method": "nextTransaction"}, ws=self.ws),
                'ProtocolParameters': OgmiosQuery({"method": "queryLedgerState/protocolParameters"}, ws=self.ws),
                }

    def get_url(self):
        return self.ws_url

    def query(self, query_name, params={}):
        return self.queries[query_name].run(params=params)

class OgmiosQuery:
    def __init__(self, query, ws=None):
        self.q = {"type": "jsonwsp/request","version": "1.0","servicename": "ogmios", "params": {}, "mirror": None, "jsonrpc": "2.0"}
        self.q.update(query)
        self.ws = ws

    def get(self, params={}):
        return json.dumps(dict(self.q, params=params))

    def run(self, params={}):
        req = self.get(params)
        self.ws.send(req)
        m = self.ws.recv()
        res = json.loads(m)
        return res
