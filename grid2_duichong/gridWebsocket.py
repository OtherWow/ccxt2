import time
import websocket
import json
from loguru import logger
import threading
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from user.account import Account
from binance import binance as ba
from gridBot import 创建网格4

总手续费 = 0
总盈亏 = 0


class PublicGridWebSocket:
    def __init__(self, user_main_1: Account, user_main_2: Account):
        self.ws = None
        self.user_main_1 = user_main_1
        self.user_main_2 = user_main_2
        self.设置做多网格参数()
        logger.debug("PublicGridWebSocket初始化成功")

    def on_message(self, ws, message):
        data = json.loads(message)
        self.user_main_1.now_price = float(data['p'])
        self.user_main_2.now_price = float(data['p'])
        if self.user_main_1.now_price > self.user_main_1.中间价格 and self.user_main_1.网格已启动 is not True and self.user_main_1.触发做多订单号 == '':
            self.设置做多网格参数()
            ba.限价单(self.user_main_1, self.user_main_1.单网格数量,self.user_main_1.做多触发价格, "SELL")
            self.user_main_1.触发做多订单号 = str(self.user_main_1.order_info['orderId'])
        # if self.user_main_1.now_price < self.user_main_1.中间价格 and self.user_main_1.position_side == 'LONG' and self.user_main_1.触发做空订单号 == '':
        #     self.设置做空网格参数()
            # ba.限价单(self.user_main_1, self.user_main_1.单网格数量,self.user_main_1.做空触发价格, "BUY")
            # self.user_main_1.触发做空订单号 = str(self.user_main_1.order_info['orderId'])
        # if self.user_main_1.网格已启动 is not True and self.user_main_1.now_price>=self.user_main_1.做多触发价格:
        #     self.user_main_1.网格已启动 = True
        #     self.user_main_1.初始化完成 = False
        #     创建网格4(self.user_main_1,self.user_main_2)
        # if self.user_main_1.网格已启动 is not True and self.user_main_1.now_price <= self.user_main_1.做空触发价格:
        #     self.user_main_1.初始化完成 = False
        #     self.user_main_1.网格已启动 = True
        #     创建网格4(self.user_main_1, self.user_main_2)

    def on_ping(self, message, data):
        return

    def run(self):
        threading.Thread(target=self.public_ws_run, args={self.user_main_1}).start()

    def public_ws_run(self, user_main):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + user_main.websocket_symbol + "@markPrice",
                                         on_message=self.on_message,
                                         on_ping=self.on_ping)
        self.ws.run_forever(sslopt={"check_hostname": False})

    def 设置做多网格参数(self):
        self.user_main_1.position_side = 'LONG'  # 做多 SHORT   LONG
        self.user_main_1.网格区间上限 = 0.4
        self.user_main_1.网格区间下限 = 0.24
        self.user_main_1.网格限价止损价格 = 0.2399
        self.user_main_1.网格市价止损价格 = 0.2399

        self.user_main_2.position_side = self.user_main_1.position_side
        self.user_main_2.网格区间上限 = self.user_main_1.网格区间上限
        self.user_main_2.网格区间下限 = self.user_main_1.网格区间下限
        self.user_main_2.网格限价止损价格 = self.user_main_1.网格限价止损价格
        self.user_main_2.网格市价止损价格 = self.user_main_1.网格市价止损价格

    def 设置做空网格参数(self):
        self.user_main_1.position_side = 'SHORT'  # 做空 SHORT   LONG
        self.user_main_1.网格区间上限 = 0.23
        self.user_main_1.网格区间下限 = 0.15
        self.user_main_1.网格限价止损价格 = 0.2301
        self.user_main_1.网格市价止损价格 = 0.2301

        self.user_main_2.position_side = self.user_main_1.position_side
        self.user_main_2.网格区间上限 = self.user_main_1.网格区间上限
        self.user_main_2.网格区间下限 = self.user_main_1.网格区间下限
        self.user_main_2.网格限价止损价格 = self.user_main_1.网格限价止损价格
        self.user_main_2.网格市价止损价格 = self.user_main_1.网格市价止损价格


