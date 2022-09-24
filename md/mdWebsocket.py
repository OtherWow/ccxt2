import time
import websocket
import json
from loguru import logger
import threading
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from binance import binance as ba
import md


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
        # 监控价格 价格大于设定的值且对冲单仓位=0且网格仓位！=0时 市价买入
        if self.user_hedge.position_amt == 0 and self.user_main.position_amt != 0:
            if self.user_hedge.position_side == 'SHORT':  # 对冲单做空
                if self.user_hedge.now_price <= self.user_hedge.开单价格:
                    logger.info(
                        self.user_hedge.name + " 当前价格:{:4f}".format(
                            self.user_hedge.now_price) + "小于等于设定的价格:{:4f}".format(
                            self.user_hedge.开单价格) + " 对冲单仓位:" + str(self.user_hedge.position_amt) +
                        " 网格仓位:" + str(self.user_main.position_amt) + " 触发对冲单市价开单,方向：" + self.user_hedge.position_side)
                    ba.查询账户持仓情况(self.user_hedge)
                    ba.查询账户持仓情况(self.user_main)
                    if self.user_hedge.position_amt == 0 and self.user_main.position_amt != 0:
                        ba.市价单(self.user_hedge, self.user_hedge.首单数量, 'SELL')
                        logger.info(self.user_hedge.name + " 卖出市价单,数量：" + str(
                            self.user_hedge.首单数量) + " 当前价格：" + self.user_hedge.now_price) + "方向：" + self.user_hedge.position_side
                        time.sleep(1)
                        ba.查询账户持仓情况(self.user_hedge)
                        ba.查询账户持仓情况(self.user_main)
            else:  # 对冲单做多
                if self.user_hedge.now_price >= self.user_hedge.开单价格:
                    logger.info(
                        self.user_hedge.name + " 当前价格:{:4f}".format(
                            self.user_hedge.now_price) + "大于等于设定的价格:{:4f}".format(
                            self.user_hedge.开单价格) + " 对冲单仓位:" + str(self.user_hedge.position_amt) +
                        " 网格仓位:" + str(self.user_main.position_amt) + " 触发对冲单市价开单,方向：" + self.user_hedge.position_side)
                    ba.查询账户持仓情况(self.user_hedge)
                    ba.查询账户持仓情况(self.user_main)
                    if self.user_hedge.position_amt == 0 and self.user_main.position_amt != 0:
                        ba.市价单(self.user_hedge, self.user_hedge.首单数量, 'BUY')
                        logger.info(self.user_hedge.name + " 买入市价单,数量：" + str(
                            self.user_hedge.首单数量) + " 当前价格：" + self.user_hedge.now_price) + "方向：" + self.user_hedge.position_side
                        time.sleep(1)
                        ba.查询账户持仓情况(self.user_hedge)
                        ba.查询账户持仓情况(self.user_main)
        if self.user_hedge.position_amt != 0:
            if (self.user_hedge.position_side == 'SHORT' and self.user_hedge.now_price > self.user_hedge.开单价格) or (
                    self.user_hedge.position_side == 'LONG' and self.user_hedge.now_price < self.user_hedge.开单价格):  # 对冲单做空
                # 3. 监控价格 价格小于设定的值且对冲单仓位！=0 对冲单市价平仓
                logger.info(
                    self.user_hedge.name + " 当前价格:{:4f}".format(self.user_hedge.now_price) + " 设定的价格:{:4f}".format(
                        self.user_hedge.开单价格) + " 对冲单仓位:" + str(
                        self.user_hedge.position_amt) + " 触发对冲单市价平仓,方向：" + self.user_hedge.position_side)
                ba.查询账户持仓情况(self.user_hedge)
                if self.user_hedge.position_amt != 0:
                    ba.市价平仓(self.user_hedge)
                    time.sleep(1)
                    ba.撤销所有订单(self.user_hedge)
                    ba.查询账户持仓情况(self.user_hedge)

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
        self.num = None
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
                    self.user_main.position_amt = abs(float(temp['pa']))
                    # logger.info(self.user_main.name + "账户仓位变更为【" + str(self.user_main.position_amt) + "】")
                    if pa == 0:
                        logger.info(self.user_main.name + "账户仓位变更为【0】,清空对冲单仓位，清空网格挂单，清空对冲单挂单")
                        ba.市价平仓(self.user_hedge)
                        time.sleep(1)
                        ba.撤销所有订单(self.user_hedge)
                        ba.查询账户持仓情况(self.user_main)
                        ba.查询账户持仓情况(self.user_hedge)
                    return
        # if user['e'] == 'ORDER_TRADE_UPDATE' and user['o']['o'] == 'LIMIT' and user['o']['x'] == 'TRADE':
        #     md.止盈止损单(self.user_main)
        #     if self.user_main.马丁补单单号字典[self.user_main.马丁补单当前索引] == user['o']['i']:
        #         if self.user_hedge.position_side == 'SHORT':
        #             side = 'SELL'
        #         else:
        #             side = 'BUY'
        #         if self.user_main.马丁补单当前索引 == 0:
        #             md.市价单(self.user_hedge, self.user_hedge.首单数量, side)
        #         elif self.user_main.马丁补单当前索引 == 1:
        #             md.市价单(self.user_hedge, self.user_hedge.首次补仓数量, side)
        #             self.num = self.user_hedge.首次补仓数量
        #         else:
        #             self.num = self.num * self.user_hedge.补仓倍数
        #             md.市价单(self.user_hedge, self.num, side)
        #         time.sleep(2)
        #         md.止盈止损单(self.user_hedge)
        #         self.user_main.马丁补单当前索引 += 1

    def ws2_message(self, ws, message):
        data = json.loads(message)
        if data['e'] == 'ACCOUNT_UPDATE':
            for temp in data['a']['P']:
                if temp['s'] == self.user_hedge.symbol:
                    self.user_hedge.position_amt = abs(float(temp['pa']))
                    logger.info(self.user_hedge.name + "账户仓位变更为【" + str(self.user_hedge.position_amt) + "】")
                    # md.查询账户持仓情况(self.user_hedge)
                    # time.sleep(1)
        #             if pa == 0:
        #                 logger.info(self.user_hedge.name + "账户仓位变更为【0】,重新开单")
        #                 time.sleep(10)
        #                 md.双马丁策略(self.user_main, self.user_hedge)
        #             return

    def on_ping(self, message):
        return


class Webhooks:
    user1 = None
    user2 = None

    def __init__(self, user_main, user_hedge):
        self.user_main = user_main
        self.user_hedge = user_hedge
        Webhooks.user1 = user_main
        Webhooks.user2 = user_hedge

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
        # print("转化前data:" + user)
        data = json.dumps(eval(data))
        # print("转化后data:" + user)
        json_obj = json.loads(data)
        if Webhooks.user1.now_timestamp != json_obj['timestamp']:
            Webhooks.user1.now_timestamp = json_obj['timestamp']
            md.sign1(json_obj, Webhooks.user1, Webhooks.user2)


if __name__ == '__main__':
    for i in range(6):
        print(i)
    print("")
