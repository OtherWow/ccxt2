import time
from loguru import logger
from binance import binance as ba
from user.account import Account


class Grid(object):
    def __init__(self):
        self.此网格上边界价格 = 0
        self.此网格下边界价格 = 0
        self.此网格数量 = 0
        self.此网格订单号 = ""
        self.此网格持仓数量 = 0
        self.网格名称 = ""
        self.订单方向 = ""


def 创建网格2(user_main: Account, user_hedge: Account):
    ba.撤销所有订单(user_main)
    ba.撤销所有订单(user_hedge)
    ba.查询账户持仓情况(user_main)
    ba.查询账户持仓情况(user_hedge)
    if user_main.position_amt != 0:
        logger.info(f"{user_main.name}账户有持仓，无法创建网格")
        return
    if user_hedge.position_amt != 0:
        logger.info(f"{user_hedge.name}账户有持仓，无法创建网格")
        return

    网格初始化2(user_main, user_hedge)
    if user_main.position_side == "LONG":  # 做多
        触发价 = user_main.网格限价止损价格 / (1 - user_main.价格保护百分比 / 2)
        数量 = user_main.网格数量 * user_main.单网格数量
        ba.限价止损单自填数量(user_main, 触发价, user_main.网格限价止损价格, 数量)
        ba.市价止损单(user_main, user_main.网格市价止损价格)

        触发价 = user_hedge.网格限价止损价格 / (1 + user_hedge.价格保护百分比 / 2)
        数量 = user_hedge.网格数量 * user_hedge.单网格数量
        ba.限价止损单自填数量(user_hedge, 触发价, user_hedge.网格限价止损价格, 数量)
        ba.市价止损单(user_hedge, user_hedge.网格区间上限)

    elif user_main.position_side == "SHORT":  # 做空
        触发价 = user_main.网格限价止损价格 / (1 + user_main.价格保护百分比 / 2)
        数量 = user_main.网格数量 * user_main.单网格数量
        ba.限价止损单自填数量(user_main, 触发价, user_main.网格限价止损价格, 数量)
        ba.市价止损单(user_main, user_main.网格区间上限)

        触发价 = user_hedge.网格限价止损价格 / (1 - user_hedge.价格保护百分比 / 2)
        数量 = user_hedge.网格数量 * user_hedge.单网格数量
        ba.限价止损单自填数量(user_hedge, 触发价, user_hedge.网格限价止损价格, 数量)
        ba.市价止损单(user_hedge, user_hedge.网格市价止损价格)

    logger.info(
        f"{user_main.name}创建网格成功，网格区间【{user_main.网格区间下限}，{user_main.网格区间上限}】，网格数量{user_main.网格数量}，单网格数量{user_main.单网格数量}，网格限价止损价格{user_main.网格限价止损价格}，网格市价止损价格{user_main.网格市价止损价格}")
    logger.info(
        f"{user_hedge.name}创建网格成功，网格区间【{user_hedge.网格区间下限}，{user_hedge.网格区间上限}】，网格数量{user_hedge.网格数量}，单网格数量{user_hedge.单网格数量}，网格限价止损价格{user_hedge.网格限价止损价格}，网格市价止损价格{user_hedge.网格市价止损价格}")
    return


def 网格初始化2(user_main: Account, user_hedge: Account):
    user_main.grid_list.clear()
    user_hedge.grid_list.clear()
    user_main.order_map.clear()
    user_hedge.order_map.clear()
    网格价格范围 = (user_main.网格区间上限 - user_main.网格区间下限) / user_main.网格数量
    user_main.单网格数量 = round(user_main.投入金额 * user_main.leverage / user_main.now_price / user_main.网格数量,
                            user_main.交易对数量精度)
    当前下边界价格 = user_main.网格区间下限
    for i in range(user_main.网格数量):
        grid = Grid()
        grid.此网格上边界价格 = 当前下边界价格 + 网格价格范围
        grid.此网格下边界价格 = 当前下边界价格
        grid.此网格数量 = user_main.单网格数量
        grid.网格名称 = f"{user_main.name}网格{i}"
        当前下边界价格 = 当前下边界价格 + 网格价格范围
        user_main.grid_list.append(grid)

    网格价格范围 = (user_hedge.网格区间上限 - user_hedge.网格区间下限) / user_hedge.网格数量
    user_hedge.单网格数量 = round(user_hedge.投入金额 * user_hedge.leverage / user_hedge.now_price / user_hedge.网格数量,
                             user_hedge.交易对数量精度)
    当前下边界价格 = user_hedge.网格区间下限
    for i in range(user_hedge.网格数量):
        grid = Grid()
        grid.此网格上边界价格 = 当前下边界价格 + 网格价格范围
        grid.此网格下边界价格 = 当前下边界价格
        grid.此网格数量 = user_hedge.单网格数量
        grid.网格名称 = f"{user_hedge.name}网格{i}"
        当前下边界价格 = 当前下边界价格 + 网格价格范围
        user_hedge.grid_list.append(grid)
    校验网格2(user_main, user_hedge)
    user_main.初始化完成 = True
    user_hedge.初始化完成 = True
    return