def 触发限价单则新增任务队列(data, user: Account, 配对user: Account, user_main: Account, user_main2: Account):
    global 总手续费
    global 总盈亏
    if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['x'] == 'TRADE' and data['o']['X'] == 'FILLED' and (data['o']['s'] == user.symbol) and float(data['o']['rp']) != 0:
        总手续费 += round(float(data['o']['n']), 7)
        总盈亏 += round(float(data['o']['rp']), 7)
        user.手续费 += round(float(data['o']['n']), 7)
        user.盈亏 += round(float(data['o']['rp']), 7)
        logger.info(f"总手续费：【{总手续费}】，总盈亏：【{总盈亏}】")
    if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE' and data['o']['X'] == 'FILLED' and (data['o']['s'] == user.symbol):  # 限价单成交
        # if user_main.触发做空订单号 == str(data['o']['i']) or user_main.触发做多订单号 == str(data['o']['i']):
        if  user_main.触发做多订单号 == str(data['o']['i']):
            logger.info(f"触发网格开单：【{data}】")
            user_main.触发做空订单号 = ''
            user_main.触发做多订单号 = ''
            user_main.初始化完成 = False
            user_main.网格已启动 = True
            创建网格4(user_main, user_main2)
        else:
            if (user.position_side == "LONG" and data['o']['S'] == 'SELL') or (user.position_side == "SHORT" and data['o']['S'] == 'BUY'):
                配对user.已配对次数 += 1
            logger.info(f"{user.name}【{user.symbol}】：限价单{data['o']['i']}成交，手续费：【{user.手续费}】，盈亏：【{user.盈亏}】，成交价格：{data['o']['p']}，成交数量：{data['o']['z']}，成交方向：{data['o']['S']}。{user_main.name}已配对【{user_main.已配对次数}】次")
            user.任务队列.put(str(data['o']['i']))
        return


class PrivateGridWebSocket:
    def __init__(self, user_main_1: Account, user_main_2: Account, ):
        self.num = None
        self.ws1 = None
        self.ws1_1 = None
        self.user_main_1 = user_main_1
        self.user_main_2 = user_main_2

    def run(self):
        threading.Thread(target=self.private_ws1).start()
        threading.Thread(target=self.private_ws1_1).start()

    def private_ws1(self):
        websocket.enableTrace(True)
        self.ws1 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_main_1.listen_key,
                                          on_message=self.ws1_message)
        self.ws1.run_forever(sslopt={"check_hostname": False})

    def private_ws1_1(self):
        websocket.enableTrace(True)
        self.ws1_1 = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + self.user_main_2.listen_key,
                                            on_message=self.ws1_1_message)
        self.ws1_1.run_forever(sslopt={"check_hostname": False})

    def ws1_message(self, ws, message):
        data = json.loads(message)
        self.如果仓位为0且满足条件则全部平仓(data, self.user_main_1)
        触发限价单则新增任务队列(data, self.user_main_1, self.user_main_1, self.user_main_1, self.user_main_2)

    def ws1_1_message(self, ws, message):
        data = json.loads(message)
        self.如果仓位为0且满足条件则全部平仓(data, self.user_main_2)
        触发限价单则新增任务队列(data, self.user_main_2, self.user_main_1, self.user_main_1, self.user_main_2)

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
                        ba.查询账户持仓情况(self.user_main_1)
                        ba.查询账户持仓情况(self.user_main_2)
                        ba.市价平仓(self.user_main_1)
                        ba.市价平仓(self.user_main_2)
                        ba.查询账户持仓情况(self.user_main_1)
                        ba.查询账户持仓情况(self.user_main_2)
                        user.网格已启动 = False
                        user.初始化完成 = False
                    return

    def on_ping(self, message, data):
        return


class Webhooks:
    user1 = None
    user2 = None

    def __init__(self, user_main: Account, ):
        self.user_main = user_main
        Webhooks.user1 = user_main

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
