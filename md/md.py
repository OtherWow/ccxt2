import time
from loguru import logger
from user.account import Account
from binance import binance as ba


# 先下对冲单，对冲单根据信号开单
def sign1(sign_data, user_main: Account, user_hedge: Account):
    # 根据信号开仓
    ba.查询账户持仓情况(user_main)
    ba.查询账户持仓情况(user_hedge)
    if user_main.position_amt > 0 or user_hedge.position_amt > 0:
        logger.info("收到信号" + str(sign_data['type']) + ",但是主账户已持仓" + str(user_main.position_amt) + " 或 对冲单已持仓" + str(
            user_hedge.position_amt) + "，忽略本次信号。对冲单持仓数量：" + str(
            user_hedge.position_amt) + " 对冲单持仓价格：" + str(user_hedge.entry_price) + " 当前价格：" + str(user_hedge.now_price))
        return
    # 对冲单开首单
    if sign_data['type'] == 'sell':
        logger.info(user_hedge.name + "收到信号" + str(sign_data['type']) + "对冲单开始做空开仓 当前价格：" + str(user_hedge.now_price))
        user_hedge.position_side = 'SHORT'
        user_main.position_side = 'LONG'
        ba.撤销所有订单(user_hedge)
        ba.市价单(user_hedge, user_hedge.首单数量, "SELL")
        time.sleep(2)
        ba.查询账户持仓情况(user_hedge)
        user_hedge.首单价值 = user_hedge.position_amt * user_hedge.entry_price
        user_main.马丁触发价格 = user_hedge.entry_price * (1 - user_hedge.对冲单价格变动百分比触发马丁)
        止盈止损单(user_hedge)
        logger.info(user_hedge.name + "对冲单已做空开仓 持仓数量：" + str(
            user_hedge.position_amt) + " 持仓价格：" + str(user_hedge.entry_price) + " 对冲单首单价值：" + str(
            user_hedge.首单价值) + "马丁触发价格：" + str(user_main.马丁触发价格))
        return

    elif sign_data['type'] == 'buy':
        logger.info(user_hedge.name + "收到信号" + str(sign_data['type']) + "对冲单开始做多开仓 当前价格：" + str(user_hedge.now_price))
        user_hedge.position_side = 'LONG'
        user_main.position_side = 'SHORT'
        ba.撤销所有订单(user_hedge)
        ba.市价单(user_hedge, user_hedge.首单数量, "BUY")
        time.sleep(2)
        ba.查询账户持仓情况(user_hedge)
        user_hedge.首单价值 = user_hedge.position_amt * user_hedge.entry_price
        user_main.马丁触发价格 = user_hedge.entry_price * (1 + user_hedge.对冲单价格变动百分比触发马丁)
        止盈止损单(user_hedge)
        logger.info(user_hedge.name + "对冲单已做多开仓 持仓数量：" + str(
            user_hedge.position_amt) + " 持仓价格：" + str(user_hedge.entry_price) + " 对冲单首单价值：" + str(
            user_hedge.首单价值) + "马丁触发价格：" + str(user_main.马丁触发价格))
        return


def 马丁开首单(user_main: Account, user_hedge: Account):
    ba.查询账户持仓情况(user_main)
    ba.查询账户持仓情况(user_hedge)
    if user_main.position_amt == 0 and user_hedge.position_amt > 0:
        user_main.马丁触发价格 = 0
        ba.撤销所有订单(user_main)
        if user_main.position_side == 'SHORT':
            ba.市价单(user_main, user_main.首单数量, 'SELL')
        if user_main.position_side == 'LONG':
            ba.市价单(user_main, user_main.首单数量, 'BUY')
        time.sleep(2)
        ba.查询账户持仓情况(user_main)
        user_main.首单价值 = user_main.position_amt * user_main.entry_price
        止盈止损单(user_main)
        ba.查询账户持仓情况(user_hedge)
        logger.debug("开始下对冲但止盈单,触发价:" + str(user_main.对冲单平仓触发价) + "委托价:" + str(user_main.对冲单平仓委托价) + " 当前价格：" + str(
            user_hedge.now_price) + " 仓位价格：" + str(user_hedge.entry_price))
        try:
            ba.限价止盈单(user_hedge, (user_hedge.now_price + user_main.对冲单平仓委托价) / 2, user_main.对冲单平仓委托价)
        except Exception as e:
            logger.error(user_hedge.name + "限价止盈单异常:" + str(e))

        ba.查询账户持仓情况(user_main)
        # 开始循环下限价单
        if user_main.position_side == 'SHORT':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 + last_percent)
                try:
                    ba.限价单(user_main, num, price, 'SELL')
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + str(e) + " 价格：" + str(price) + " 数量：" + str(
                            num))
                num = num * user_main.补仓倍数
        if user_main.position_side == 'LONG':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 - last_percent)
                try:
                    ba.限价单(user_main, num, price, 'BUY')
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + str(e) + " 价格：" + str(price) + " 数量：" + str(
                            num))
                num = num * user_main.补仓倍数
    else:
        user_main.马丁触发价格 = 0
        return


