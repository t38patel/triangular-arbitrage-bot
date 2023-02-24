import requests
import json

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