def 校验网格2(user_main: Account, user_hedge: Account):
    main_市价单方向 = ""
    hedge_市价单方向 = ""
    main_市价单数量 = 0
    hedge_市价单数量 = 0
    网络间隔 = 0.03

    for i in range(0, len(user_main.grid_list)):
        grid = user_main.grid_list[i].此网格数量
        grid2 = user_hedge.grid_list[i].此网格数量
        if grid.此网格订单号 == "":
            if user_main.position_side == "LONG":  # 做多
                if user_main.now_price <= grid.此网格下边界价格:
                    if user_main.position_amt == 0:
                        ba.市价单(user_main, grid.此网格数量, "BUY")
                        ba.查询账户持仓情况(user_main)
                    else:
                        main_市价单数量 += grid.此网格数量
                        main_市价单方向 = "BUY"
                    ba.限价单(user_main, grid.此网格数量, grid.此网格上边界价格, "SELL")
                    grid.订单方向 = "SELL"
                else:
                    ba.限价单(user_main, grid.此网格数量, grid.此网格下边界价格, "BUY")
                    grid.订单方向 = "BUY"
                time.sleep(网络间隔)

                if user_hedge.now_price >= grid2.此网格上边界价格:
                    if user_hedge.position_amt == 0:
                        ba.市价单(user_hedge, grid2.此网格数量, "SELL")
                    else:
                        hedge_市价单数量 += grid2.此网格数量
                        hedge_市价单方向 = "SELL"
                    ba.限价单(user_hedge, grid2.此网格数量, grid2.此网格下边界价格, "BUY")
                    grid2.订单方向 = "BUY"
                else:
                    ba.限价单(user_hedge, grid2.此网格数量, grid2.此网格上边界价格, "SELL")
                    grid2.订单方向 = "SELL"
                time.sleep(网络间隔)

            elif user_main.position_side == "SHORT":  # 做空
                if user_main.now_price >= grid.此网格上边界价格:
                    if user_main.position_amt == 0:
                        ba.市价单(user_main, grid.此网格数量, "SELL")
                    else:
                        main_市价单数量 += grid.此网格数量
                        main_市价单方向 = "SELL"
                    ba.限价单(user_main, grid.此网格数量, grid.此网格下边界价格, "BUY")
                    grid.订单方向 = "BUY"
                else:
                    ba.限价单(user_main, grid.此网格数量, grid.此网格上边界价格, "SELL")
                    grid.订单方向 = "SELL"
                time.sleep(网络间隔)

                if user_hedge.now_price <= grid2.此网格下边界价格:
                    if user_hedge.position_amt == 0:
                        ba.市价单(user_hedge, grid2.此网格数量, "BUY")
                        ba.查询账户持仓情况(user_hedge)
                    else:
                        hedge_市价单数量 += grid2.此网格数量
                        hedge_市价单数量 = "BUY"
                    ba.限价单(user_hedge, grid2.此网格数量, grid2.此网格上边界价格, "SELL")
                    grid2.订单方向 = "SELL"
                else:
                    ba.限价单(user_hedge, grid2.此网格数量, grid2.此网格下边界价格, "BUY")
                    grid2.订单方向 = "BUY"
                time.sleep(网络间隔)
            else:
                logger.info(f"{user_main.name} 请先设置持仓方向！")
                return
            grid.此网格订单号 = user_main.order_info['orderId']
            grid2.此网格订单号 = user_hedge.order_info['orderId']
            user_main.order_map[user_main.order_info['orderId']] = grid
            user_hedge.order_map[user_hedge.order_info['orderId']] = grid2
            logger.info(
                f"{grid.网格名称}挂单成功，订单号：{grid.此网格订单号}，价格：{user_main.order_info['price']}，数量：{user_main.order_info['origQty']}，方向：{user_main.order_info['side']}")
            logger.info(
                f"{grid2.网格名称}挂单成功，订单号：{grid2.此网格订单号}，价格：{user_hedge.order_info['price']}，数量：{user_hedge.order_info['origQty']}，方向：{user_hedge.order_info['side']}")
    if main_市价单数量 != 0:
        ba.市价单(user_main, main_市价单数量, main_市价单方向)
    if hedge_市价单数量 != 0:
        ba.市价单(user_hedge, hedge_市价单数量, hedge_市价单方向)


