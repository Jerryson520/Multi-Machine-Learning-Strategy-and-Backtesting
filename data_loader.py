from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd

## Load from Alpaca
class DataLoader:
    def __init__(self, stock_client):
        self.stock_client = stock_client
        
    def fetch_historical_data(self, symbol, start_date=None, end_date=None):
        request_params = StockBarsRequest(
                                symbol_or_symbols=[symbol],
                                timeframe=TimeFrame.Day,
                                start=start_date
                        )
        bars = self.stock_client.get_stock_bars(request_params)
        bars_df = bars.df

        bars_df = (
            bars_df[['open', 'high', 'low', 'close', 'volume']]
            .reset_index().drop('symbol', axis=1)
        )

        bars = (
            bars_df
            .set_index(pd.to_datetime(bars_df['timestamp']))
            .rename(columns={
                'open': 'Open', 
                'high': 'High', 
                'low': 'Low', 
                'close': 'Close', 
                'volume': 'Volume'
                })
        )

        bars.index = bars.index.strftime('%Y-%m-%d')
        bars.index.name = 'Date'

        return bars