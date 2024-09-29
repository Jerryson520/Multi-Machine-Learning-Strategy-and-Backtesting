from portfolio.portfolio import Portfolio
import pandas as pd
import numpy as np

class MarketOnClosePortfolio(Portfolio):
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def generate_positions(self):
        positions = pd.DataFrame(index=self.bars.index).fillna(0.0)
        positions[self.symbol] = 100 * self.signals["signal"]
        return positions.cumsum()

    def backtest_portfolio(self):
        # portfolio = pd.DataFrame({'pos_value': self.positions[self.symbol] * self.bars['Close']})

        # pos_diff = self.positions.diff()

        # portfolio['holdings'] = self.positions[self.symbol] * self.bars['Close']
        # portfolio['cash'] = self.initial_capital - (pos_diff[self.symbol] * self.bars['Close']).cumsum()

        # portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        # portfolio['returns'] = portfolio['total'].pct_change()

        portfolio = pd.DataFrame(index=self.bars.index)
        portfolio["holdings"] = self.positions[self.symbol] * self.bars["Close"]
        pos_diff = self.positions.diff()
        portfolio["cash"] = (
            self.initial_capital - (pos_diff[self.symbol] * self.bars["Close"]).cumsum()
        )
        portfolio["total"] = portfolio["cash"] + portfolio["holdings"]
        portfolio["returns"] = portfolio["total"].pct_change()

        return portfolio