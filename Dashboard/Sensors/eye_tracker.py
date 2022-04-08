import os
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

from datetime import datetime, date, timedelta
import numpy as np

from .utils import filter_by_date, remove_file


class EyeTracker():
    def __init__(self):
        self._datadir = 'data/eye_tracker/'
        self._df = self.accumulate_data()


    def fig(self, date, time_range=[0, 23]):
        ''' produce a plotply figure with a selected timeframe '''
        df = filter_by_date(self._df, date, time_range)
        fig = px.scatter(df,
                     x='FPOGX',
                     y='FPOGY',
                     title="Eye's position on the screen",
                     animation_frame='time',
                     labels={'time':'Seconds after calibration'},
                     range_x=[0, 1],
                     range_y=[1, 0],
                     height=525
                     )
        fig.update_layout(title_font={'size':18},
            title_x=0.5,
            xaxis = go.XAxis(visible=False, showticklabels=False),
            yaxis = go.YAxis(visible=False, showticklabels=False)
            )
        return fig


    def accumulate_data(self):
        ''' merges all the different recordings to a single dataframe with cleaned data '''
        df = pd.DataFrame()
        for file in os.listdir(self._datadir):
            if '.csv' in file:
                df_temp = self.clean_df(self._datadir + file)
                df = pd.concat([df, df_temp])
        return df


    def clean_df(self,filepath):
        """
        Makes a new file based on the wanted column of the old file. Removes the old file and returns the clean dataframe.\n
        args:\n
            filepath: The filepath to the csv file to be cleaned up
        """
        def convert_to_dateformat(start, sec):
            timechange = timedelta(seconds=sec)
            return start + timechange

        try:
            new_df = pd.read_csv(filepath)
            if "_clean.csv" not in filepath:
                new_df = new_df.iloc[0:,3:7] # chooses the desired columns
                new_file_name = str(os.path.basename(filepath))
                new_df.to_csv(new_file_name,index=False)
                os.rename(new_file_name,filepath[:-4]+"_clean.csv")
                remove_file(filepath)
            
            start_time = new_df.columns[0]
            timeobj = datetime.strptime(start_time, 'TIME(%Y/%m/%d %H:%M:%S.%f)')
            new_df = new_df.rename(columns = {new_df.columns[0]: 'time'})
            new_df['timeobj'] = new_df['time'].apply(lambda x: convert_to_dateformat(timeobj, x))

            new_df = new_df[new_df.index % 40 == 0] # keeps every 40th record in the dataframe

        except FileNotFoundError:
            print("File not found with filepath: '" +filepath+"'")  

        return new_df


    def heat_map(self, date, time_range=[0, 23]):
        '''Creates a heat map from the eye tracking data'''
        df = filter_by_date(self._df, date, time_range)

        a = np.zeros((36, 64))
        x_cords = df['FPOGX'].tolist()
        y_cords = df['FPOGY'].tolist()

        try:
            for i in range(len(x_cords)):
                if 0.1 <= x_cords[i] <= 0.99 and 0.1 <= y_cords[i] <= 0.99:
                #Adds only coordinates wich are on the screen
                    x = (int(x_cords[i] * 64))
                    y = (int(y_cords[i] * 36))
                    a[y-1,x-1] += 1

        except TypeError:
            print('No eye tracking data at this time.')

        fig = px.imshow(a,color_continuous_scale=px.colors.sequential.Plasma,
                        title="Heatmap of eye tracking data")
        fig.update_layout(title_font={'size':18}, title_x=0.5)
        fig.update_traces(hovertemplate="X-cord.: %{x}"
                                        "<br>Y-cord.: %{y}"
                                        "<br>Times viewed: %{z}<extra></extra>")

        return fig
