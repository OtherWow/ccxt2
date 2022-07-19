import time

from account import Account
from loguru import logger
import mading
import threading
from mywebsocket import PublicWebSocket, PrivateWebSocket

if __name__ == '__main__':
    trace = logger.add("log/log.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    user_main = Account("cx")
    user_main.止损总金额 = 10.0
    user_main.止盈总金额 = 1.0
    user_hedge = Account("syb")
    user_hedge.止损总金额 = user_main.止盈总金额
    user_hedge.止盈总金额 = user_main.止损总金额
    if user_main.position_side == 'SHORT':
        user_hedge.position_side = 'LONG'
    else:
        user_hedge.position_side = 'SHORT'
    logger.info("开始初始化交易所...")
    mading.init_exchange(user_main, user_hedge)
    # a = mading.获取交易对规则(user_main)
    logger.info("交易所初始化完毕,开始获取用户token...")
    mading.get_token(user_main, user_hedge)
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    pub = PublicWebSocket(user_main, user_hedge)
    pub.run()
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    pri = PrivateWebSocket(user_main, user_hedge)
    pri.run()
    logger.info("私有化线程启动完毕,进入task...")
    time.sleep(3)
    mading.trade_task(user_main, user_hedge)
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
