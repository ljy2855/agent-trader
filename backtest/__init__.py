"""Daily-bar backtest for the intraday strategy's entry/exit rules.

⚠️ This is a *proxy* backtest, not an exact replay. Kiwoom REST has no
historical leaderboard or orderbook snapshots, so the live universe selection
(등락률/거래대금 상위) and the orderbook-based score terms (ratio/spread/
breakout) cannot be reconstructed. What this CAN test, on a fixed large-cap
universe with daily OHLC, is the **entry band + stop-loss/take-profit exit
rules** — i.e. "does buying a big-cap on a +N% day and exiting at -2.5%/+5%
have positive expectancy?". Treat results as directional, not precise.
"""
