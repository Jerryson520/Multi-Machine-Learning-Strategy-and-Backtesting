import pandas as pd
import numpy as np
from strategy.strategy import Strategy

class MovingAverageCrossStrategy(Strategy):
    def __init__(self, symbol, bars, short_window=2, long_window=5):
        self.symbol = symbol
        self.bars = bars
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):
        signals = pd.DataFrame(index=self.bars.index)
        signals["signal"] = 0.0

        signals["short_mavg"] = (
            self.bars["Close"].rolling(self.short_window, min_periods=1).mean()
        )
        signals["long_mavg"] = (
            self.bars["Close"].rolling(self.long_window, min_periods=1).mean()
        )

        # print(signals['short_mavg'][self.short_window:].shift(1) < signals['long_mavg'][self.short_window:].shift(1))

        
        signals["signal"][self.short_window :] = np.where(
            (
                (
                    signals["short_mavg"][self.short_window :]
                    > signals["long_mavg"][self.short_window :]
                )
                & (
                    signals["short_mavg"][self.short_window :].shift(1)
                    < signals["long_mavg"][self.short_window :].shift(1)
                )
            ),
            1.0,
            0.0,
        )

        signals["signal"][self.short_window :] = np.where(
            (
                (
                    signals["short_mavg"][self.short_window :]
                    < signals["long_mavg"][self.short_window :]
                )
                & (
                    signals["short_mavg"][self.short_window :].shift(1)
                    > signals["long_mavg"][self.short_window :].shift(1)
                )
            ),
            -1.0,
            signals["signal"][self.short_window:],
        )

        # # signals['positions'] = signals['signal'].diff()
        # signals['positions'] = signals['signal'].cumsum()

        return signals