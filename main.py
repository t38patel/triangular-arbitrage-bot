import json
import time
import arbitrage

url = "https://poloniex.com/public?command=returnTicker"

# Get the correct coins to be traded
# Exchange: poloniex
# https://docs.poloniex.com/#introduction
def step_0():
    coin_json = arbitrage.get_coin_tickers(url)
    coin_list = arbitrage.structure_tradeables(coin_json)
    return coin_list

# Structure triangular pairs
def step_1(coin_list):
    structured_list = arbitrage.structure_triangular_pairs(coin_list)
    with open("structured_triangular_pairs.json", "w") as fp:
        json.dump(structured_list, fp)

# Calculate surface arb opportunities
def step_2():
    # Get the structured pairs
    with open("structured_triangular_pairs.json") as json_file:
        structured_pairs = json.load(json_file)

    # Get the surface prices
    prices_json = arbitrage.get_coin_tickers(url)

    # Loop through and get structured price info
    for t_pair in structured_pairs:
        time.sleep(0.3)
        prices_dict = arbitrage.get_price_for_t_pair(t_pair, prices_json)
        surface_arb = arbitrage.calculate_surface_rate(t_pair, prices_dict)
        if len(surface_arb) > 0:
            real_rate_arb = arbitrage.get_depth_from_orderbook(surface_arb)
            print(real_rate_arb)
            time.sleep(2)


"""MAIN"""
if __name__ == "__main__":
    coin_list = step_0()
    structured_pairs = step_1(coin_list)

    step_2()






