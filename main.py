import json

import arbitrage

# Get the correct coins to be traded
# Exchange: poloniex
# https://docs.poloniex.com/#introduction
def step_0():
    url = "https://poloniex.com/public?command=returnTicker"
    coin_json = arbitrage.get_coin_tickers(url)
    coin_list = arbitrage.structure_tradeables(coin_json)
    return coin_list

# Structure triangular pairs
def step_1(coin_list):
    structured_list = arbitrage.structure_triangular_pairs(coin_list)
    with open("structured_triangular_pairs.json", "w") as fp:
        json.dump(structured_list, fp)



"""MAIN"""
if __name__ == "__main__":
    coin_list = step_0()
    structured_pairs = step_1(coin_list)






