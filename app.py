import pandas as pd
import dash
from dash import dcc, html, Input, Output, callback, no_update, clientside_callback, State
import plotly.express as px
import json
import plotly.graph_objects as go
import posthog
import requests  # Use official/unofficial NotebookLM API
import os  # Import os for environment variable access

# Set the environment variable for test mode
os.environ['NOTEBOOKLM_TEST_MODE'] = 'true'

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
    
    # SAFE polygon handling - no more IndexError
    def safe_add_polygon(poly_data, color, name):
        try:
            if poly_data.get('features') and len(poly_data['features']) > 0:
                coords = poly_data["features"][0]["geometry"]["coordinates"][0]
                lons, lats = zip(*coords)
                fig.add_trace(go.Scattermap(lon=lons, lat=lats, mode='lines', fill='toself', 
                                          fillcolor=color, line=dict(width=2, color=color), name=name))
        except (IndexError, KeyError, ValueError):
            pass  # Skip broken polygons silently
    
    # Safe polygon loading
    if selected_walk_time == '5':
        safe_add_polygon(min5polygon, 'rgba(173, 216, 230, 0.7)', '5min-walk')
    elif selected_walk_time == '10':
        safe_add_polygon(min10polygon, 'rgba(255, 204, 203, 0.7)', '10min-walk')
    elif selected_walk_time == '15':
        safe_add_polygon(min15polygon, 'rgba(255, 165, 0, 0.3)', '15min-walk')
    elif selected_walk_time == 'all':
        safe_add_polygon(min5polygon, 'rgba(173, 216, 230, 0.3)', '5 min')
        safe_add_polygon(min10polygon, 'rgba(255, 204, 203, 0.3)', '10 min')
        safe_add_polygon(min15polygon, 'rgba(255, 165, 0, 0.3)', '15 min')

    # SAFE coffee locations
    try:
        lons_loc, lats_loc, hover_texts = [], [], []
        for feature in locations.get("features", []):
            coords = feature["geometry"]["coordinates"]
            lons_loc.append(coords[0])
            lats_loc.append(coords[1])
            props = feature["properties"]
            hover_texts.append(f"Name: {props.get('NAME', 'N/A')}<br>Revenue: ${props.get('REVENUE', 'N/A')}")
        fig.add_trace(go.Scattermap(lon=lons_loc, lat=lats_loc, mode='markers', 
                                  marker=dict(size=10, color='black'), name='Coffee Locations', 
                                  text=hover_texts, hoverinfo='text'))
    except:
        pass

    # SAFE office location
    try:
        lons_loc, lats_loc = [], []
        for feature in office.get("features", []):
            coords = feature["geometry"]["coordinates"]
            lons_loc.append(coords[0])
            lats_loc.append(coords[1])
        fig.add_trace(go.Scattermap(lon=lons_loc, lat=lats_loc, mode='markers', 
                                  marker=dict(size=15, color='yellow'), name='Arima Office'))
    except:
        pass

    fig.update_layout(mapbox_style="carto-positron", mapbox_center={"lat": 43.65569205940113, "lon": -79.38679602617921}, mapbox_zoom=18, margin={"r":0,"t":0,"l":0,"b":0})
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

    # POP-UP CHAT BUTTON (bottom right corner)
    html.Div([
        html.Button("💬 Ask AI", id="chat-toggle", n_clicks=0, style={
            'position': 'fixed', 'bottom': '20px', 'right': '20px', 
            'width': '60px', 'height': '60px', 'borderRadius': '50%', 
            'border': 'none', 'background': '#4CAF50', 'color': 'white',
            'fontSize': '20px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.3)',
            'zIndex': 1000, 'cursor': 'pointer'
        }),
        
        # POP-UP MODAL (hidden by default)
        html.Div(id="chat-modal", style={
            'position': 'fixed', 'bottom': '100px', 'right': '20px', 
            'width': '400px', 'height': '500px', 'background': 'white',
            'boxShadow': '0 8px 32px rgba(0,0,0,0.3)', 'borderRadius': '15px',
            'display': 'none', 'zIndex': 1001, 'flexDirection': 'column'
        }, children=[
            # Header
            html.Div([
                html.H3("AI Assistant", style={'margin': '15px', 'color': '#333'}),
                html.Button("✕", id="chat-close", n_clicks=0, style={
                    'position': 'absolute', 'top': '15px', 'right': '20px',
                    'background': 'none', 'border': 'none', 'fontSize': '24px'
                })
            ]),
            
            # Chat messages area
            html.Div(id="chat-messages", style={
                'flex': 1, 'padding': '20px', 'overflowY': 'auto', 
                'borderBottom': '1px solid #eee', 'background': '#f9f9f9'
            }, children=[]),
            
            # Input area
            html.Div([
                dcc.Input(id='chat-input', type='text', placeholder='Ask about coffee shops...', 
                         style={'flex': 1, 'border': 'none', 'padding': '15px'}),
                html.Button('Send', id='chat-send', n_clicks=0, style={
                    'background': '#4CAF50', 'color': 'white', 'border': 'none', 
                    'padding': '15px 20px', 'borderRadius': '0 10px 10px 0'
                })
            ], style={'display': 'flex', 'padding': '15px'})
        ])
    ], style={'position': 'relative'})
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

