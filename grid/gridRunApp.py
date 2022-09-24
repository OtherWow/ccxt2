from gridWebsocket import PublicGridWebSocket, PrivateGridWebSocket
from loguru import logger
from binance import binance as ba
from user.account import Account
import time
import gridBot

if __name__ == '__main__':
    trace = logger.add("log/log.log", rotation="00:00")  # 每天0点创建新文件
    trace2 = logger.add("log/info.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    # ====================================网格1参数设置===================================
    user_main = Account("syb")
    user_main.position_side = 'LONG'  # 做多
    user_main.投入金额 = 25
    user_main.网格区间上限 = 1375
    user_main.网格区间下限 = 1275
    user_main.网格限价止损价格 = 1274.99
    user_main.网格市价止损价格 = 1274.98
    user_main.网格数量 = 80
    # ====================================网格2参数设置===================================
    user_hedge = Account("cx")
    user_hedge.position_side = 'SHORT'  # 做空
    user_hedge.投入金额 = 10
    user_hedge.网格区间上限 = 1400
    user_hedge.网格区间下限 = 1200
    user_hedge.网格限价止损价格 = 1400.01
    user_hedge.网格市价止损价格 = 1400.02
    user_hedge.网格数量 = 10

    logger.info("开始初始化交易所...")
    ba.init_exchange(user_main, user_hedge)
    logger.info("交易所初始化完毕,开始获取用户token...")
    ba.get_token(user_main, user_hedge)
    ba.获取交易对规则2(user_main, user_hedge)
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    pub = PublicGridWebSocket(user_main, user_hedge)
    pub.run()
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    pri = PrivateGridWebSocket(user_main, user_hedge)
    pri.run()
    logger.info("私有化线程启动完毕,进入task...")
    time.sleep(2)
    gridBot.创建网格(user_main)
    # if user_main.need_sign:
    #     logger.info("需要信号开单，开启启动webhooks...")
    #     webhook = Webhooks(user_main, user_hedge)
    #     webhook.run()
