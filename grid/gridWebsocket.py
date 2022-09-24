import time
import websocket
import json
from loguru import logger
import threading
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from user.account import Account
from binance import binance as ba


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


class PrivateGridWebSocket:
    def __init__(self, user_main: Account, user_hedge: Account):
        self.num = None
        self.ws1 = None
        self.ws2 = None
        self.user_main = user_main
        self.user_hedge = user_hedge

    def run(self):
        threading.Thread(target=self.private_ws1).start()
        threading.Thread(target=self.private_ws2).start()
        threading.Thread(target=self.队列任务).start()

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
                        logger.info(self.user_main.name + "账户仓位变更为【0】,撤销所有订单,然后平仓")
                        ba.撤销所有订单(self.user_main)
                        ba.撤销所有订单(self.user_hedge)
                        ba.查询账户持仓情况(self.user_main)
                        ba.查询账户持仓情况(self.user_hedge)
                        ba.市价平仓(self.user_main)
                        ba.市价平仓(self.user_hedge)
                    return
        if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE':  # 限价单成交
            if (self.user_main.position_side == "LONG" and data['o']['S'] == 'SELL') or (
                    self.user_main.position_side == "SHORT" and data['o']['S'] == 'BUY'):
                self.user_main.已配对次数 += 1
            logger.info(
                f"{self.user_main.name}限价单{data['o']['i']}成交，成交价格为{data['o']['p']}，成交数量为{data['o']['z']}，成交方向为{data['o']['S']}，已配对次数：【{self.user_main.已配对次数}】")
            self.user_main.任务队列.put(str(data['o']['i']))

    def ws2_message(self, ws, message):
        data = json.loads(message)
        if data['e'] == 'ACCOUNT_UPDATE':
            for temp in data['a']['P']:
                if temp['s'] == self.user_hedge.symbol:
                    pa = abs(float(temp['pa']))
                    self.user_hedge.position_amt = abs(float(temp['pa']))
                    if pa == 0:
                        logger.info(self.user_hedge.name + "账户仓位变更为【0】,撤销所有订单,然后平仓")
                        ba.撤销所有订单(self.user_main)
                        ba.撤销所有订单(self.user_hedge)
                        ba.查询账户持仓情况(self.user_main)
                        ba.查询账户持仓情况(self.user_hedge)
                        ba.市价平仓(self.user_main)
                        ba.市价平仓(self.user_hedge)
                    return

        if data['e'] == 'ORDER_TRADE_UPDATE' and data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE':  # 限价单成交
            if (self.user_hedge.position_side == "LONG" and data['o']['S'] == 'SELL') or (
                    self.user_hedge.position_side == "SHORT" and data['o']['S'] == 'BUY'):
                self.user_hedge.已配对次数 += 1
            logger.info(
                f"{self.user_hedge.name}限价单{data['o']['i']}成交，成交价格为{data['o']['p']}，成交数量为{data['o']['z']}，成交方向为{data['o']['S']}，已配对次数：【{self.user_hedge.已配对次数}】")
            self.user_hedge.任务队列.put(str(data['o']['i']))

    def on_ping(self, message):
        return

    def 队列任务(self):
        while True:
            if self.user_main.初始化完成 and (not self.user_main.任务队列.empty()):
                logger.info(self.user_main.name + "任务队列不为空，开始处理任务")
                self.处理任务(self.user_main)
            if self.user_hedge.初始化完成 and (not self.user_hedge.任务队列.empty()):
                logger.info(self.user_hedge.name + "任务队列不为空，开始处理任务")
                self.处理任务(self.user_hedge)
            time.sleep(0.2)

    def 处理任务(self, user: Account):
        orderId = user.任务队列.get()
        if orderId in user.order_map:
            grid = user.order_map[orderId]
            del user.order_map[orderId]
            grid.此网格订单号 = ""
            try:
                if grid.订单方向 == "SELL":
                    ba.限价单(user, grid.此网格数量, grid.此网格下边界价格, "BUY")
                    grid.订单方向 = "BUY"
                else:
                    ba.限价单(user, grid.此网格数量, grid.此网格上边界价格, "SELL")
                    grid.订单方向 = "SELL"
                grid.此网格订单号 = user.order_info['orderId']
                user.order_map[grid.此网格订单号] = grid
                logger.info(
                    f"{grid.网格名称}挂单成功，订单号：{grid.此网格订单号}，价格：{user.order_info['price']}，数量：{user.order_info['origQty']}，方向：{user.order_info['side']}，已配对次数：【{user.已配对次数}】")
            except Exception as e:
                ba.get_webserver_time()
                time.sleep(0.5)
                orderId = str(time.time()).replace(".", "")
                grid.此网格订单号 = orderId
                user.order_map[grid.此网格订单号] = grid
                self.user_main.任务队列.put(orderId)
                logger.error(user.name + '处理任务失败!' + str(e) + " 准备重试！")

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