@logger.catch()
def 双马丁策略(user_main: Account, user_hedge: Account):
    ba.查询账户持仓情况(user_main)
    ba.查询账户持仓情况(user_hedge)
    if user_hedge.position_amt > 0:
        ba.市价平仓(user_hedge)
        time.sleep(2)
        ba.查询账户持仓情况(user_hedge)
    if user_main.position_amt == 0 and user_hedge.position_amt == 0:
        ba.撤销所有订单(user_main)
        ba.撤销所有订单(user_hedge)
        user_main.马丁补单当前索引 = 0
        user_main.马丁补单单号字典 = {}
        if user_main.position_side == 'SHORT':
            ba.市价单(user_main, user_main.首单数量, 'SELL')
        if user_main.position_side == 'LONG':
            ba.市价单(user_main, user_main.首单数量, 'BUY')
        time.sleep(2)
        ba.查询账户持仓情况(user_main)
        user_main.首单价值 = user_main.position_amt * user_main.entry_price
        止盈止损单(user_main)
        # 开始循环下限价单
        if user_main.position_side == 'SHORT':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 + last_percent)
                try:
                    ba.限价单(user_main, num, price, 'SELL')
                    user_main.马丁补单单号字典[i] = user_main.order_info['orderId']
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user_main.补仓倍数
        if user_main.position_side == 'LONG':
            num = user_main.首次补仓数量
            last_percent = 0
            for i in range(user_main.最大补仓次数):
                last_percent = user_main.补仓价格百分比例 / 100 + last_percent * user_main.补仓价格倍数
                price = user_main.entry_price * (1 - last_percent)
                try:
                    ba.限价单(user_main, num, price, 'BUY')
                    user_main.马丁补单单号字典[i] = user_main.order_info['orderId']
                except Exception as e:
                    logger.error(
                        user_main.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user_main.补仓倍数
    else:
        logger.info(user_main.name + " 持仓数量：" + str(user_main.position_amt) + " 持仓价格：" + str(
            user_main.entry_price) + "=】【=" + user_hedge.name + " 持仓数量：" + str(
            user_hedge.position_amt) + " 持仓价格：" + str(user_hedge.entry_price) + " 仓位不为0,无法开单")


def 对冲马丁(user: Account):
    ba.查询账户持仓情况(user)
    if user.position_amt == 0:
        ba.撤销所有订单(user)
        if user.position_side == 'SHORT':
            ba.市价单(user, user.首单数量, 'SELL')
        if user.position_side == 'LONG':
            ba.市价单(user, user.首单数量, 'BUY')
        time.sleep(2)
        ba.查询账户持仓情况(user)
        user.首单价值 = user.position_amt * user.entry_price
        止盈止损单(user)
        # 开始循环下限价单
        if user.position_side == 'SHORT':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 + last_percent)
                try:
                    ba.限价单(user, num, price, 'SELL')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
        if user.position_side == 'LONG':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 - last_percent)
                try:
                    ba.限价单(user, num, price, 'BUY')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
    else:
        logger.info(user.name + "账户持仓不为0,无法开单，持仓数量:" + str(user.position_amt) + " 持仓价格:" + str(user.entry_price))
        return


def 马丁(user: Account):
    ba.查询账户持仓情况(user)
    if user.position_amt == 0:
        ba.撤销所有订单(user)
        if user.position_side == 'SHORT':
            ba.市价单(user, user.首单数量, 'SELL')
        if user.position_side == 'LONG':
            ba.市价单(user, user.首单数量, 'BUY')
        time.sleep(2)
        ba.查询账户持仓情况(user)
        user.首单价值 = user.position_amt * user.entry_price
        止盈止损单(user)
        # 开始循环下限价单
        if user.position_side == 'SHORT':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 + last_percent)
                try:
                    ba.限价单(user, num, price, 'SELL')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
        if user.position_side == 'LONG':
            num = user.首次补仓数量
            last_percent = 0
            for i in range(user.最大补仓次数):
                last_percent = user.补仓价格百分比例 / 100 + last_percent * user.补仓价格倍数
                price = user.entry_price * (1 - last_percent)
                try:
                    限价单(user, num, price, 'BUY')
                except Exception as e:
                    logger.error(
                        user.name + "第{}次限价单下单出错 ".format(i + 1) + " 价格：" + str(price) + " 数量：" + str(
                            num) + str(e))
                num = num * user.补仓倍数
    else:
        logger.info(user.name + "账户持仓不为0,无法开单，持仓数量:" + str(user.position_amt) + " 持仓价格:" + str(user.entry_price))
        return


