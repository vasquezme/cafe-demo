import pandas as pd
import dash
import os
from dash import dcc, html, Input, Output, callback, no_update
import plotly.express as px
import json
import plotly.graph_objects as go
import posthog
import requests  # Use official/unofficial NotebookLM API

# Posthog setup
posthog.api_key = 'phc_RLhhUoMn6wYHZYUizZRKGW8wf2N64mlvdkKzK0lyF95'
posthog.host = 'https://us.i.posthog.com'

posthog.capture(distinct_id='test', event='test-event')

# Load GeoJSON files
with open("data/5min-walk.geojson") as f:
    min5polygon = json.load(f)
with open("data/10min-walk.geojson") as f:
    min10polygon = json.load(f)
with open("data/15min-walk.geojson") as f:
    min15polygon = json.load(f)
with open("data/cafe-locations.geojson") as f:
    locations = json.load(f)
locations_df = pd.json_normalize(locations["features"])
with open("data/arima-office.geojson") as f:
    office = json.load(f)

# Convert columns to numeric
for col in [
    'properties.REVENUE',
    'properties.DISTANCE',
    'properties.CUSTOMERS',
    'properties.DONUTS_SOLD',
    'properties.RATING'
]:
    locations_df[col] = pd.to_numeric(locations_df[col], errors='coerce')

app = dash.Dash(__name__)
server = app.server

def create_map(selected_walk_time):
    fig = go.Figure()
    
    # Add polygons based on selected_walk_time (UNCHANGED)
    if selected_walk_time == '5':
        polygon_coords = min5polygon["features"][0]["geometry"]["coordinates"][0]
        lons, lats = zip(*polygon_coords)
        fig.add_trace(go.Scattermap(lon=lons, lat=lats, mode='lines', fill='toself', fillcolor='rgba(173, 216, 230, 0.7)', line=dict(width=2, color='blue'), name='5min-walk Polygon'))
    elif selected_walk_time == '10':
        polygon_coords = min10polygon["features"][0]["geometry"]["coordinates"][0]
        lons, lats = zip(*polygon_coords)
        fig.add_trace(go.Scattermap(lon=lons, lat=lats, mode='lines', fill='toself', fillcolor='rgba(255, 204, 203, 0.7)', line=dict(width=2, color='red'), name='10min-walk Polygon'))
    elif selected_walk_time == '15':
        polygon_coords = min15polygon["features"][0]["geometry"]["coordinates"][0]
        lons, lats = zip(*polygon_coords)
        fig.add_trace(go.Scattermap(lon=lons, lat=lats, mode='lines', fill='toself', fillcolor='rgba(255, 165, 0, 0.3)', line=dict(width=2, color='orange'), name='15min-walk Polygon'))
    elif selected_walk_time == 'all':
        for mins, poly, fillcolor, linecolor, legend in [
            ('5', min5polygon, 'rgba(173, 216, 230, 0.3)', 'blue', '5 min. Walk Time'), 
            ('10', min10polygon, 'rgba(255, 204, 203, 0.3)', 'red', '10 min. Walk Time'),
            ('15', min15polygon, 'rgba(255, 165, 0, 0.3)', 'orange', '15 min. Walk Time') 
        ]:
            polygon_coords = poly["features"][0]["geometry"]["coordinates"][0]
            lons, lats = zip(*polygon_coords)
            fig.add_trace(go.Scattermap(
                lon=lons, lat=lats, mode='lines', fill='toself', fillcolor=fillcolor,
                line=dict(width=2, color=linecolor), name=legend
            ))

    # Add coffee locations (UNCHANGED)
    lons_loc, lats_loc, hover_texts = [], [], []
    for feature in locations["features"]:
        coords = feature["geometry"]["coordinates"]
        lons_loc.append(coords[0])
        lats_loc.append(coords[1])
        props = feature["properties"]
        hover_texts.append(f"Name: {props.get('NAME', 'N/A')}<br>Chain: {props.get('CHAIN_NAME', 'N/A')}<br>Revenue: ${props.get('REVENUE', 'N/A')}<br>Rating: {props.get('RATING', 'N/A')}")
    
    fig.add_trace(go.Scattermap(lon=lons_loc, lat=lats_loc, mode='markers', marker=dict(size=10, color='black'), name='Coffee Locations', text=hover_texts, hoverinfo='text'))

    # Add office location (UNCHANGED)
    lons_loc, lats_loc = [], []
    for feature in office["features"]:
        coords = feature["geometry"]["coordinates"]
        lons_loc.append(coords[0])
        lats_loc.append(coords[1])
    
    fig.add_trace(go.Scattermap(lon=lons_loc, lat=lats_loc, mode='markers', marker=dict(size=15, color='yellow'), name='Arima Office', text='Arima Office', hoverinfo='text'))

    fig.update_layout(mapbox_style="carto-positron", mapbox_center={"lat": 43.65569205940113, "lon": -79.38679602617921}, mapbox_zoom=18, margin={"r":0,"t":0,"l":0,"b":0}, legend=dict(font=dict(size=18)))
    return fig

# Layout (UNCHANGED - YOUR EXISTING DASHBOARD)
app.layout = html.Div([
    html.H1("Coffee Shops Close to the Arima Office (5, 10, 15 min. Walk Times) ", style={'textAlign': 'center', 'marginTop': '20px', 'marginBottom': '20px', 'fontSize': '48px', 'fontFamily': 'Arial, sans-serif', 'fontWeight': 'bold', 'color': '#333'}),
    html.P(""),
    dcc.Dropdown(id='walk-time-dropdown', options=[{'label': 'ALL', 'value': 'all'}, {'label': 'UNDER 5 MINS.', 'value': '5'}, {'label': 'UNDER 10 MINS.', 'value': '10'}, {'label': 'UNDER 15 MINS.', 'value': '15'}], value='all', clearable=False, style={'width': '200px', 'margin': '0 auto 20px auto', 'fontSize': '18px','fontWeight' : 'bold'}),
    
    # Scorecard section (UNCHANGED)
    html.Div([
        html.Div([html.H3("Coffee Shops", style={"fontsize": "24px", "fontWeight": "bold"}), html.P(id="scorecard-shops", style={"fontSize": "42px", "fontWeight": "bold"})], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([html.H3("Total Revenue", style={"fontsize": "24px", "fontWeight": "bold"}), html.P(id="scorecard-revenue", style={"fontSize": "42px", "fontWeight": "bold"})], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([html.H3("Total Customers", style={"fontsize": "24px", "fontWeight": "bold"}), html.P(id="scorecard-customers", style={"fontSize": "42px", "fontWeight": "bold"})], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([html.H3("Donuts Sold", style={"fontsize": "24px", "fontWeight": "bold"}), html.P(id="scorecard-donuts", style={"fontSize": "42px", "fontWeight": "bold"})], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([html.H3("Average Distance (M)", style={"fontsize": "24px", "fontWeight": "bold"}), html.P(id="scorecard-distance", style={"fontSize": "42px", "fontWeight": "bold"})], style={"padding": "10px
