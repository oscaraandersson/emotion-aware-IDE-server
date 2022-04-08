from audioop import avg
from operator import index
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from .utils import filter_by_date, daylight_saving

TIME_DIFFERENCE = 1


class E4Wristband():
    def __init__(self):
        self._datadir = 'data/e4_wristband'
        self._df_eda, self._df_hr, self._df_bvp = self._accumulate_data()


    def _accumulate_data(self):
        """
        Returns dataframes for all e4 data
        """
        # initialize variables
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
        df3 = pd.DataFrame()
        # get all files in e4 data dir
        for file in os.listdir(self._datadir):
            if '.csv' in file:
                # read data from csv file
                df_tmp = pd.read_csv(os.path.join(self._datadir, file))
                # get time
                time_zero = float(df_tmp.columns[0])
                if 'EDA' in file:
                    # get e4 data
                    df_tmp = df_tmp.rename(columns={df_tmp.columns[0]: 'EDA'})
                    df_tmp = self._clean_df(df_tmp, time_zero)
                    df1 = pd.concat([df1, df_tmp])
                elif 'HR' in file:
                    # get hr data
                    df_tmp = df_tmp.rename(columns={df_tmp.columns[0]: 'HR'})
                    df_tmp = self._clean_df(df_tmp, time_zero)
                    df2 = pd.concat([df2, df_tmp])
                else:
                    # assume bvp data
                    df_tmp = df_tmp.rename(columns={df_tmp.columns[0]: 'BVP'})
                    df_tmp = self._clean_df(df_tmp, time_zero)
                    df3 = pd.concat([df3, df_tmp])
        # sort data
        df1 = df1.sort_values(by='timeobj')
        df2 = df2.sort_values(by='timeobj')
        df3 = df3.sort_values(by='timeobj')
        return df1, df2, df3


    def _clean_df(self, df, time_zero):
        # Frequency is located on first row
        frequency = int(df[df.columns[0]].iloc[0])
        # Remove frequency
        df = df[1:]
        # Only want one data point per second
        df = df[(df.index-1) % frequency == 0]
        df = df.reset_index(drop=True)
        def _u_to_d(unixtime):
            """ Translates unix time to datetime object """
            dt = datetime.utcfromtimestamp(unixtime)
            # Check for swedish daylight saving
            dt = daylight_saving(dt)
            return dt
        # Add a row displaying datetime per data
        df["timeobj"] = [_u_to_d((i)+time_zero) for i in range(len(df[df.columns[0]]))]
        return df


    def fig(self, data_type, date, time_range=[0, 24]):
        """
        Returns a plotly figure for the requested in data in requested timeframe
        args:
            data_type: what type of data ['EDA', 'HR', 'BVP']
            date: a date object for the day you want to get data of
            time_range: list of time from and to
        """
        # size for card
        BROWSER_HEIGHT = 500
        BROWSER_WIDTH = 750

        # initialize variables
        df = pd.DataFrame()

        if data_type == 'EDA':
            # use eda data
            df = filter_by_date(self._df_eda, date, time_range)
        elif data_type == 'HR':
            # use hr data
            df = filter_by_date(self._df_hr, date, time_range)
        else:
            # else use bvp data
            df = filter_by_date(self._df_bvp, date, time_range)
        # create figure
        fig = px.line(df,
            x = 'timeobj',
            y = data_type,
            labels={'timeobj':'Time'}
        )
        return fig


    def card(self, data_type, date, time_range=[0, 24]):
        if data_type == 'EDA':
            df = filter_by_date(self._df_eda, date, time_range)
        elif data_type == 'HR':
            df = filter_by_date(self._df_hr, date, time_range)
        else:
            df = filter_by_date(self._df_bvp, date, time_range)
        _min = df[data_type].min()
        _avg = df[data_type].mean()
        _max = df[data_type].max()
        return _min, _avg, _max

