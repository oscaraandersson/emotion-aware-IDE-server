from ast import In
from time import time
import dash
import os
from datetime import datetime, timedelta, date
import numpy as np
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from Sensors.e4 import E4Wristband
from Sensors.eye_tracker import EyeTracker
from Sensors.e4 import E4Wristband
from Sensors.piechart import Piechart

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

eye_tracker = EyeTracker()
e4 = E4Wristband()
pie = Piechart()
light_grey_color = '#F4F4F4'

# defining the graph outside the layout for easier read
graph_card = dcc.Graph(id='eye_tracking_visualization')
e4_fig = dcc.Graph(id='e4_LineGraph')
graph_card3 = dcc.Graph(id='eye_tracker_heatmap')
pie_card = dcc.Graph(id="pie_chart")
pie_summary = dcc.Graph(id="pie_summary")
header = dbc.Row(
            dbc.Container(
                [
                    html.H1("Emotional Aware Dashboard"),
                    html.P("Explore your data from the E4 wristband, eyetracker and EEG headset")
                ]
            ),
            className="text-white h-200 bg-dark",
            style={
                'padding' : 20,
                'textAlign': 'center'
            }
        )


E4description_p1 = """Blood Volume Pulse (BVP) is the change of blood volume in the microvascular bed of tissue.
                            This is used to generate the heart rate. However, compared to the heart rate, BVP has a higher
                            frequency and more precision."""

E4description_p2 = """Blood Volume Pulse (BVP) is the change of blood volume in the microvascular bed of tissue. 
                    This is used to generate the heart rate. However, compared to the heart rate, BVP has a higher frequency and more precision."""

Pie_desciption_p1 = """ With the data collected from the e4 wristband and a neural network we have tried to preticted an users moods."""
Pie_desciption_p2 = """ The Pie shows the summary of emotions during the given time range"""

time_labels = [{'label':f'{i:02}:00', 'value':i} for i in range(0, 24, 2)]

date_picker_bar = html.Div(
    html.Div(
        children=[
                    html.H4('Select a timeframe', style={'margin' : 'auto', 'margin-right' : 20}),
                    html.P('Date:', style={'margin' : 'auto'}),
                    dcc.DatePickerSingle(id='datepicker', date=date(2022, 2, 9), style={'background-color' : 'red', 'border-radius' : 10}),
                    html.P('Start time:', style={'margin' : 'auto'}),
                    dcc.Dropdown(time_labels, 8, id='start', style={'width':100}),
                    html.P('End time:', style={'margin' : 'auto'}),
                    dcc.Dropdown(time_labels, 18, id='end', style={'width':100}),
                ], style={'width' : 'fit-content',
                          'display' : 'grid',
                          'gap' : 20,
                          'grid-auto-flow' : 'column',
                          'align-items' : 'center',
                          'vertical-align' : 'center',
                          'margin' : '0 auto',
                          'background' : '#F4F4F4',
                          'border-radius' : 10,
                          'padding' : 10,
                          'padding-right' : 30,
                          'padding-left' : 30}
                ), style={'justify-content' : 'center',
                          'width' : 'auto',
                          'padding-top' : 40,
                          'padding-bottom' : 40}
)

E4ColumnPicker = dbc.Col(
    [
        html.Div(
            html.H2("E4 Wristband"),
            style={'textAlign' : 'left','padding' : 10}
        ),
        html.Div(
            dbc.Card([
                    dbc.CardBody([
                            html.H4("Select datasource", className="card-title"),
                            dcc.Dropdown(
                                options=[
                                    {'label' : 'Heart rate', 'value' : 'HR'},
                                    {'label' : 'EDA', 'value' : 'EDA'}, 
                                    {'label' : 'Blood Volume Pulse','value':'BVP'}], 
                                value="HR",
                                id='e4dropdown',
                                style={'width':200}
                            )
                        ])
                    ], color=light_grey_color),
        ),
        html.Div(
            [
                html.Div(
                    html.P([
                            E4description_p1, 
                            html.Br(), html.Br(), 
                            E4description_p2
                            ], style={'color' : '#353535', 'margin-top': 20})
                ),
            ], style={'padding' : 5}
        )
    ],
    width=3,
    style={'padding' : 30,'width' : '24rem'}
)

