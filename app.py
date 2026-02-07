import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import json
import plotly.graph_objects as go
import posthog
import requests  # Use official/unofficial NotebookLM API


posthog.api_key = 'phc_RLhhUoMn6wYHZYUizZRKGW8wf2N64mlvdkKzK0lyF95'
posthog.host = 'https://us.i.posthog.com'

posthog.capture(
    distinct_id='test',
    event='test-event'
)


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

# Convert columns to numeric, coercing errors to NaN
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
    # Add polygons based on selected_walk_time
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
                lon=lons,
                lat=lats,
                mode='lines',
                fill='toself',
                fillcolor=fillcolor,
                line=dict(width=2, color=linecolor),
                name=legend
            ))

    # Add locations
    # Extract all coffee location points
    lons_loc = []
    lats_loc = []
    hover_texts = []
    for feature in locations["features"]:
        coords = feature["geometry"]["coordinates"]
        lons_loc.append(coords[0])
        lats_loc.append(coords[1])
        props = feature["properties"]
        hover_texts.append(
            f"Name: {props.get('NAME', 'N/A')}<br>"
            f"Chain: {props.get('CHAIN_NAME', 'N/A')}<br>"
            f"Revenue: ${props.get('REVENUE', 'N/A')}<br>"
            f"Rating: {props.get('RATING', 'N/A')}"
        )
    
    fig.add_trace(
        go.Scattermap(
            lon=lons_loc,
            lat=lats_loc,
            mode='markers',
            marker=dict(size=10, color='black'),
            name='Coffee Locations',
            text=hover_texts,
            hoverinfo='text'
        )
    )

    # Add office location
    # Extract all coffee location points
    lons_loc = []
    lats_loc = []
    for feature in office["features"]:
        coords = feature["geometry"]["coordinates"]
        lons_loc.append(coords[0])
        lats_loc.append(coords[1])

    fig.add_trace(
        go.Scattermap(
            lon=lons_loc,
            lat=lats_loc,
            mode='markers',
            marker=dict(size=15, color='yellow'),
            name='Arima Office',
            text='Arima Office',
            hoverinfo='text'
        )
    )


    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": 43.65569205940113, "lon": -79.38679602617921}, 
        mapbox_zoom=18,
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            font=dict(size=18)
        ),
    )
    return fig


# Calculations for scorecards
# total_locations = filtered_df.shape[0]
# total_revenue = filtered_df['properties.REVENUE'].sum()
# total_customers = filtered_df['properties.CUSTOMERS'].sum()
# total_donuts_sold = filtered_df['properties.DONUTS_SOLD'].sum()
# average_distance =  filtered_df['properties.DISTANCE'].mean()
# average_walk_time = filtered_df['properties.WALKTIME'].mean()
# average_rating = filtered_df['properties.RATING'].mean()
# count_chains = filtered_df['properties.CHAIN_NAME'].value_counts()
# grouped_df = (filtered_df.groupby('properties.NAME', as_index=False)['properties.REVENUE'].sum().sort_values(by='properties.REVENUE', ascending=False))
# grouped_df1 = (filtered_df.groupby('properties.CHAIN_NAME', as_index=False)['properties.REVENUE'].sum().sort_values(by='properties.REVENUE', ascending=False))


# fig1 = px.bar(grouped_df, 
#               x='properties.NAME', 
#               y='properties.REVENUE', 
#               title='Coffee Shop Revenue',
#               labels={'properties.NAME': 'Coffee Shops', 'properties.REVENUE': 'Revenue ($)'})

# fig2 = px.pie(filtered_df, names="properties.CHAIN_NAME", 
#              title="Number of Chains vs. Independent Coffee Shops",
#                color_discrete_sequence=['#636EFA', '#EF553B'])

# fig3 = px.pie(grouped_df1, names="properties.CHAIN_NAME", 
#              title="Revenue by Coffee Shops",
#                color_discrete_sequence=['#636EFA', '#EF553B'])              

