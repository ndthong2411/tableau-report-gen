# utils/dag.py

import networkx as nx
import plotly.graph_objects as go
import logzero
from logzero import logger


def generate_dag(calculated_fields_df):
    G = nx.DiGraph()
    
    for _, row in calculated_fields_df.iterrows():
        calculated_field = row['Field Name']
        dependencies = row['Dependencies']
        G.add_node(calculated_field, type='Calculated Field')
        for dep in dependencies:
            G.add_node(dep, type='Original Column')
            G.add_edge(dep, calculated_field)
    
    return G


def plot_dag(G):
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_color.append(1 if G.nodes[node]['type'] == 'Calculated Field' else 0)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="bottom center",
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Viridis',
            color=node_color,
            size=10,
            colorbar=dict(
                thickness=15,
                title='Type',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
    
    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='<br>DAG of Calculated Fields Dependencies',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="",
                    showarrow=False,
                    xref="paper", yref="paper") ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    return fig
