def deal_long(context, future_code, symbol):
    # 当月合约
    current_f = future_code
    # 获取当前合约历史数据
    num = 40
    df = attribute_history(current_f, num)
    ma_40 = df['close'].mean()
    price_now = df['close'][-1]
    last_day_close = df['close'][-1]
    if last_day_close == 0:
        log.error(current_f, "此合约没价格")
        return
    # 是否目前有仓位
    cur_long = 0

    # 最新价
    price_l = 0
    # 查看多单仓位情况
    if current_f in context.portfolio.long_positions.keys() and context.portfolio.long_positions[current_f].value > 0:
        cur_long = 1
        price_l = context.portfolio.long_positions[current_f].price
        #
        cost_price = g.porfolio_long_price[current_f]
        if cost_price == 0:
            log.error(current_f, cost_price, "long持仓价为0")
            g.porfolio_long_price[current_f] = context.portfolio.long_positions[current_f].avg_cost

    # 获取过去10年级别数据
    df_month = attribute_history(current_f, 120, unit='20d')
    lowest = df_month['low'].min()

    # 止盈or止损or加仓
    if cur_long > 0:
        #
        open_position_time = context.portfolio.long_positions[current_f].init_time
        last_open_position_time = context.portfolio.long_positions[current_f].transact_time
        # 更新开仓以来的最高价
        df_high = get_price(current_f, start_date=last_open_position_time, end_date=context.current_dt,
                            frequency='daily')
        #
        highest_from_open = df_high["close"].max()

        # long动态止盈：TODO 最高点回踩3%止盈
        is_close_position = (price_l - highest_from_open) / highest_from_open <= -0.05

        # 移动止损: TODO 0.5%
        is_stopping_loss = price_l <= g.porfolio_long_price[current_f] * 0.995 or (
                is_one_week_ago(context.current_dt, last_open_position_time) and price_l <= g.porfolio_long_price[
            current_f] + 1)
        if is_close_position:
            result = order_target_value(current_f, 0, side='long')
            if result is not None:
                g.porfolio_long_price[current_f] = 0
                # 盈利后此品种休息一段时间
                if is_close_position:
                    g.temp_removed_future_list.append(current_f)
                return

        # 浮盈加仓
        is_add_position = price_l < last_day_close
        open_cash = context.portfolio.available_cash * 0.2
        more_amount = amount_available(context, open_cash, price_l, symbol)
        if is_add_position and more_amount > 0:
            result = order(current_f, more_amount, side='long')
            if result is not None and result.filled > 0:
                g.porfolio_long_price[current_f] = result.price
                # log.info("long浮盈加仓",current_f,more_amount)
                return


    '''long开仓=============================================================
    '''
    if cur_long == 0:
        # 开仓手数
        # 保证金=合约价格x交易单位x保证金比例
        # 开仓：限制轻每单10w
        open_cash = 100000 if context.portfolio.available_cash < 500000 else context.portfolio.available_cash * 0.2
        amount = amount_available(context, open_cash, price_now, symbol)
        is_open_position = ma_40 < last_day_close < lowest * 1.4

        # 开仓
        if is_open_position and amount > 0:
            result = order_target(current_f, amount, side='long')
            if result is None:
                log.error('下单错误', current_f, price_now)
            elif result.filled > 0:
                #
                g.porfolio_long_price[current_f] = context.portfolio.long_positions[current_f].price
