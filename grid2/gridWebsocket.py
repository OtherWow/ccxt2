import time
import websocket
import json
from loguru import logger
import threading
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from user.account import Account
from binance import binance as ba

总手续费 = 0
总盈亏 = 0


class PublicGridWebSocket:
    def __init__(self, user_main: Account, user_hedge: Account):
        self.ws = None
        self.user_main = user_main
        self.user_hedge = user_hedge
        logger.debug("PublicGridWebSocket初始化成功")

    def on_message(self, ws, message):
        data = json.loads(message)
        self.user_main.now_price = float(data['p'])
        self.user_hedge.now_price = float(data['p'])

    def run(self):
        threading.Thread(target=self.public_ws_run, args={self.user_main}).start()

    def public_ws_run(self, user_main):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + user_main.websocket_symbol + "@markPrice",
                                         on_message=self.on_message,
                                         on_close=self.on_close,
                                         on_error=self.on_error
                                         )
        self.ws.run_forever(sslopt={"check_hostname": False}, ping_interval=60, ping_timeout=10)

    def on_close(self, code, reason):
        logger.info(f"{self.user_main.name}：公共连接关闭，code：{code}，reason：{reason},准备断线重连...")
        self.ws = None
        self.public_ws_run(self.user_main)

    def on_error(self, error):
        logger.info(f"{self.user_main.name}：公共连接错误，error：{error} ")
        logger.debug(type(error))


def 触发限价单则新增任务队列(data, user: Account, 配对user: Account, user_main: Account, user_hedge: Account):
    # global 总手续费
    # global 总盈亏
    # if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['x'] == 'TRADE' and data['o']['X'] == 'FILLED' and (data['o']['s'] == user.symbol) and float(data['o']['rp']) != 0:
    #     总手续费 += round(float(data['o']['n']), 7)
    #     总盈亏 += round(float(data['o']['rp']), 7)
    #     user.手续费 += round(float(data['o']['n']), 7)
    #     user.盈亏 += round(float(data['o']['rp']), 7)
    #     logger.info(f"总手续费：【{总手续费}】，总盈亏：【{总盈亏}】")
    if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE' and data['o']['X'] == 'FILLED' and (data['o']['s'] == user.symbol and user.trade_currency == data['o']['N']):  # 限价单成交
        if (user.position_side == "LONG" and data['o']['S'] == 'SELL') or (user.position_side == "SHORT" and data['o']['S'] == 'BUY'):
            配对user.已配对次数 += 1
        logger.info(f"{user.name}【{user.symbol}】：限价单{data['o']['i']}成交，成交价格：{data['o']['p']}，成交数量：{data['o']['z']}，成交方向：{data['o']['S']}。{user_main.name}已配对【{user_main.已配对次数}】次,{user_hedge.name}已配对【{user_hedge.已配对次数}】次")
        user.任务队列.put(str(data['o']['i']))
        return