Pie_info = dbc.Row([
    dbc.Col([
        html.Div([
            html.Div(
                html.P([
                    Pie_desciption_p1,
                    html.Br(),html.Br(),
                    Pie_desciption_p2,
                    html.Br(),html.Br(),
                    "Red : Tense",
                    html.Br(),html.Br(),
                    "Blue : Calm",
                    html.Br(),html.Br(),
                    "Purple : Fatigued",
                    html.Br(),html.Br(),
                    "Green : Excited"
                    ], style={'color' : '#353535', 'margin-top': 20})
                )]
            )
    ]),
    dbc.Col(
        pie_card
    )
    ])


E4Graph = dbc.Col([e4_fig], width=6)
E4Summary = dbc.Col([html.Div(children=[], id='summary', style={'padding' : 10, 'align' : 'right'})], align='right', width=2)

def summary_card(number, source, label):
    return html.Div([
            html.H4(str(number), style={'margin' : 7}),
            html.P(f'{label} {source}', style={'margin' : 7})],
            style={
                'text-align' : 'center',
                'padding' : 10,
                'margin-top' : 15,
                'margin-bottom' : 15,
                'background' : light_grey_color,
                'border-radius' : 20})

# the layout
app.layout = html.Div(
    [
        header,
        html.Div(
            children=[
                date_picker_bar,
                dbc.Row(
                    [
                        E4ColumnPicker,
                        E4Graph,
                        E4Summary,
                    ], justify='between', align='center'
                ),

            html.Hr(),
            html.H2('Eyetracker'),
            dbc.Row(
                [dbc.Col(
                    graph_card, width=5)
                ,dbc.Col(
                    graph_card3, width=5)
                ], justify="center"),
            html.H2("Daily Summary"),
            Pie_info
            ], style= {'padding-left' : 60, 'padding-right' : 60},
        ),
    ]
)

@app.callback(
    Output('eye_tracking_visualization', 'figure'),
    Input('datepicker', 'date'),
    Input('start', 'value'),
    Input('end', 'value'))
def update_eyetracker_scatterfig(date, start, end):
    time_range = [start, end]
    date = datetime.strptime(date, '%Y-%m-%d').date()
    return eye_tracker.fig(date, time_range)


@app.callback(
    Output('eye_tracker_heatmap', 'figure'),
    Input('datepicker', 'date'),
    Input('start', 'value'),
    Input('end', 'value'))
def update_eyetracker_heatmap(date, start, end):
    time_range = [start, end]
    date = datetime.strptime(date, '%Y-%m-%d').date()
    return eye_tracker.heat_map(date, time_range)


@app.callback(
    Output('e4_LineGraph', 'figure'),
    Input('e4dropdown', 'value'),
    Input('datepicker', 'date'),
    Input('start', 'value'),
    Input('end', 'value'))
def update_e4_LineGraph(data_type, date, start, end):
    time_range = [start, end]
    date = datetime.strptime(date, '%Y-%m-%d').date()
    return e4.fig(data_type, date, time_range)


@app.callback(
    Output('summary', 'children'),
    Input('e4dropdown', 'value'),
    Input('datepicker', 'date'),
    Input('start', 'value'),
    Input('end', 'value'))
def update_e4_summary(data_type, date, start, end):
    time_range = [start, end]
    date = datetime.strptime(date, '%Y-%m-%d').date()
    _min, _avg, _max = e4.card(data_type, date, time_range)
    return [summary_card(round(_avg, 3), data_type, 'average'),
            summary_card(round(_min, 3), data_type, 'min'),
            summary_card(round(_max, 3), data_type, 'max')]

@app.callback(
    Output("pie_chart","figure"),
    Input("datepicker","date"),
    Input("start","value"),
    Input("end","value"))
def update_pie(date,start,end):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    time_range = [start,end]
    return pie.create_pie(date,time_range)



if __name__ == '__main__':
    app.run_server(host='localhost', debug=True)
