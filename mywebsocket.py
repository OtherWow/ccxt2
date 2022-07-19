import websocket
import json
from loguru import logger
import threading


class PublicWebSocket():
    def __init__(self, user_main,user_hedge):
        self.user_main = user_main
        self.user_hedge = user_hedge

    def on_message(self, ws, message):
        data = json.loads(message)
        self.user_main.now_price = float(data['p'])
        self.user_hedge.now_price = float(data['p'])
        # print("市场价格："+str(message))

    def on_ping(self, message):
        return

    def public_ws_run(self,user_main):
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + user_main.websocket_symbol + "@markPrice",
                                    on_message=PublicWebSocket.on_message,
                                    on_ping=PublicWebSocket.on_ping)
        ws.run_forever(sslopt={"check_hostname": False})


    def run(self,user_main):
        threading.Thread(target=public_ws_run, args={user_main}).start()

class PrivateWebSocket():
    def __init__(self, user):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://fstream.binance.com/ws/" + user.listen_key,
                                         on_message=self.auth_message)
        self.ws.run_forever(sslopt={"check_hostname": False})
        self.user = user

    def auth_message(self, ws, message):
        data = json.loads(message)
        # if not self.user.need_sign:
        #     if data['e'] == 'ACCOUNT_UPDATE':
        #         for i in data['a']['P']:
        #             if i['s'] == d.symbol:
        #                 pa = abs(float(i['pa']))
        #                 logger.info("账户仓位变更=>最后仓位数量:" + str(d.last_entry_num) + "当前仓位数量:" + str(pa))
        #                 if d.min_entry_num <= pa != d.last_entry_num:
        #                     logger.info("触发仓位变更 最小仓位数量：" + str(d.min_entry_num))
        #                     d.last_entry_num = pa
        #                     trade("")
        #                 break
        #
        # if d.right_now_order_after_stop:
        #     if data['e'] == 'ORDER_TRADE_UPDATE':
        #         if data['o']['x'] == 'EXPIRED':
        #             if data['o']['o'] == 'STOP_MARKET':
        #                 logger.info("已止损平仓")
        #                 time.sleep(1)
        #                 data = {
        #                     "type": "sell",
        #                     "timestamp": 431115,
        #                 }
        #                 trade(data)
        #             elif data['o']['o'] == 'TAKE_PROFIT_MARKET':
        #                 logger.info("已止盈平仓")
        #                 time.sleep(1)
        #                 data = {
        #                     "type": "sell",
        #                     "timestamp": 431115,
        #                 }
        #                 trade(data)
        #         if data['o']['o'] == 'LIMIT' and data['o']['x'] == 'TRADE' and data['o']['S'] == 'BUY':
        #             logger.info("已限价止损平仓")
        #             time.sleep(1)
        #             data = {
        #                 "type": "sell",
        #                 "timestamp": 431115,
        #             }
        #             trade(data)

    def on_ping(self, message):
        return


if __name__ == '__main__':
    # 1
    print("")