app.layout = html.Div([
    html.H1(
        "Coffee Shops Close to the Arima Office (5, 10, 15 min. Walk Times) ",
        style={
            'textAlign': 'center',
            'marginTop': '20px',
            'marginBottom': '20px',
            'fontSize': '48px',
            'fontFamily': 'Arial, sans-serif',
            'fontWeight': 'bold',
            'color': '#333'
        }
    ),
    html.P(""),
    dcc.Dropdown(
        id='walk-time-dropdown',
        options=[
            {'label': 'ALL', 'value': 'all'},
            {'label': 'UNDER 5 MINS.', 'value': '5'},
            {'label': 'UNDER 10 MINS.', 'value': '10'},
            {'label': 'UNDER 15 MINS.', 'value': '15'}
    ],
    value='all',  # default value
    clearable=False,
    style={'width': '200px', 'margin': '0 auto 20px auto', 'fontSize': '18px','fontWeight' : 'bold'}
    ),

        # --- SCORECARD SECTION ---
    html.Div([
        html.Div([
            html.H3("Coffee Shops", style={"fontsize": "24px", "fontWeight": "bold"}),
            html.P(id="scorecard-shops", style={"fontSize": "42px", "fontWeight": "bold"})
        ], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([
            html.H3("Total Revenue", style={"fontsize": "24px", "fontWeight": "bold"}),
            html.P(id="scorecard-revenue", style={"fontSize": "42px", "fontWeight": "bold"})
        ], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([
            html.H3("Total Customers", style={"fontsize": "24px", "fontWeight": "bold"}),
            html.P(id="scorecard-customers", style={"fontSize": "42px", "fontWeight": "bold"})
        ], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([
            html.H3("Donuts Sold", style={"fontsize": "24px", "fontWeight": "bold"}),
            html.P(id="scorecard-donuts", style={"fontSize": "42px", "fontWeight": "bold"})
        ], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([
            html.H3("Average Distance (M)", style={"fontsize": "24px", "fontWeight": "bold"}),
            html.P(id="scorecard-distance", style={"fontSize": "42px", "fontWeight": "bold"})
        ], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),
        html.Div([
            html.H3("Average Rating", style={"fontsize": "24px", "fontWeight": "bold"}),
            html.P(id="scorecard-rating", style={"fontSize": "42px", "fontWeight": "bold"})
        ], style={"padding": "10px", "margin": "5px", "background": "#f9f9f9", "border": "2px solid #333", "borderRadius": "5px", "textAlign": "center", "width": "200px"}),    
], style={"display": "flex", "justifyContent": "center", "marginBottom": "30px"}),   

    # Add the graph to the layout
    dcc.Graph(id='map-graph', style={'height': '80vh'}),
    dcc.Graph(id='bar-graph'),
    html.Div([
        dcc.Graph(id='pie-graph'),
        dcc.Graph(id='pie-graph-2'),
    ], style={"display": "flex", "justifyContent": "center", "alignItems": "stretch", "gap": "20px"}),
    dcc.Graph(id='scatter-graph'),
    html.Div([
    ], style={"display": "flex", "justifyContent": "center", "alignItems": "stretch", "gap": "20px"}),
    dcc.Graph(id='scatter-graph-2'),

    dcc.Input(id='user-input', type='text', placeholder='Ask a question about the data...', style={'width': '80%', 'margin': '20px auto', 'fontSize': '18px'}),
    html.Button('Submit', id='submit-button', n_clicks=0, style={'display': 'block', 'margin': '0 auto', 'fontSize': '18px', 'fontWeight': 'bold'}),
    html.Div(id='chat-response', style={'whiteSpace': 'pre-line', 'margin': '20px', 'fontSize': '18px'}),
])

@app.callback(
    [
        Output('map-graph', 'figure'),
        Output('scorecard-shops', 'children'),
        Output('scorecard-revenue', 'children'),
        Output('scorecard-customers', 'children'),
        Output('scorecard-donuts', 'children'),
        Output('scorecard-distance', 'children'),
        Output('scorecard-rating', 'children'),
        Output('bar-graph', 'figure'),
        Output('pie-graph', 'figure'),
        Output('pie-graph-2', 'figure'),
        Output('scatter-graph', 'figure'),
        Output('scatter-graph-2', 'figure'),
    ],
    [
        Input('walk-time-dropdown', 'value'),
    ]
)
def update_output(selected_walk_time):
    posthog.capture(
        distinct_id='user-id',  # Replace with actual user ID
        event='dropdown-changed',
        properties={'selected_value': selected_walk_time}
    )
    return update_dashboard(selected_walk_time)

def update_dashboard(selected_walk_time):
    if selected_walk_time == 'all':
        filtered_df = locations_df
    elif selected_walk_time == '15':
        filtered_df = locations_df[locations_df['properties.WALKTIME'].astype(str).isin(['5', '10', '15'])]
    else:
        filtered_df = locations_df[locations_df['properties.WALKTIME'].astype(str) == selected_walk_time]
                                                                                      
    # Scorecard calculations
    total_locations = filtered_df.shape[0]
    total_revenue = filtered_df['properties.REVENUE'].sum()
    total_customers = filtered_df['properties.CUSTOMERS'].sum()
    total_donuts_sold = filtered_df['properties.DONUTS_SOLD'].sum()
    average_distance = filtered_df['properties.DISTANCE'].mean()
    average_rating = filtered_df['properties.RATING'].mean()

    grouped_df = (
        filtered_df.groupby('properties.NAME', as_index=False)['properties.REVENUE']
        .sum().sort_values(by='properties.REVENUE', ascending=False)
        .rename(columns={'properties.NAME': 'Coffee Shop', 'properties.REVENUE': 'Revenue ($)'})
    )
    grouped_df1 = (
        filtered_df.groupby('properties.CHAIN_NAME', as_index=False)['properties.REVENUE']
        .sum().sort_values(by='properties.REVENUE', ascending=False)
    )

    top5_names = (filtered_df.groupby('properties.NAME')['properties.REVENUE']
                  .sum()
                  .sort_values(ascending=False)
                  .head(5)
                  .index
    )
    top5_df = filtered_df[filtered_df['properties.NAME'].isin(top5_names)]


    fig1 = px.bar(grouped_df, x='Coffee Shop', y='Revenue ($)', title='Coffee Shop Revenue')
    fig2 = px.pie(filtered_df, names="properties.CHAIN_NAME", title="Market Share by Location Counts")
    fig3 = px.pie(grouped_df1, names="properties.CHAIN_NAME", values="properties.REVENUE", title="Market Share by Revenue")
    fig4 = px.scatter(top5_df, x='properties.DISTANCE', y='properties.REVENUE', size='properties.CUSTOMERS', color='properties.NAME', hover_name='properties.NAME', log_x=False, size_max=40,
                      title='Top 5 Coffee Chains by Revenue - Customer Counts',
                      labels={'properties.DISTANCE': 'Distance', 'properties.REVENUE': 'Revenue ($)', 'properties.CUSTOMERS': 'Customers', 'properties.NAME': 'Coffee Shop'})   
    fig5 = px.scatter(top5_df, x='properties.DISTANCE', y='properties.REVENUE', size='properties.DONUTS_SOLD', color='properties.NAME', hover_name='properties.NAME', log_x=False, size_max=40,
                      title='Top 5 Coffee Chains by Revenue - Donuts Sold',
                      labels={'properties.DISTANCE': 'Distance', 'properties.REVENUE': 'Revenue ($)', 'properties.DONUTS_SOLD': 'Donuts Sold', 'properties.NAME': 'Coffee Shop'}) 

    # If you want a third chart, use grouped_df1


    # Map
    fig_map = create_map(selected_walk_time)

    return (
        fig_map, # Map figure
        f"{total_locations}", #scorecard-shops
        f"${total_revenue}", #scorecard-shops
        f"{total_customers}", #scorecard-shops
        f"{total_donuts_sold}", #scorecard-shops
        f"{average_distance:.1f}", #scorecard-shops
        f"{average_rating:.0f} Stars", #scorecard-shops
        fig1, #bar-graph all stores
        fig2, #pie-graph chains vs independents
        fig3, #pie-graph-2 revenue by coffee shops
        fig4, #scatter-graph distance vs revenue - customer counts bubble chart
        fig5, #scatter-graph-2 top 5 coffee chains by revenue - donuts sold bubble chart
    )

@app.callback(
    Output("chat-response", "children"),
    Input("user-input", "value"),
)
def handle_chat(user_msg):
    if not user_msg:
        raise dash.exceptions.PreventUpdate
    answer = call_notebooklm(user_msg)  # your function
    return answer or "No answer received."

@app.callback(
    Output("chat-output", "children"),
    Input("chat-input", "value")
)
def handle_chat(user_msg):
    try:
        if not user_msg:
            raise dash.exceptions.PreventUpdate
        
        # Your NotebookLM call here
        response = call_notebooklm_api(notebook_id="515420a1-c679-4948-9b5c-a9e729e529e6", query=user_msg)  # NotebookLM ID added
        return response
        
    except Exception as e:
        print(f"ERROR: {str(e)}")  # This will show in Render logs
        return f"Error: {str(e)}"  # This shows in UI

def handle_chat(user_msg):
    return f"Echo: {user_msg} (NotebookLM pending admin approval)"

if __name__ == "__main__":
    app.run(debug=True)
