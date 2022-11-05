import sys
import os

import threading

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
    user_main.symbol = '1000LUNCUSDT'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD   1000LUNCUSDT
    user_main.websocket_symbol = '1000luncusdt'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd   1000luncusdt
    user_main.trade_currency = 'USDT'  # 交易货币  USDT  BUSD
    user_main.position_side = 'SHORT'  # 做多 SHORT   LONG
    user_main.网格区间上限 = 0.4
    user_main.网格区间下限 = 0.24
    user_main.网格限价止损价格 = 0.4001
    user_main.网格市价止损价格 = 0.4001
    user_main.网格间距 = 0.0004
    user_main.网格数量 = 398
    user_main.单网格数量 = 60
    return user_main


def get_hedge():
    # ====================================网格2参数设置===================================
    user_hedge = Account("yyn_small")
    user_hedge.symbol = '1000LUNCBUSD'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD  1000LUNCUSDT
    user_hedge.websocket_symbol = '1000luncbusd'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd  1000luncusdt
    user_hedge.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD
    user_hedge.position_side = 'LONG'  # 做空 SHORT   LONG
    user_hedge.网格区间上限 = 0.24
    user_hedge.网格区间下限 = 0.16
    user_hedge.网格限价止损价格 = 0.0799
    user_hedge.网格市价止损价格 = 0.0799
    user_hedge.网格间距 = 0.0002
    user_hedge.网格数量 = 398
    user_hedge.单网格数量 = 50
    return user_hedge


def 处理任务(user: Account, orderId):
    logger.info(user.name + f"【{user.symbol}】任务队列不为空，开始处理任务")
    if orderId in user.order_map:
        grid = user.order_map[orderId]
        del user.order_map[orderId]
        grid.此网格订单号 = ""
        try:
            if grid.订单方向 == "SELL":
                ba.限价单抛异常(user, grid.此网格数量, grid.此网格下边界价格, "BUY", grid)
            else:
                ba.限价单抛异常(user, grid.此网格数量, grid.此网格上边界价格, "SELL", grid)
            user.order_map[grid.此网格订单号] = grid
            logger.info(f"{grid.网格名称}挂单成功，订单号：{grid.此网格订单号}，价格：{user.order_info['price']}，数量：{user.order_info['origQty']}，方向：{user.order_info['side']}")  # ，已配对次数：【{user.已配对次数}】
        except:
            logger.exception(f"{grid.网格名称} 处理任务失败! 准备重试！")
            # ba.统计账户挂单详情(user)
            ba.get_webserver_time()
            time.sleep(0.5)
            newOrderId = str(time.time()).replace(".", "")
            grid.此网格订单号 = newOrderId
            user.order_map[grid.此网格订单号] = grid
            user.任务队列.put(newOrderId)
        return
    else:
        logger.info(f"订单号{orderId} 异常 没有匹配到对应的订单号！")


if __name__ == '__main__':
    trace = logger.add("log/all.log", rotation="00:00")  # 每天0点创建新文件
    trace2 = logger.add("log/info.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    trace3 = logger.add("log/log.log", rotation="00:00", )  # 每天0点创建新文件

    user_main_1 = get_main()
    user_hedge_1 = get_hedge()

    # ====================================网格3参数设置===================================
    user_main_2 = get_main()
    user_main_2.symbol = '1000LUNCBUSD'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD  1000LUNCUSDT
    user_main_2.websocket_symbol = '1000luncbusd'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd  1000luncusdt
    user_main_2.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD

    # ====================================网格4参数设置===================================
    user_hedge_2 = get_hedge()
    user_hedge_2.symbol = '1000LUNCUSDT'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD
    user_hedge_2.websocket_symbol = '1000luncusdt'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd
    user_hedge_2.trade_currency = 'USDT'  # 交易货币  USDT  BUSD

    logger.info("开始初始化交易所...")
    ba.init_exchange(user_main_1, user_hedge_1)
    ba.init_exchange(user_main_2, user_hedge_2)
    logger.info("交易所初始化完毕,开始获取用户token...")
    ba.get_token(user_main_1, user_hedge_1)
    ba.get_token(user_main_2, user_hedge_2)
    ba.获取交易对规则2(user_main_1, user_hedge_1)
    ba.获取交易对规则2(user_main_2, user_hedge_2)
    user_main_1.交易对价格精度 = 4
    user_hedge_1.交易对价格精度 = 4
    user_main_2.交易对价格精度 = 4
    user_hedge_2.交易对价格精度 = 4
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
    while True:
        if user_main_1.初始化完成 and (not user_main_1.任务队列.empty()):
            orderid = user_main_1.任务队列.get()
            Account.executor.submit(lambda p: 处理任务(*p), (user_main_1, orderid))
        if user_main_2.初始化完成 and (not user_main_2.任务队列.empty()):
            orderid = user_main_2.任务队列.get()
            Account.executor.submit(lambda p: 处理任务(*p), (user_main_2, orderid))
        if user_hedge_1.初始化完成 and (not user_hedge_1.任务队列.empty()):
            orderid = user_hedge_1.任务队列.get()
            Account.executor.submit(lambda p: 处理任务(*p), (user_hedge_1, orderid))
        if user_hedge_2.初始化完成 and (not user_hedge_2.任务队列.empty()):
            orderid = user_hedge_2.任务队列.get()
            Account.executor.submit(lambda p: 处理任务(*p), (user_hedge_2, orderid))
    # if user_main.need_sign:
    #     logger.info("需要信号开单，开启启动webhooks...")
    #     webhook = Webhooks(user_main, user_hedge)
    #     webhook.run()
