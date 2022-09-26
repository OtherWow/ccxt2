from gridWebsocket import PublicGridWebSocket, PrivateGridWebSocket
from loguru import logger
from binance import binance as ba
from user.account import Account
import time
import gridBot

if __name__ == '__main__':
    trace = logger.add("log/log.log", rotation="00:00")  # 每天0点创建新文件
    trace2 = logger.add("log/info.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    # # ====================================网格1参数设置===================================
    # user_main = Account("syb")
    # user_main.position_side = 'LONG'  # 做多
    # user_main.网格区间上限 = 1375
    # user_main.网格区间下限 = 1275
    # user_main.网格限价止损价格 = 1274.99
    # user_main.网格市价止损价格 = 1274.98
    # user_main.网格数量 = 70
    # user_main.单网格数量 = 0.005
    # # ====================================网格2参数设置===================================
    # user_hedge = Account("cx")
    # user_hedge.position_side = 'SHORT'  # 做空
    # user_hedge.网格区间上限 = 1400
    # user_hedge.网格区间下限 = 1200
    # user_hedge.网格限价止损价格 = 1400.01
    # user_hedge.网格市价止损价格 = 1400.02
    # user_hedge.网格数量 = 400
    # user_hedge.单网格数量 = 20

    # ====================================网格1参数设置===================================
    user_main_1 = Account("yyn_big")
    user_main_1.symbol = 'ETHBUSD'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD
    user_main_1.websocket_symbol = 'ethbusd'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd
    user_main_1.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD
    user_main_1.position_side = 'LONG'  # 做多
    user_main_1.网格区间上限 = 1510
    user_main_1.网格区间下限 = 1190
    user_main_1.网格限价止损价格 = 1189.8
    user_main_1.网格市价止损价格 = 1189.7
    user_main_1.网格数量 = 396
    user_main_1.单网格数量 = 0.022
    # ====================================网格2参数设置===================================
    user_hedge_1 = Account("yyn_small")
    user_hedge_1.symbol = 'ETHBUSD'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD
    user_hedge_1.websocket_symbol = 'ethbusd'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd
    user_hedge_1.trade_currency = 'BUSD'  # 交易货币  USDT  BUSD
    user_hedge_1.position_side = 'SHORT'  # 做空
    user_hedge_1.网格区间上限 = 1510
    user_hedge_1.网格区间下限 = 1190
    user_hedge_1.网格限价止损价格 = 1510.05
    user_hedge_1.网格市价止损价格 = 1510.06
    user_hedge_1.网格数量 = 396
    user_hedge_1.单网格数量 = 0.022
    # ====================================网格3参数设置===================================
    user_main_2 = Account("yyn_big")
    user_main_2.symbol = 'ETHUSDT'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD
    user_main_2.websocket_symbol = 'ethusdt'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd
    user_main_2.trade_currency = 'USDT'  # 交易货币  USDT  BUSD
    user_main_2.position_side = 'LONG'  # 做多
    user_main_2.网格区间上限 = 1510
    user_main_2.网格区间下限 = 1190
    user_main_2.网格限价止损价格 = 1189.8
    user_main_2.网格市价止损价格 = 1189.7
    user_main_2.网格数量 = 396
    user_main_2.单网格数量 = 0.022
    # ====================================网格4参数设置===================================
    user_hedge_2 = Account("yyn_small")
    user_hedge_1.symbol = 'ETHUSDT'  # 交易对  LUNA2BUSD   ETHUSDT  1000LUNCBUSD   ETHBUSD
    user_hedge_1.websocket_symbol = 'ethusdt'  # 交易对  luna2busd   ethusdt    1000luncbusd   ethbusd
    user_hedge_1.trade_currency = 'USDT'  # 交易货币  USDT  BUSD
    user_hedge_2.position_side = 'SHORT'  # 做空
    user_hedge_2.网格区间上限 = 1510
    user_hedge_2.网格区间下限 = 1190
    user_hedge_2.网格限价止损价格 = 1510.05
    user_hedge_2.网格市价止损价格 = 1510.06
    user_hedge_2.网格数量 = 396
    user_hedge_2.单网格数量 = 0.022

    logger.info("开始初始化交易所...")
    ba.init_exchange(user_main_1, user_hedge_1)
    ba.init_exchange(user_main_2, user_hedge_2)
    logger.info("交易所初始化完毕,开始获取用户token...")
    ba.get_token(user_main_1, user_hedge_1)
    ba.get_token(user_main_2, user_hedge_2)
    ba.获取交易对规则2(user_main_1, user_hedge_1)
    ba.获取交易对规则2(user_main_2, user_hedge_2)
    # user_main.交易对价格精度 = 4
    # user_hedge.交易对价格精度 = 4
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    pub = PublicGridWebSocket(user_main_1, user_hedge_1)
    pub = PublicGridWebSocket(user_main_2, user_hedge_2)
    pub.run()
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    pri = PrivateGridWebSocket(user_main_1, user_hedge_1,user_main_2,user_hedge_2)
    pri.run()
    logger.info("私有化线程启动完毕,进入task...")
    time.sleep(4)
    # gridBot.创建网格(user_main)
    # ba.限价单(user_main, 30,0.18, 'BUY')
    # ba.限价单(user_main, 30,0.1802, 'BUY')
    # ba.限价单(user_main, 30,0.1804, 'BUY')

    gridBot.创建网格2(user_main, user_hedge)
    # if user_main.need_sign:
    #     logger.info("需要信号开单，开启启动webhooks...")
    #     webhook = Webhooks(user_main, user_hedge)
    #     webhook.run()
