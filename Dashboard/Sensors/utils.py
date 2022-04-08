import pandas as pd
from datetime import datetime, timedelta
import os

def remove_file(filepath):
    """Removes a file with the given filepath, if it exists
    args:
        filepath: path to the file to be removed
    """
    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        print("Can not delete the file as it doesn't exist")


def filter_by_date(df, date, time=[0, 23]):
    '''Returs a dataframe filtered by date and time
    args:
        df: dataframe with a column named timeobj, containing datetimeobbjects
        date: datetime object
        time: list with starting-hour and ending-hour, ex [8, 16] 
    '''
    start_hour = int(time[0])
    start_minutes = int((time[0] * 60) % 60)
    end_hour = int(time[1])
    end_minutes = int((time[1] * 60) % 60)

    start = datetime(date.year, date.month, date.day, start_hour, start_minutes)
    end = datetime(date.year, date.month, date.day, end_hour, end_minutes)

    df = df[df['timeobj'] > start]
    df = df[df['timeobj'] < end]
    
    return df


def daylight_saving(dt):
    """Returns a datetime object, unchanged from output if 
       datetime does not apply
    args:
        dt: datetime object containing the time to be checked
    """
    # Hardcoded for this year only (2022)
    # Problem if user creates file at 01:59 and keeps recording,
    # it is a edgecase which is unlikely to happen :)
    THIS_YEAR = datetime.today().year
    DAYLIGHT_START = datetime(THIS_YEAR, 3, 27, 2)
    DAYLIGHT_END   = datetime(THIS_YEAR, 10, 30, 3)

    if (DAYLIGHT_START <= dt and dt <= DAYLIGHT_END):
        dt += timedelta(hours=1)

    return dt
