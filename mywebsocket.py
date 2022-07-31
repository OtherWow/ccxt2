import websocket
import json
from loguru import logger
import threading
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
import mading


class PublicWebSocket:
    def __init__(self, user_main, user_hedge):
        self.ws = None
        self.user_main = user_main
        self.user_hedge = user_hedge
        logger.debug("PublicWebSocket初始化成功")

    def on_message(self, ws, message):
        data = json.loads(message)
        self.user_main.now_price = float(data['p'])
        self.user_hedge.now_price = float(data['p'])
        if self.user_main.position_side == 'SHORT':
            if self.user_main.now_price >= self.user_main.马丁触发价格 != 0:
                mading.马丁开首单(self.user_main, self.user_hedge)
            # if self.user_main.position_amt>0 and self.user_main.now_price > self.user_main.entry_price and self.user_hedge.position_amt == 0:
            #     if self.user_hedge.now_price > self.user_main.entry_price:
            #         mading.市价单(self.user_hedge, self.user_hedge.首单数量, 'BUY')
            #         mading.止盈止损单(self.user_hedge)
        if self.user_main.position_side == 'LONG':
            if self.user_main.now_price <= self.user_main.马丁触发价格 != 0:
                mading.马丁开首单(self.user_main, self.user_hedge)
            # if self.user_main.position_amt>0 and self.user_main.now_price < self.user_main.entry_price and self.user_hedge.position_amt == 0:
            #     if self.user_hedge.now_price < self.user_main.entry_price:
            #         mading.市价单(self.user_hedge, self.user_hedge.首单数量, 'BUY')
            #         mading.止盈止损单(self.user_hedge)

    def on_ping(self, message):
        return

    def run(self):
        threading.Thread(target=self.public_ws_run, args={self.user_main}).start()

    def public_ws_run(self, user_main):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + user_main.websocket_symbol + "@markPrice",
                                         on_message=self.on_message,
                                         on_ping=self.on_ping)
        self.ws.run_forever(sslopt={"check_hostname": False})


class PrivateWebSocket:
    def __init__(self, user_main, user_hedge):
        self.ws1 = None
        self.ws2 = None
        self.user_main = user_main
        self.user_hedge = user_hedge

    def run(self):
        threading.Thread(target=self.private_ws1).start()
        threading.Thread(target=self.private_ws2).start()

    def private_ws1(self):
        websocket.enableTrace(True)
        self.ws1 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_main.listen_key,
                                          on_message=self.ws1_message)
        self.ws1.run_forever(sslopt={"check_hostname": False})

    def private_ws2(self):
        websocket.enableTrace(True)
        self.ws2 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_hedge.listen_key,
                                          on_message=self.ws2_message)
        self.ws2.run_forever(sslopt={"check_hostname": False})

    def ws1_message(self, ws, message):
        data = json.loads(message)
        if data['e'] == 'ACCOUNT_UPDATE':
            for temp in data['a']['P']:
                if temp['s'] == self.user_main.symbol:
                    pa = abs(float(temp['pa']))
                    if pa == 0:
                        logger.info(self.user_main.name + "账户仓位变更为0,对冲单开始平仓")
                        mading.撤销所有订单(self.user_hedge)
                        mading.撤销所有订单(self.user_main)
                        mading.查询账户持仓情况(self.user_hedge)
                        if self.user_hedge.position_amt > 0:
                            mading.市价平仓(self.user_hedge)
                    return
        if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE':
            mading.止盈止损单(self.user_main)
            return

    def ws2_message(self, ws, message):
        data = json.loads(message)
        if data['e'] == 'ACCOUNT_UPDATE':
            for temp in data['a']['P']:
                if temp['s'] == self.user_hedge.symbol:
                    pa = abs(float(temp['pa']))
                    if pa == 0:
                        logger.info(self.user_hedge.name + "账户仓位变更为0")
                    return
        if data['e'] == 'ORDER_TRADE_UPDATE':
            if data['o']['x'] == 'EXPIRED' and data['o']['o'] == 'STOP_MARKET':
                logger.info("已止损平仓")

            if data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE' and data['o']['S'] == 'BUY':
                logger.info("已限价止损平仓")

    def on_ping(self, message):
        return


user1 = None
user2 = None


class Webhooks:
    def __init__(self, user_main, user_hedge):
        self.user_main = user_main
        self.user_hedge = user_hedge
        user1 = user_main
        user2 = user_hedge

    def init_webhooks(self):
        addr = ('', self.user_main.port)
        server = HTTPServer(addr, RequestHandler)
        server.serve_forever()

    def run(self):
        threading.Thread(target=self.init_webhooks).start()


class RequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        data = self.rfile.read(int(self.headers['content-length']))
        data = unquote(str(data, encoding='utf-8'))
        # print("转化前data:" + data)
        data = json.dumps(eval(data))
        # print("转化后data:" + data)
        json_obj = json.loads(data)
        if user1.now_timestamp != json_obj['timestamp']:
            user1.now_timestamp = json_obj['timestamp']
            mading.sign1(json_obj, user1, user2)


if __name__ == '__main__':
    for i in range(6):
        print(i)
    print("")
