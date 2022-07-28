import time

from loguru import logger

import mading
from account import Account
from mywebsocket import PublicWebSocket, PrivateWebSocket,Webhooks

if __name__ == '__main__':
    trace = logger.add("log/log.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    user_main = Account("yyn_big")
    user_hedge = Account("yyn_small")
    user_hedge.止盈相当于首单 = True
    user_hedge.止盈百分比 = 105.4
    user_hedge.止损相当于首单 = True
    user_hedge.止损百分比 = 0.2
    if user_main.position_side == 'SHORT':
        user_hedge.position_side = 'LONG'
    else:
        user_hedge.position_side = 'SHORT'
    logger.info("开始初始化交易所...")
    mading.init_exchange(user_main, user_hedge)
    # # a = mading.获取交易对规则(user_main)
    logger.info("交易所初始化完毕,开始获取用户token...")
    mading.get_token(user_main, user_hedge)
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    # pub = PublicWebSocket(user_main, user_hedge)
    # pub.run()
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    # pri = PrivateWebSocket(user_main, user_hedge)
    # pri.run()
    logger.info("私有化线程启动完毕,进入task...")
    if user_main.need_sign:
        webhook = Webhooks(user_main, user_hedge)
        webhook.run()
    time.sleep(3)
    # mading.trade_task(user_main, user_hedge)
    # if d.right_now_order:
    #     撤销所有订单()
    #     time.sleep(5)
    #     data = {
    #         "type": "sell",
    #         "timestamp": 431115,
    #     }
    #     trade(data)
    # if d.need_sign:
    #     threading.Thread(target=init_webhooks()).start()  # 创建线程
    mading.查询账户持仓情况(user_main)
    # mading.查询当前所有挂单(user_main)
    # mading.市价单(user_main,3,"SELL")
    # mading.限价单(user_main,6,1,"BUY")
    # mading.限价单(user_main,6,10,"BUY")
    # mading.限价单(user_main,3,21,"SELL")
    # mading.限价单(user_main,3,2.2,"SELL")

    # user_main.限价单订单簿.append(1212539485)
    # user_main.限价单订单簿.append(1212539526)
    # user_main.限价单订单簿.append(1212539550)
    # user_main.限价单订单簿.append(1212545933)
    # logger.debug("限价单订单簿: {}".format(user_main.限价单订单簿))
    # mading.市价平仓(user_main)
    # mading.撤销所有订单(user_main)
    # mading.批量撤销订单(user_main,user_main.限价单订单簿)
    mading.查询当前所有挂单(user_main)
    #[1212212129]