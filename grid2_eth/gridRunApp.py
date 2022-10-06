import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gridWebsocket import PublicGridWebSocket, PrivateGridWebSocket
from loguru import logger
from binance import binance as ba
from user.account import Account
import time
import gridBot
import json


def get_main():
    # ====================================网格1参数设置===================================
    user_main = Account("yyn_big")
    # user_main = Account("syb")
    user_main.symbol = 'ETHUSDT'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD   1000LUNCUSDT
    user_main.websocket_symbol = 'ethusdt'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd   1000luncusdt
    user_main.trade_currency = 'USDT'  # 交易货币  USDT  BUSD
    user_main.position_side = 'SHORT'  # 做多 SHORT   LONG
    user_main.网格区间上限 = 1960
    user_main.网格区间下限 = 1360
    user_main.网格限价止损价格 = 1960.01
    user_main.网格市价止损价格 = 1960.01
    user_main.网格数量 = 398
    user_main.单网格数量 = 0.0067
    return user_main


def get_hedge():
    # ====================================网格2参数设置===================================
    user_hedge = Account("yyn_small")
    user_hedge.symbol = 'ETHBUSD'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD  1000LUNCUSDT
    user_hedge.websocket_symbol = 'ethbusd'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd  1000luncusdt
    user_hedge.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD
    user_hedge.position_side = 'LONG'  # 做空 SHORT   LONG
    user_hedge.网格区间上限 = 1360
    user_hedge.网格区间下限 = 760
    user_hedge.网格限价止损价格 = 759.99
    user_hedge.网格市价止损价格 = 759.99
    user_hedge.网格数量 = 398
    user_hedge.单网格数量 = 0.0067
    return user_hedge


if __name__ == '__main__':

    trace = logger.add("log/all.log", rotation="00:00")  # 每天0点创建新文件
    trace2 = logger.add("log/info.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    trace3 = logger.add("log/log.log", rotation="00:00",format="{time:YYYY-MM-DD HH:mm:ss} | {message}")  # 每天0点创建新文件

    user_main_1 = get_main()
    user_hedge_1 = get_hedge()

    # ====================================网格3参数设置===================================
    user_main_2 = get_main()
    user_main_2.symbol = 'ETHBUSD'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD  1000LUNCUSDT
    user_main_2.websocket_symbol = 'ethbusd'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd  1000luncusdt
    user_main_2.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD

    # ====================================网格4参数设置===================================
    user_hedge_2 = get_hedge()
    user_hedge_2.symbol = 'ETHUSDT'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD
    user_hedge_2.websocket_symbol = 'ethusdt'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd
    user_hedge_2.trade_currency = 'USDT'  # 交易货币  USDT  BUSD

    logger.info("开始初始化交易所...")
    ba.init_exchange(user_main_1, user_hedge_1)
    ba.init_exchange(user_main_2, user_hedge_2)
    logger.info("交易所初始化完毕,开始获取用户token...")
    ba.get_token(user_main_1, user_hedge_1)
    ba.get_token(user_main_2, user_hedge_2)
    ba.获取交易对规则2(user_main_1, user_hedge_1)
    ba.获取交易对规则2(user_main_2, user_hedge_2)
    # user_main_1.交易对价格精度 = 4
    # user_hedge_1.交易对价格精度 = 4
    # user_main_2.交易对价格精度 = 4
    # user_hedge_2.交易对价格精度 = 4
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    pub = PublicGridWebSocket(user_main_1, user_hedge_1)
    pub2 = PublicGridWebSocket(user_main_2, user_hedge_2)
    pub.run()
    pub2.run()
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    pri = PrivateGridWebSocket(user_main_1, user_hedge_1, user_main_2, user_hedge_2)
    pri.run()
    logger.info("私有化线程启动完毕,进入task...")
    time.sleep(4)
    # gridBot.创建网格(user_main)
    # ba.限价单(user_main, 30,0.18, 'BUY')
    # ba.限价单(user_main, 30,0.1802, 'BUY')
    # ba.限价单(user_main, 30,0.1804, 'BUY')

    # ba.撤销所有订单(user_main_1)
    # ba.撤销所有订单(user_main_2)
    # ba.撤销所有订单(user_hedge_1)
    # ba.撤销所有订单(user_hedge_2)
    # ba.市价平仓(user_main_1)
    # ba.市价平仓(user_main_2)
    # ba.市价平仓(user_hedge_1)
    # ba.市价平仓(user_hedge_2)
    # ba.查询账户持仓情况(user_main_1)
    # ba.查询账户持仓情况(user_main_2)
    # ba.查询账户持仓情况(user_hedge_1)
    # ba.查询账户持仓情况(user_hedge_2)



    # for i in range(100):
    #     ba.限价单(user_main_2, 30, 1.804, 'SELL')
    # ba.限价单(user_main_2, 30, 1.804, 'SELL')
    # ba.统计账户挂单详情(user_main_2)
    gridBot.创建网格4(user_main_1, user_hedge_1, user_main_2, user_hedge_2)
    # if user_main.need_sign:
    #     logger.info("需要信号开单，开启启动webhooks...")
    #     webhook = Webhooks(user_main, user_hedge)
    #     webhook.run()
