import requests
import json
import time

# Make a get request
def get_coin_tickers(url):
    req = requests.get(url)
    coin_json = json.loads(req.text)
    return coin_json

# Loop through each pair to filter the tradeable pairs
def structure_tradeables(coin_json):
    coin_list = []
    for coin in coin_json:
        is_frozen = coin_json[coin]["isFrozen"]
        is_post_only = coin_json[coin]["postOnly"]
        if is_frozen == "0" and is_post_only == "0":
            coin_list.append(coin)
    return coin_list

# Structure arb pairs
def structure_triangular_pairs(coin_list):
    triangular_pairs_list = []
    remove_duplicates_list = []
    pairs_list = coin_list[0:]

    # PAIR A
    for pairA in pairs_list:
        pairA_split = pairA.split("_")
        pairA_base = pairA_split[0]
        pairA_quote = pairA_split[1]

        a_pair_box = [pairA_base, pairA_quote]

        # PAIR B
        for pairB in pairs_list:
            pairB_split = pairB.split("_")
            pairB_base = pairB_split[0]
            pairB_quote = pairB_split[1]

            # Check pair b
            if pairB != pairA:
                if pairB_base in a_pair_box or pairB_quote in a_pair_box:

                    # PAIR C
                    for pairC in pairs_list:
                        pairC_split = pairC.split("_")
                        pairC_base = pairC_split[0]
                        pairC_quote = pairC_split[1]

                        # Count matching C items, ensure pair c is not the same as pair b or a
                        if pairC != pairA and pairC != pairB:
                            combined = [pairA, pairB, pairC]
                            pair_box = [pairA_base, pairA_quote, pairB_base, pairB_quote, pairC_base, pairC_quote]

                            counts_c_base = 0
                            for i in pair_box:
                                if i == pairC_base:
                                    counts_c_base += 1

                            counts_c_quote = 0
                            for i in pair_box:
                                if i == pairC_quote:
                                    counts_c_quote += 1

                            if counts_c_quote == 2 and counts_c_quote == 2 and pairC_base != pairC_quote:
                                combination = pairA + "," + pairB + "," + pairC
                                item = ''.join(sorted(combined))
                                if item not in remove_duplicates_list:
                                    match_dict ={
                                        "a_base": pairA_base,
                                        "b_base": pairB_base,
                                        "c_base": pairC_base,
                                        "a_quote": pairA_quote,
                                        "b_quote": pairB_quote,
                                        "c_quote": pairC_quote,
                                        "pair_a": pairA,
                                        "pair_b": pairB,
                                        "pair_c": pairC,
                                        "combination": combination
                                    }
                                    triangular_pairs_list.append(match_dict)
                                    remove_duplicates_list.append(item)

    return triangular_pairs_list

# Structure prices
def get_price_for_t_pair(t_pair, prices_json):

    # Get pair info
    pairA = t_pair["pair_a"]
    pairB = t_pair["pair_b"]
    pairC = t_pair["pair_c"]

    # Get price info
    pairA_ask = prices_json[pairA]["lowestAsk"]
    pairA_bid = prices_json[pairA]["highestBid"]
    pairB_ask = prices_json[pairB]["lowestAsk"]
    pairB_bid = prices_json[pairB]["highestBid"]
    pairC_ask = prices_json[pairC]["lowestAsk"]
    pairC_bid = prices_json[pairC]["highestBid"]

    return {
        "pairA_ask": pairA_ask,
        "pairA_bid": pairA_bid,
        "pairB_ask": pairB_ask,
        "pairB_bid": pairB_bid,
        "pairC_ask": pairC_ask,
        "pairC_bid": pairC_bid,
    }