class PrivateGridWebSocket:
    def __init__(self, user_main_1: Account, user_hedge_1: Account, user_main_2: Account, user_hedge_2: Account):
        self.num = None
        self.ws1 = None
        self.ws1_1 = None
        self.ws2 = None
        self.ws2_2 = None
        self.user_main_1 = user_main_1
        self.user_main_2 = user_main_2
        self.user_hedge_1 = user_hedge_1
        self.user_hedge_2 = user_hedge_2

    def run(self):
        threading.Thread(target=self.private_ws1).start()
        threading.Thread(target=self.private_ws1_1).start()
        threading.Thread(target=self.private_ws2).start()
        threading.Thread(target=self.private_ws2_2).start()

    def private_ws1(self):
        websocket.enableTrace(True)
        self.ws1 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_main_1.listen_key,
                                          on_message=self.ws1_message,
                                          on_close=self.ws1_close,
                                          on_error=self.ws1_error
                                          )
        self.ws1.run_forever(sslopt={"check_hostname": False}, ping_interval=60, ping_timeout=10)

    def ws1_close(self, code, reason):
        logger.info(f"{self.user_main_1.name}：ws1关闭，code：{code}，reason：{reason},准备断线重连...")
        self.ws1 = None
        self.private_ws1()

    def ws1_error(self, error):
        logger.info(f"{self.user_main_1.name}：ws1错误，error：{error} ")
        logger.debug(type(error))

    def private_ws2(self):
        websocket.enableTrace(True)
        self.ws2 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_hedge_2.listen_key,
                                          on_message=self.ws2_message,
                                          on_close=self.ws2_close,
                                          on_error=self.ws2_error)
        self.ws2.run_forever(sslopt={"check_hostname": False}, ping_interval=60, ping_timeout=10)

    def ws2_close(self, code, reason):
        logger.info(f"{self.user_hedge_2.name}：ws2关闭，code：{code}，reason：{reason},准备断线重连...")
        self.ws2 = None
        self.private_ws2()

    def ws2_error(self, error):
        logger.info(f"{self.user_hedge_2.name}：ws2错误，error：{error} ")
        logger.debug(type(error))

    def private_ws1_1(self):
        websocket.enableTrace(True)
        self.ws1_1 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_main_2.listen_key,
                                            on_message=self.ws1_1_message,
                                            on_close=self.ws1_1_close,
                                            on_error=self.ws1_1_error)
        self.ws1_1.run_forever(sslopt={"check_hostname": False}, ping_interval=60, ping_timeout=10)

    def ws1_1_close(self, code, reason):
        logger.info(f"{self.user_main_2.name}：ws1_1关闭，code：{code}，reason：{reason},准备断线重连...")
        self.ws1_1 = None
        self.private_ws1_1()

    def ws1_1_error(self, error):
        logger.info(f"{self.user_main_2.name}：ws1_1错误，error：{error} ")
        logger.debug(type(error))

    def private_ws2_2(self):
        websocket.enableTrace(True)
        self.ws2_2 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_hedge_2.listen_key,
                                            on_message=self.ws2_2_message,
                                            on_close=self.ws2_2_close,
                                            on_error=self.ws2_2_error)
        self.ws2_2.run_forever(sslopt={"check_hostname": False}, ping_interval=60, ping_timeout=10)

    def ws2_2_close(self, code, reason):
        logger.info(f"{self.user_hedge_2.name}：ws2_2关闭，code：{code}，reason：{reason},准备断线重连...")
        self.ws2_2 = None
        self.private_ws2_2()

    def ws2_2_error(self, error):
        logger.info(f"{self.user_hedge_2.name}：ws2_2错误，error：{error} ")
        logger.debug(type(error))

    def ws1_message(self,ws, message):
        data = json.loads(message)
        self.如果仓位为0且满足条件则全部平仓(data, self.user_main_1)
        触发限价单则新增任务队列(data, self.user_main_1, self.user_main_1, self.user_main_1, self.user_hedge_1)

    def ws1_1_message(self,ws, message):
        data = json.loads(message)
        self.如果仓位为0且满足条件则全部平仓(data, self.user_main_2)
        触发限价单则新增任务队列(data, self.user_main_2, self.user_main_1, self.user_main_1, self.user_hedge_1)

    def ws2_message(self,ws, message):
        data = json.loads(message)
        self.如果仓位为0且满足条件则全部平仓(data, self.user_hedge_1)
        触发限价单则新增任务队列(data, self.user_hedge_1, self.user_hedge_1, self.user_main_1, self.user_hedge_1)

    def ws2_2_message(self,ws, message):
        data = json.loads(message)
        self.如果仓位为0且满足条件则全部平仓(data, self.user_hedge_2)
        触发限价单则新增任务队列(data, self.user_hedge_2, self.user_hedge_1, self.user_main_1, self.user_hedge_1)

    def 如果仓位为0且满足条件则全部平仓(self, data, user: Account):
        if data['e'] == 'ACCOUNT_UPDATE':
            for temp in data['a']['P']:
                if temp['s'] == user.symbol:
                    pa = abs(float(temp['pa']))
                    user.position_amt = abs(float(temp['pa']))
                    if pa == 0 and ((
                                            user.position_side == "LONG" and user.now_price <= user.网格限价止损价格) or (
                                            user.position_side == "SHORT" and user.now_price >= user.网格限价止损价格)):
                        logger.info(user.name + "账户【" + user.symbol + "】仓位变更为【0】,撤销所有订单,然后平仓")
                        ba.撤销所有订单(self.user_main_1)
                        ba.撤销所有订单(self.user_main_2)
                        ba.撤销所有订单(self.user_hedge_1)
                        ba.撤销所有订单(self.user_hedge_2)
                        ba.查询账户持仓情况(self.user_main_1)
                        ba.查询账户持仓情况(self.user_main_2)
                        ba.查询账户持仓情况(self.user_hedge_1)
                        ba.查询账户持仓情况(self.user_hedge_2)
                        ba.市价平仓(self.user_main_1)
                        ba.市价平仓(self.user_main_2)
                        ba.市价平仓(self.user_hedge_1)
                        ba.市价平仓(self.user_hedge_2)
                        ba.查询账户持仓情况(self.user_main_1)
                        ba.查询账户持仓情况(self.user_main_2)
                        ba.查询账户持仓情况(self.user_hedge_1)
                        ba.查询账户持仓情况(self.user_hedge_2)
                    return

    def on_ping(self, message, data):
        return


class Webhooks:
    user1 = None
    user2 = None

    def __init__(self, user_main: Account, user_hedge: Account):
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
        # md.sign1(json_obj, Webhooks.user1, Webhooks.user2)


if __name__ == '__main__':
    for i in range(6):
        print(i)
    print("")
