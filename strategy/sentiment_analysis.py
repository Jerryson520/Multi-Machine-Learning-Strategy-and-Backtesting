import pandas as pd
import numpy as np
import json
import requests
from strategy.strategy import Strategy
from pandas.tseries.offsets import BDay


# Sentiment analysis strategy
class SentimentAnalysisStrategy(Strategy):
    def __init__(self, symbol, bars, threshold, news_api_key):
        self.symbol = symbol
        self.bars = bars
        self.threshold = threshold  # 0.2
        self.news_loader = NewsLoader(news_api_key)
        self.sentiment_analyzer = SentimentAnalyzer()

    def generate_news_signals(self):
        score_df = self.sentiment_analyzer.daily_compound_sentiment_score(
            self.news_loader.load_news(self.symbol)
        )

        vader_Buy, vader_Sell = [], []
        for i in range(len(score_df)):
            if score_df["Score"].values[i] > self.threshold:
                # print(f"Trade Call for {extreme_scores_df['Date'][i]} is Buy.")
                vader_Buy.append(score_df["Date"][i])
            elif score_df["Score"].values[i] < -self.threshold:
                # print(f"Trade Call for {extreme_scores_df['Date'][i]} is Sell.")
                vader_Sell.append(score_df["Date"][i])
        return vader_Buy, vader_Sell

    def generate_signals(self):
        signals = pd.DataFrame(index=self.bars.index)
        signals["signal"] = 0.0

        vader_Buy, vader_Sell = self.generate_news_signals()

        for i in range(len(self.bars)):
            if self.bars.index[i].date() in vader_Buy:
                signals.iloc[i, :] = 1.0

        for i in range(len(self.bars)):
            if self.bars.index[i].date() in vader_Sell:
                signals.iloc[i, :] = -1.0

        return signals


class TradingDateCalculator:
    @staticmethod
    def get_trade_open(date):
        curr_date_open = pd.to_datetime(date).floor("d").replace(
            hour=13, minute=30
        ) - BDay(0)
        curr_date_close = pd.to_datetime(date).floor("d").replace(
            hour=20, minute=0
        ) - BDay(0)

        prev_date_close = (curr_date_open - BDay()).replace(hour=20, minute=0)
        next_date_open = (curr_date_close + BDay()).replace(hour=13, minute=30)

        if (pd.to_datetime(date) >= prev_date_close) & (
            pd.to_datetime(date) < curr_date_open
        ):
            return curr_date_open
        elif (pd.to_datetime(date) >= curr_date_close) & (
            pd.to_datetime(date) < next_date_open
        ):
            return next_date_open
        else:
            return None


class NewsLoader:
    def __init__(self, news_api_key):
        self.news_api_key = news_api_key
        self.url = "https://newsapi.org/v2/everything?"

    def load_news(self, symbol, pageSize=100):  # Timeframe,
        parameters = {
            "q": symbol,
            "sortBy": "popularity",
            "pageSize": pageSize,
            "apiKey": self.news_api_key,
        }

        response = requests.get(self.url, params=parameters)
        data = pd.DataFrame(response.json())

        # Transformation to data for use
        news_df = pd.concat([data["articles"].apply(pd.Series)], axis=1)

        # This is sentiment analysi regarding to headlines
        final_news = news_df[["publishedAt", "title"]].copy(deep=True)
        final_news["publishedAt"] = pd.to_datetime(final_news["publishedAt"])
        final_news = final_news.sort_values(by="publishedAt").reset_index(drop=True)

        # Change according to business day
        final_news.loc[:, "trading_time"] = final_news["publishedAt"].apply(
            TradingDateCalculator.get_trade_open
        )  # def get_trade_open(date):
        final_news = final_news[final_news["trading_time"].notnull()].copy()
        final_news.loc[:, "Date"] = pd.to_datetime(final_news["trading_time"]).dt.date
        final_news = final_news.drop(labels=["publishedAt", "trading_time"], axis=1)

        return final_news


class SentimentAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def score_each_article(self, final_news):
        cs = []
        for idx, row in final_news.iterrows():
            cs.append(self.sentiment_analyzer.polarity_scores(row["title"])["compound"])

        final_news.loc[:, "compound_vader_score"] = cs
        article_score = final_news[
            (final_news[["compound_vader_score"]] != 0).all(axis=1)
        ].reset_index(drop=True)

        return article_score

    def daily_compound_sentiment_score(self, final_news):
        """
        Input: DataFrame; |publishedAt|title|
        Output: DataFrame; |Date|Score|
        """
        article_score = self.score_each_article(final_news)

        # Get unique dates
        unique_dates = article_score["Date"].unique()
        grouped_dates = article_score.groupby(["Date"])
        keys_dates = list(grouped_dates.groups.keys())

        # get max/min score daily
        max_cs = []
        min_cs = []

        for key in keys_dates:
            data = grouped_dates.get_group(key)
            if data["compound_vader_score"].max() > 0:
                max_cs.append(data["compound_vader_score"].max())
            elif data["compound_vader_score"].max() < 0:
                max_cs.append(0)

            if data["compound_vader_score"].min() < 0:
                min_cs.append(data["compound_vader_score"].min())
            elif data["compound_vader_score"].min() > 0:
                min_cs.append(0)

        # figure compound socre
        extreme_scores_dict = {
            "Date": keys_dates,
            "max_scores": max_cs,
            "min_scores": min_cs,
        }
        extreme_scores_df = pd.DataFrame(extreme_scores_dict)

        final_scores = []
        for i in range(len(extreme_scores_df)):
            final_scores.append(
                extreme_scores_df["max_scores"][i] + extreme_scores_df["min_scores"][i]
            )

        daily_score = pd.DataFrame({"Date": keys_dates, "Score": final_scores})

        return daily_score


class NewsSentimentAnalysis:
    def __init__(self, news_api_key):
        self.news_loader = NewsLoader(news_api_key)
        self.sentiment_analyzer = SentimentAnalyzer()

    def analyze_sentiment(self, symbol, pageSize=100):
        final_news = self.news_loader.load_news(symbol, pageSize)
        return self.sentiment_analyzer.daily_compound_sentiment_score(final_news)