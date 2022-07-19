from account import Account
from loguru import logger
import mading
import threading
from mywebsocket import PublicWebSocket, PrivateWebSocket

if __name__ == '__main__':
    trace = logger.add("log/log.log", level="INFO", rotation="00:00")  # 每天0点创建新文件
    user_main = Account("syb")
    user_hedge = Account("cx")
    logger.info("开始初始化交易所...")
    mading.init_exchange(user_main, user_hedge)
    logger.info("交易所初始化完毕,开始获取用户token...")
    mading.get_token(user_main, user_hedge)
    logger.info("获取用户token完毕,开始启动公有化线程获取用户交易对信息...")
    threading.Thread(target=PublicWebSocket, args={user_main}).start()  # 创建线程
    threading.Thread(target=PublicWebSocket, args={user_hedge}).start()  # 创建线程
    logger.info("公有化线程启动完毕,开始启动私有化线程获取用户交易信息...")
    threading.Thread(target=PrivateWebSocket, args={user_main}).start()  # 创建线程
    threading.Thread(target=PrivateWebSocket, args={user_hedge}).start()  # 创建线程
    logger.info("私有化线程启动完毕,进入task...")

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