def 创建网格(user: Account):
    ba.撤销所有订单(user)
    ba.查询账户持仓情况(user)
    if user.position_amt != 0:
        logger.info(f"{user.name}账户有持仓，无法创建网格")
        return
    网格初始化(user)
    if user.position_side == "LONG":  # 做多
        触发价 = user.网格限价止损价格 / (1 - user.价格保护百分比 / 2)
        数量 = user.网格数量 * user.单网格数量
        ba.限价止损单自填数量(user, 触发价, user.网格限价止损价格, 数量)
        ba.市价止损单(user, user.网格市价止损价格)
    elif user.position_side == "SHORT":  # 做空
        触发价 = user.网格限价止损价格 / (1 + user.价格保护百分比 / 2)
        数量 = user.网格数量 * user.单网格数量
        ba.限价止损单自填数量(user, 触发价, user.网格限价止损价格, 数量)
        ba.市价止损单(user, user.网格区间上限)
    logger.info(
        f"{user.name}创建网格成功，网格区间【{user.网格区间下限}，{user.网格区间上限}】，网格数量{user.网格数量}，单网格数量{user.单网格数量}，网格限价止损价格{user.网格限价止损价格}，网格市价止损价格{user.网格市价止损价格}")
    return


def 网格初始化(user: Account):
    user.grid_list.clear()
    user.order_map.clear()
    网格价格范围 = (user.网格区间上限 - user.网格区间下限) / user.网格数量
    user.单网格数量 = round(user.投入金额 * user.leverage / user.now_price / user.网格数量, user.交易对数量精度)
    当前下边界价格 = user.网格区间下限
    for i in range(user.网格数量):
        grid = Grid()
        grid.此网格上边界价格 = 当前下边界价格 + 网格价格范围
        grid.此网格下边界价格 = 当前下边界价格
        grid.此网格数量 = user.单网格数量
        grid.网格名称 = f"{user.name}网格{i}"
        当前下边界价格 = 当前下边界价格 + 网格价格范围
        user.grid_list.append(grid)
    校验网格(user)
    user.初始化完成 = True
    return


def 校验网格(user: Account):
    市价单方向 = ""
    市价单数量 = 0
    网络间隔 = 0.03
    for grid in user.grid_list:
        if grid.此网格订单号 == "":
            if user.position_side == "LONG":  # 做多
                if user.now_price <= grid.此网格下边界价格:
                    if user.position_amt == 0:
                        ba.市价单(user, grid.此网格数量, "BUY")
                        ba.查询账户持仓情况(user)
                    else:
                        市价单数量 += grid.此网格数量
                        市价单方向 = "BUY"
                    ba.限价单(user, grid.此网格数量, grid.此网格上边界价格, "SELL")
                    grid.订单方向 = "SELL"
                else:
                    ba.限价单(user, grid.此网格数量, grid.此网格下边界价格, "BUY")
                    grid.订单方向 = "BUY"
                time.sleep(网络间隔)
            elif user.position_side == "SHORT":  # 做空
                if user.now_price >= grid.此网格上边界价格:
                    if user.position_amt == 0:
                        ba.市价单(user, grid.此网格数量, "SELL")
                    else:
                        市价单数量 += grid.此网格数量
                        市价单方向 = "SELL"
                    ba.限价单(user, grid.此网格数量, grid.此网格下边界价格, "BUY")
                    grid.订单方向 = "BUY"
                else:
                    ba.限价单(user, grid.此网格数量, grid.此网格上边界价格, "SELL")
                    grid.订单方向 = "SELL"
                time.sleep(网络间隔)
            else:
                logger.info(f"{user.name} 请先设置持仓方向！")
                return
            grid.此网格订单号 = user.order_info['orderId']
            user.order_map[user.order_info['orderId']] = grid
            logger.info(
                f"{grid.网格名称}挂单成功，订单号：{grid.此网格订单号}，价格：{user.order_info['price']}，数量：{user.order_info['origQty']}，方向：{user.order_info['side']}")
    if 市价单数量 != 0:
        ba.市价单(user, 市价单数量, 市价单方向)