# Calculate surface rate
def calculate_surface_rate(t_pair, prices_dict):

    starting_amount = 1
    min_surface_rate = 0
    surface_dict = {}
    contract_2 = ""
    contract_3 = ""
    direction_trade_1 = ""
    direction_trade_2 = ""
    direction_trade_3 = ""
    acquired_coin_t2 = 0
    acquired_coin_t3 = 0
    calculated = 0

    a_base = t_pair["a_base"]
    a_quote = t_pair["a_quote"]
    b_base = t_pair["b_base"]
    b_quote = t_pair["b_quote"]
    c_base = t_pair["c_base"]
    c_quote = t_pair["c_quote"]
    pair_a = t_pair["pair_a"]
    pair_b = t_pair["pair_b"]
    pair_c = t_pair["pair_c"]

    a_ask = float(prices_dict["pairA_ask"])
    a_bid = float(prices_dict["pairA_bid"])
    b_ask = float(prices_dict["pairB_ask"])
    b_bid = float(prices_dict["pairB_bid"])
    c_ask = float(prices_dict["pairC_ask"])
    c_bid = float(prices_dict["pairC_bid"])

    if a_ask == 0 or a_bid == 0 or b_ask == 0 or b_bid == 0 or c_ask == 0 or c_bid == 0:
        return []

    direction_list = ["forward", "reverse"]
    for direction in direction_list:

        # Set additional variables for swap information
        swap_1 = 0
        swap_2 = 0
        swap_3 = 0
        swap_1_rate = 0
        swap_2_rate = 0
        swap_3_rate = 0

        """
            Poloniex Rules !!
            If we are swapping the coin on the left (Base) to the right (Quote) then * (1 / Ask)
            If we are swapping the coin on the right (Quote) to the left (Base) then * Bid
        """

        # Assume starting with a_base and swapping for a_quote
        if direction == "forward":
            swap_1 = a_base
            swap_2 = a_quote
            swap_1_rate = 1 / a_ask
            direction_trade_1 = "base_to_quote"

        # Assume starting with a_base and swapping for a_quote
        if direction == "reverse":
            swap_1 = a_quote
            swap_2 = a_base
            swap_1_rate = a_bid
            direction_trade_1 = "quote_to_base"

        # Place first trade
        contract_1 = pair_a
        acquired_coin_t1 = starting_amount * swap_1_rate

        """  FORWARD """
        # SCENARIO 1 Check if a_quote (acquired_coin) matches b_quote
        if direction == "forward":
            if a_quote == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_b

                # If b_base (acquired coin) matches c_base
                if b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # If b_base (acquired coin) matches c_quote
                if b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 2 Check if a_quote (acquired_coin) matches b_base
        if direction == "forward":
            if a_quote == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_b

                # If b_quote (acquired coin) matches c_base
                if b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # If b_quote (acquired coin) matches c_quote
                if b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 3 Check if a_quote (acquired_coin) matches c_quote
        if direction == "forward":
            if a_quote == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_c

                # If c_base (acquired coin) matches b_base
                if c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # If c_base (acquired coin) matches b_quote
                if c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 4 Check if a_quote (acquired_coin) matches c_base
        if direction == "forward":
            if a_quote == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_c

                # If c_quote (acquired coin) matches b_base
                if c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # If c_quote (acquired coin) matches b_quote
                if c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        """  REVERSE """
        # SCENARIO 1 Check if a_base (acquired_coin) matches b_quote
        if direction == "reverse":
            if a_base == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_b

                # If b_base (acquired coin) matches c_base
                if b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # If b_base (acquired coin) matches c_quote
                if b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 2 Check if a_base (acquired_coin) matches b_base
        if direction == "reverse":
            if a_base == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_b

                # If b_quote (acquired coin) matches c_base
                if b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # If b_quote (acquired coin) matches c_quote
                if b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 3 Check if a_base (acquired_coin) matches c_quote
        if direction == "reverse":
            if a_base == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_c

                # If c_base (acquired coin) matches b_base
                if c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # If c_base (acquired coin) matches b_quote
                if c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 4 Check if a_base (acquired_coin) matches c_base
        if direction == "reverse":
            if a_base == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_c

                # If c_quote (acquired coin) matches b_base
                if c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # If c_quote (acquired coin) matches b_quote
                if c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # P/L
        profit_loss = acquired_coin_t3 - starting_amount
        profit_loss_percent = (profit_loss / starting_amount) * 100 if profit_loss != 0 else 0

        # Trade Descriptions
        trade_description_1 = f"Start with {swap_1} of {starting_amount}. Swap at {swap_1_rate} for {swap_2} acquiring {acquired_coin_t1}."
        trade_description_2 = f"Swap {acquired_coin_t1} of {swap_2} at {swap_2_rate} for {swap_3} acquiring {acquired_coin_t2}."
        trade_description_3 = f"Swap {acquired_coin_t2} of {swap_3} at {swap_3_rate} for {swap_1} acquiring {acquired_coin_t3}."

        # Output
        if profit_loss_percent > min_surface_rate:
            surface_dict = {
                "swap_1": swap_1,
                "swap_2": swap_2,
                "swap_3": swap_3,
                "contract_1": contract_1,
                "contract_2": contract_2,
                "contract_3": contract_3,
                "direction_trade_1": direction_trade_1,
                "direction_trade_2": direction_trade_2,
                "direction_trade_3": direction_trade_3,
                "starting_amount": starting_amount,
                "acquired_coin_t1": acquired_coin_t1,
                "acquired_coin_t2": acquired_coin_t2,
                "acquired_coin_t3": acquired_coin_t3,
                "swap_1_rate": swap_1_rate,
                "swap_2_rate": swap_2_rate,
                "swap_3_rate": swap_3_rate,
                "profit_loss": profit_loss,
                "profit_loss_perc": profit_loss_percent,
                "direction": direction,
                "trade_description_1": trade_description_1,
                "trade_description_2": trade_description_2,
                "trade_description_3": trade_description_3
            }
            return surface_dict
    return surface_dict

