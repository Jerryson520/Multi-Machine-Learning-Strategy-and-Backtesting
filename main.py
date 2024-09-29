import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from alpaca.data.historical import StockHistoricalDataClient # Create stock historical data client
from strategy.ma_cross import MovingAverageCrossStrategy
from portfolio.closeprice import MarketOnClosePortfolio
from portfolio.openprice import MarketOnOpenPortfolio
from data_loader import DataLoader

if __name__ == "__main__":
    # symbol = "AMD"
    symbol = "AAPL"
    
    api_key = "PK6IRONYS5AQ646ZTDKX"
    api_secret = "HEYwi2T3MzAmYgednADOq0g6pEjuULcEz0Hbdqg8"
    client = StockHistoricalDataClient(api_key, api_secret)
    
    start_date = "2014-01-01 00:00:00"
    
    data_loader = DataLoader(client)
    bars = data_loader.fetch_historical_data(symbol, start_date=start_date)
    
    short_window, long_window = 50, 150

    mac = MovingAverageCrossStrategy(
        symbol, bars, short_window=short_window, long_window=long_window
    )
    signals = mac.generate_signals()

    portfolio = MarketOnOpenPortfolio(symbol, bars, signals, initial_capital=100000.0)
    returns = portfolio.backtest_portfolio()
    
    # backtesting results
    fig, ax = plt.subplots(2, 1, figsize=(15, 10), tight_layout=True)
    # fig.patch.set_facecolor('white')
    ax[0].plot(bars["Close"], label="Close")
    ax[0].plot(signals[["short_mavg", "long_mavg"]], label=["short_sma", "long_sma"])
    ax[0].scatter(
        signals[signals["signal"] == 1.0].index,
        signals["short_mavg"][signals["signal"] == 1.0],
        100,
        c="green",
        marker="^",
    )
    ax[0].scatter(
        signals[signals["signal"] == -1.0].index,
        signals["short_mavg"][signals["signal"] == -1.0],
        100,
        c="red",
        marker="v",
    )
    ax[0].legend()
    ax[0].set_title(
        f"{symbol} Close price and {short_window}d-SMA and {long_window}d-SMA for 10 years"
    )
    ax[0].set_xlabel("Date")

    ax[1].plot(returns["total"])
    ax[1].scatter(
        returns[signals["signal"] == 1.0].index,
        returns["total"][signals["signal"] == 1.0],
        s=100,
        c="green",
        marker="^",
    )
    ax[1].scatter(
        returns[signals["signal"] == -1.0].index,
        returns["total"][signals["signal"] == -1.0],
        s=100,
        c="red",
        marker="v",
    )

    plt.show()