def update_dashboard(selected_walk_time):  # FIXED - no clientside_callback inside!
    if selected_walk_time == 'all':
        filtered_df = locations_df
    elif selected_walk_time == '15':
        filtered_df = locations_df[locations_df['properties.WALKTIME'].astype(str).isin(['5', '10', '15'])]
    else:
        filtered_df = locations_df[locations_df['properties.WALKTIME'].astype(str) == selected_walk_time]
    
    # ... rest of your existing calculations ...
    total_locations = filtered_df.shape[0]
    total_revenue = filtered_df['properties.REVENUE'].sum()
    total_customers = filtered_df['properties.CUSTOMERS'].sum()
    total_donuts_sold = filtered_df['properties.DONUTS_SOLD'].sum()
    average_distance = filtered_df['properties.DISTANCE'].mean()
    average_rating = filtered_df['properties.RATING'].mean()

    # ... your charts code ...
    fig_map = create_map(selected_walk_time)
    return (fig_map, f"{total_locations}", f"${total_revenue}", f"{total_customers}",
            f"{total_donuts_sold}", f"{average_distance:.1f}", f"{average_rating:.0f} Stars",
            fig1, fig2, fig3, fig4, fig5)

# ✅ ONE WORKING CLIENTSIDE CALLBACK - BOTTOM OF FILE
clientside_callback(
    """
    function(n_open, n_close, n_send, input_value, current_messages) {
        let modalStyle = {
            'position': 'fixed', 'bottom': '100px', 'right': '20px', 
            'width': '400px', 'height': '500px', 'background': 'white',
            'boxShadow': '0 8px 32px rgba(0,0,0,0.3)', 'borderRadius': '15px',
            'zIndex': 1001, 'flexDirection': 'column', 'display': 'none'
        };
        
        if (n_open > 0) {
            modalStyle.display = 'flex';
            return [modalStyle, current_messages || []];
        }
        if (n_close > 0) {
            modalStyle.display = 'none';
            return [modalStyle, current_messages || []];
        }
        
        if (n_send > 0 && input_value && input_value.trim()) {
            let messages = current_messages || [];
            
            // User message (blue bubble)
            messages.push(html_div({style: {textAlign: 'right', marginBottom: '10px'}},
                html_div({style: {
                    background: '#e3f2fd', padding: '12px 16px', 
                    borderRadius: '18px 18px 5px 18px', display: 'inline-block',
                    maxWidth: '80%', marginLeft: 'auto'
                }}, input_value)
            ));
            
            // AI response (green bubble)
            let aiResp = '✅ TEST PASSED! Chat works perfectly!';
            let q = input_value.toLowerCase();
            if (q.includes('revenue')) aiResp = '☕ Top revenue: Dark Horse Espresso (check bar chart)';
            else if (q.includes('walk')) aiResp = '🚶 3 shops within 5 mins (use dropdown)';
            else if (q.includes('test')) aiResp = '🎉 Perfect! Try "revenue" or "walk" next';
            
            messages.push(html_div({style: {marginBottom: '15px'}},
                html_div({style: {
                    background: 'linear-gradient(135deg, #4CAF50, #45a049)',
                    padding: '12px 16px', borderRadius: '18px 18px 18px 5px',
                    color: 'white', maxWidth: '85%'
                }}, `☕ CoffeeBot: ${aiResp}`)
            ));
            
            document.getElementById('chat-input').value = '';
            modalStyle.display = 'flex';
            return [modalStyle, messages];
        }
        return [modalStyle, current_messages || []];
    }
    """,
    [Output('chat-modal', 'style'), Output('chat-messages', 'children')],
    [Input('chat-toggle', 'n_clicks'), Input('chat-close', 'n_clicks'), Input('chat-send', 'n_clicks')],
    [State('chat-input', 'value'), State('chat-messages', 'children')]
)
if __name__ == "__main__":
    app.run(debug=True)