# Reformat the orderbook for further calculation
def reformated_orderbook(prices, c_direction):
    price_list_main = []
    if c_direction == "base_to_quote":
        for p in prices["asks"]:
            ask_price = float(p[0])
            adj_price = 1 / ask_price if ask_price != 0 else 0
            adj_quantity = float(p[1]) * ask_price
            price_list_main.append([adj_price, adj_quantity])
    if c_direction == "quote_to_base":
        for p in prices["bids"]:
            bid_price = float(p[0])
            adj_price = bid_price if bid_price != 0 else 0
            adj_quantity = float(p[1])
            price_list_main.append([adj_price, adj_quantity])
    return price_list_main

# Get Acquired Coin Also Known As Depth Calculation
def calculate_acquired_coin(amount_in, orderbook):

    trading_balance = amount_in
    quantity_bought = 0
    acquired_coin = 0
    counts = 0
    for level in orderbook:

        # Extract the level price and quantity
        level_price = level[0]
        level_available_quantity = level[1]

        # Amount In is <= first level total amount
        if trading_balance <= level_available_quantity:
            quantity_bought = trading_balance
            trading_balance = 0
            amount_bought = quantity_bought * level_price

        # Amount In is > a given level total amount
        if trading_balance > level_available_quantity:
            quantity_bought = level_available_quantity
            trading_balance -= quantity_bought
            amount_bought = quantity_bought * level_price

        # Accumulate acquired coin
        acquired_coin = acquired_coin + amount_bought

        # Exit the trade
        if trading_balance == 0:
            return acquired_coin

        # Exit if not enough order book levels
        counts += 1
        if counts == len(orderbook):
            return 0

# Get depth from orderbook
def get_depth_from_orderbook(surface_arb):
    swap_1 = surface_arb["swap_1"]
    starting_amount = 100
    starting_amount_dict = {
        "USDT": 100,
        "USDC": 100,
        "BTC": 0.01,
        "ETH": 0.05
    }
    if swap_1 in starting_amount_dict:
        starting_amount = starting_amount_dict[swap_1]

    contract_1 = surface_arb["contract_1"]
    contract_2 = surface_arb["contract_2"]
    contract_3 = surface_arb["contract_3"]
    contract_1_direction = surface_arb["direction_trade_1"]
    contract_2_direction = surface_arb["direction_trade_2"]
    contract_3_direction = surface_arb["direction_trade_3"]


    url1 = f"https://poloniex.com/public?command=returnOrderBook&currencyPair={contract_1}&depth=20"
    depth_1_prices = get_coin_tickers(url1)
    depth_1_reformatted_prices = reformated_orderbook(depth_1_prices, contract_1_direction)
    time.sleep(0.3)
    url2 = f"https://poloniex.com/public?command=returnOrderBook&currencyPair={contract_2}&depth=20"
    depth_2_prices = get_coin_tickers(url2)
    depth_2_reformatted_prices = reformated_orderbook(depth_2_prices, contract_2_direction)
    time.sleep(0.3)
    url3 = f"https://poloniex.com/public?command=returnOrderBook&currencyPair={contract_3}&depth=20"
    depth_3_prices = get_coin_tickers(url3)
    depth_3_reformatted_prices = reformated_orderbook(depth_3_prices, contract_3_direction)

    # Get Acquired Coins
    acquired_coin_t1 = calculate_acquired_coin(starting_amount, depth_1_reformatted_prices)
    acquired_coin_t2 = calculate_acquired_coin(acquired_coin_t1, depth_2_reformatted_prices)
    acquired_coin_t3 = calculate_acquired_coin(acquired_coin_t2, depth_3_reformatted_prices)

    # Calculate real rate (P/L)
    profit_loss = acquired_coin_t3 - starting_amount
    real_rate_percentage = (profit_loss / starting_amount) * 100 if profit_loss != 0 else 0

    if real_rate_percentage > -1:
        return_dict = {
            "profit_loss": profit_loss,
            "real_rate_perc": real_rate_percentage,
            "contract_1": contract_1,
            "contract_2": contract_2,
            "contract_3": contract_3,
            "contract_1_direction": contract_1_direction,
            "contract_2_direction": contract_2_direction,
            "contract_3_direction": contract_3_direction
        }
        return return_dict
    else:
        return {}



