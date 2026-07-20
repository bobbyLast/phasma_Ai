"""Quick smoke test: news-aligned Kalshi fetch (no secrets printed)."""

import asyncio

import sys

import os



_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if _root not in sys.path:

    sys.path.insert(0, _root)



from config.secure_config import config

from engines.news_engine_integrated import IntegratedNewsSources

from utils.prediction_market_filters import (

    is_stale_prediction_market,

    should_block_prediction_trade_post,

)





async def main():

    IntegratedNewsSources._shared_news_cache = None

    IntegratedNewsSources._shared_news_cache_time = None

    src = IntegratedNewsSources(config)

    news = await src.fetch_all_integrated_sources()

    kalshi = [i for i in news if i.get("prediction_market") == "kalshi"]

    matched = [

        i for i in kalshi

        if i.get("symbol") or i.get("news_match_score", 0) > 0

    ]

    stale_2024 = [

        i for i in kalshi

        if "2024" in (i.get("title") or "").lower()

    ]

    trade_post_queue = [

        i for i in kalshi

        if not should_block_prediction_trade_post(config, i)

    ]

    print(

        f"total_items={len(news)} kalshi_items={len(kalshi)} "

        f"news_aligned={len(matched)} stale_2024_titles={len(stale_2024)} "

        f"trade_post_queue={len(trade_post_queue)}"

    )

    for item in matched[:5]:

        sym = item.get("symbol") or "-"

        score = item.get("news_match_score", 0)

        title = (item.get("title") or "")[:72]

        intel = item.get("intel_only", False)

        print(f"  score={score} sym={sym} intel_only={intel} | {title}")

    ok = len(stale_2024) == 0 and len(trade_post_queue) == 0

    if not ok:

        if stale_2024:

            print("FAIL: stale 2024 titles in kept Kalshi markets")

        if trade_post_queue:

            print("FAIL: Kalshi items would enter trade post queue")

    else:

        print("PASS: no stale 2024 titles; Kalshi intel-only blocks trade posts")

    return 0 if ok else 1





if __name__ == "__main__":

    raise SystemExit(asyncio.run(main()))