@logger.catch()
def 止盈止损单(user: Account):
    ba.查询账户持仓情况(user)
    try:
        ba.批量撤销订单(user, user.止盈止损订单簿)
        user.止盈止损订单簿 = []
    except Exception as e:
        logger.error(user.name + '撤销止盈止损单失败!' + str(e))
    委托价 = 0.0
    触发价 = 0.0
    if user.position_amt > 0:
        if user.开启止损:
            止损百分比 = 0.0
            if user.position_amt == user.首单数量:
                止损百分比 = user.首单止损百分比
            else:
                止损百分比 = user.止损百分比
            if user.止损类型 == 1:  # 0 固定金额止损  1 百分比止损
                if user.止损相对于首单:
                    user.止损总金额 = (止损百分比 / 100) * user.首单价值
                else:
                    user.止损总金额 = (止损百分比 / 100) * (user.position_amt * user.entry_price)
            # =============================计算止损价格==================================
            if user.position_side == 'SHORT':
                # 做空时的止损价格计算： （当前价格-仓位价格+0.0006*当前价格）仓位数量 = 预估损失
                委托价 = (user.止损总金额 / user.position_amt + user.entry_price) / (1 + user.限价手续费率 + user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            if user.position_side == 'LONG':
                # 做多时的止损价格计算： （仓位价格-当前价格+0.0006*当前价格）仓位数量 = 预估损失
                委托价 = (user.entry_price - user.止损总金额 / user.position_amt) / (1 - user.限价手续费率 - user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            try:
                ba.限价止损单(user, 触发价, 委托价)
            except Exception as e:
                logger.error(user.name + "限价止损单发送失败！开始下市价止损单！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
                    user.now_price) + " 首单价值：" + str(user.首单价值) + str(e))
                ba.市价止损单(user, 委托价)
            user.止盈止损订单簿.append(user.order_info['orderId'])
            user.止损单号 = user.order_info['orderId']
            logger.info(user.name + "下单标记止损单,止损价格：{:.4f}".format(委托价) + " 预估损失：" + str(
                user.止损总金额) + " 当前仓位价格： {:.4f}".format(
                user.entry_price) + " 当前仓位数量：{:.4f}".format(user.position_amt))
        if user.开启止盈:
            止盈百分比 = 0.0
            if user.position_amt == user.首单数量:
                止盈百分比 = user.首单止盈百分比
            else:
                止盈百分比 = user.止盈百分比
            if user.止盈类型 == 1:  # 0 固定金额止盈  1 百分比止盈
                if user.止盈相对于首单:
                    user.止盈总金额 = (止盈百分比 / 100) * user.首单价值
                else:
                    user.止盈总金额 = (止盈百分比 / 100) * (user.position_amt * user.entry_price)
            # =============================计算止盈价格==================================
            if user.position_side == 'SHORT':
                # 做空时的止盈价格计算： （仓位价格-当前价格-0.0006*当前价格）仓位数量 = 预估盈利
                委托价 = (user.entry_price - user.止盈总金额 / user.position_amt) / (1 + user.限价手续费率 + user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            if user.position_side == 'LONG':
                # 做多时的止盈价格计算： （当前价格-仓位价格-0.0006*当前价格）仓位数量 = 预估损失
                委托价 = (user.止盈总金额 / user.position_amt + user.entry_price) / (1 - user.限价手续费率 - user.市价手续费率)
                触发价 = (委托价 + user.now_price) / 2
            try:
                user.对冲单平仓委托价 = 委托价
                user.对冲单平仓触发价 = 触发价
                ba.限价止盈单(user, 触发价, 委托价)
            except Exception as e:
                logger.error(user.name + "限价止盈单发送失败！开始下市价止盈单！触发价:" + str(触发价) + " 委托价：" + str(委托价) + " 当前价格:" + str(
                    user.now_price) + " 首单价值：" + str(user.首单价值) + str(e))
                ba.市价止盈单(user, 委托价)
            user.止盈止损订单簿.append(user.order_info['orderId'])
            user.止盈单号 = user.order_info['orderId']
            logger.info(
                user.name + "已下单标记止盈单,止盈价格：{:.4f}".format(委托价) + " 预估盈利：" + str(
                    user.止盈总金额) + " 当前仓位价格： {:.4f}".format(
                    user.entry_price) + " 当前仓位数量：{:.4f}".format(user.position_amt))
