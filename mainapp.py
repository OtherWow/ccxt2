import time

from loguru import logger

import mading
from account import Account
from mywebsocket import PublicWebSocket, PrivateWebSocket,Webhooks

if __name__ == '__main__':
    trace = logger.add("log/log.log", rotation="00:00")  # 每天0点创建新文件
    trace2 = logger.add("log/info.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    user_main = Account("yyn_big")
    user_hedge = Account("yyn_small")
    user_hedge.开单价格 = 1.5365
    user_hedge.首单数量 = 3900
    # user_hedge.首单数量 = user_main.首次补仓数量*2
    # user_hedge.首次补仓数量 = user_main.首次补仓数量*1.6
    # user_hedge.对冲单价格变动百分比触发马丁 = 0.004
    # user_hedge.止盈百分比 = 5
    # user_hedge.首单止盈百分比 = 5
    # user_hedge.止损百分比 = 1.5
    # user_hedge.首单止损百分比 = 1.5
    # user_hedge.止盈相当于首单 = True
    # user_hedge.止损相当于首单 = False
    if user_main.position_side == 'SHORT':
        user_hedge.position_side = 'LONG'
    else:
        user_hedge.position_side = 'SHORT'
    logger.info("开始初始化交易所...")
    mading.init_exchange(user_main, user_hedge)
    logger.info("交易所初始化完毕,开始获取用户token...")
    mading.get_token(user_main, user_hedge)
    mading.获取交易对规则2(user_main, user_hedge)
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    pub = PublicWebSocket(user_main, user_hedge)
    pub.run()
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    pri = PrivateWebSocket(user_main, user_hedge)
    pri.run()
    logger.info("私有化线程启动完毕,进入task...")
    # time.sleep(2)
    # mading.双马丁策略(user_main, user_hedge)
    # if user_main.need_sign:
    #     logger.info("需要信号开单，开启启动webhooks...")
    #     webhook = Webhooks(user_main, user_hedge)
    #     webhook.run()

    time.sleep(2)
    mading.查询账户持仓情况(user_hedge)
    mading.查询当前所有挂单(user_hedge)
    mading.查询账户持仓情况(user_main)
    mading.查询当前所有挂单(user_main)
    #
    # mading.市价平仓(user_hedge)
    # mading.市价平仓(user_main)
    # mading.撤销所有订单(user_hedge)
    # mading.撤销所有订单(user_main)
    # user_hedge.止盈止损订单簿.append('8389765533504603620')
    # user_hedge.止盈止损订单簿.append('8389765533504604462')

    # mading.止盈止损单(user_hedge)
    # mading.批量撤销订单(user_hedge,user_hedge.止盈止损订单簿)
    # logger.info(user_hedge.止盈止损订单簿)
    # mading.查询账户持仓情况(user_hedge)
    # mading.查询当前所有挂单(user_hedge)
    # mading.查询账户持仓情况(user_main)
    # mading.查询当前所有挂单(user_main)