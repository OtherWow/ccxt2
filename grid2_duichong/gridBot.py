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


def 创建网格4(user_main_1: Account, user_main_2: Account):
    ba.撤销所有订单(user_main_1)
    ba.撤销所有订单(user_main_2)
    ba.查询账户持仓情况(user_main_1)
    ba.查询账户持仓情况(user_main_2)
    ba.市价平仓(user_main_1)
    ba.市价平仓(user_main_2)
    ba.查询账户持仓情况(user_main_1)
    ba.查询账户持仓情况(user_main_2)
    if user_main_1.position_amt != 0:
        logger.info(f"{user_main_1.name}账户有持仓，无法创建网格")
        return
    if user_main_2.position_amt != 0:
        logger.info(f"{user_main_2.name}账户有持仓，无法创建网格")
        return

    网格初始化4(user_main_1,user_main_2)
    if user_main_1.position_side == "LONG":  # 做多
        触发价 = user_main_1.网格限价止损价格 / (1 - user_main_1.价格保护百分比 / 2)
        数量 = user_main_1.网格数量 * user_main_1.单网格数量 / 2
        # ba.限价止损单自填数量(user_main_1, 触发价, user_main_1.网格限价止损价格, 数量)
        ba.市价止损单(user_main_1, user_main_1.网格市价止损价格)
        # ba.限价止损单自填数量(user_main_2, 触发价, user_main_2.网格限价止损价格, 数量)
        ba.市价止损单(user_main_2, user_main_2.网格市价止损价格)

    elif user_main_1.position_side == "SHORT":  # 做空
        触发价 = user_main_1.网格限价止损价格 / (1 + user_main_1.价格保护百分比 / 2)
        数量 = user_main_1.网格数量 * user_main_1.单网格数量 / 2
        # ba.限价止损单自填数量(user_main_1, 触发价, user_main_1.网格限价止损价格, 数量)
        ba.市价止损单(user_main_1, user_main_1.网格区间上限)
        # ba.限价止损单自填数量(user_main_2, 触发价, user_main_2.网格限价止损价格, 数量)
        ba.市价止损单(user_main_2, user_main_2.网格区间上限)


    logger.info(
        f"{user_main_1.name}创建网格成功，网格区间【{user_main_1.网格区间下限}，{user_main_1.网格区间上限}】，网格数量{user_main_1.网格数量}，单网格数量{user_main_1.单网格数量}，网格限价止损价格{user_main_1.网格限价止损价格}，网格市价止损价格{user_main_1.网格市价止损价格}")
    return


def 网格初始化4(user_main_1: Account, user_main_2: Account):
    user_main_1.grid_list.clear()
    user_main_2.grid_list.clear()
    user_main_1.order_map.clear()
    user_main_2.order_map.clear()
    网格价格范围 = (user_main_1.网格区间上限 - user_main_1.网格区间下限) / user_main_1.网格数量
    当前下边界价格 = user_main_1.网格区间下限
    for i in range(user_main_1.网格数量):
        grid = Grid()
        grid.此网格上边界价格 = 当前下边界价格 + 网格价格范围
        grid.此网格下边界价格 = 当前下边界价格
        grid.此网格数量 = user_main_1.单网格数量
        当前下边界价格 = 当前下边界价格 + 网格价格范围
        if i <= (user_main_1.网格数量 / 2 - 1):
            grid.网格名称 = f"{user_main_1.name}网格{i}【{user_main_1.symbol}】"
            user_main_1.grid_list.append(grid)
        else:
            grid.网格名称 = f"{user_main_1.name}网格{i}【{user_main_2.symbol}】"
            user_main_2.grid_list.append(grid)

    校验网格2(user_main_1)
    校验网格2(user_main_2)
    user_main_1.初始化完成 = True
    user_main_2.初始化完成 = True
    return

def 网格初始化3(user_main_1: Account, user_main_2: Account):
    user_main_1.grid_list.clear()
    user_main_2.grid_list.clear()
    user_main_1.order_map.clear()
    user_main_2.order_map.clear()
    网格价格范围 = (user_main_1.网格区间上限 - user_main_1.网格区间下限) / user_main_1.网格数量
    当前下边界价格 = user_main_1.网格区间下限
    for i in range(user_main_1.网格数量):
        grid = Grid()
        grid.此网格上边界价格 = 当前下边界价格 + 网格价格范围
        grid.此网格下边界价格 = 当前下边界价格
        grid.此网格数量 = user_main_1.单网格数量
        当前下边界价格 = 当前下边界价格 + 网格价格范围
        if i <= (user_main_1.网格数量 / 2 - 1):
            grid.网格名称 = f"{user_main_1.name}网格{i}【{user_main_1.symbol}】"
            user_main_1.grid_list.append(grid)
        else:
            grid.网格名称 = f"{user_main_1.name}网格{i}【{user_main_2.symbol}】"
            user_main_2.grid_list.append(grid)

    校验网格2(user_main_1)
    校验网格2(user_main_2)
    user_main_1.初始化完成 = True
    user_main_2.初始化完成 = True
    return







def 校验网格2(user_main: Account):
    main_市价单方向 = ""
    main_市价单数量 = 0
    for i in range(0, len(user_main.grid_list)):
        time.sleep(0.05)
        grid = user_main.grid_list[i]
        if grid.此网格订单号 == "":
            if user_main.position_side == "LONG":  # 做多
                if user_main.now_price <= grid.此网格下边界价格:
                    if user_main.position_amt == 0:
                        ba.市价单(user_main, grid.此网格数量, "BUY")
                        ba.查询账户持仓情况(user_main)
                    else:
                        main_市价单数量 += grid.此网格数量
                        main_市价单方向 = "BUY"
                    Account.executor.submit(lambda p: ba.限价单_多线程(*p), (user_main, grid, grid.此网格上边界价格, "SELL"))
                else:
                    Account.executor.submit(lambda p: ba.限价单_多线程(*p), (user_main, grid, grid.此网格下边界价格, "BUY"))
            elif user_main.position_side == "SHORT":  # 做空
                if user_main.now_price >= grid.此网格上边界价格:
                    if user_main.position_amt == 0:
                        ba.市价单(user_main, grid.此网格数量, "SELL")
                        ba.查询账户持仓情况(user_main)
                    else:
                        main_市价单数量 += grid.此网格数量
                        main_市价单方向 = "SELL"
                    Account.executor.submit(lambda p: ba.限价单_多线程(*p), (user_main, grid, grid.此网格下边界价格, "BUY"))
                else:
                    Account.executor.submit(lambda p: ba.限价单_多线程(*p), (user_main, grid, grid.此网格上边界价格, "SELL"))
            else:
                logger.info(f"{user_main.name} 请先设置持仓方向！")
                return
    if main_市价单数量 != 0:
        ba.市价单(user_main, main_市价单数量, main_市价单方向)



