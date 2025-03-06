import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import inspect
import streamlit as st

def load_data(file_path):
    df = pd.read_excel(file_path, sheet_name='Master Sheet')
    return df

def clean_cols(df):
    df.columns = df.columns.str.strip()
    return df

def apply_css():
    return st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #f7f3e4;
    }
    [data-testid="stHeader"] {
        background-color: #f7f3e4;
    }       
    [data-testid="stSidebarContent"] {
        background-color:  #fbfaf2; 
    }
    div[data-baseweb="select"] > div {
        background-color:  #fbfaf2; 
    }
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #fbfaf2;
    }                  
    </style> 
    """.strip(), unsafe_allow_html=True) # alt for sidebar: #ece3c7 
 
def style_plotly(fig, bgcolor="#f7f3e4", gridcolor="gray"):
    fig.update_layout(
        paper_bgcolor=bgcolor,
        plot_bgcolor=bgcolor,
        font_color="black",
    )
    fig.update_xaxes(gridcolor=gridcolor, griddash='dot')
    fig.update_yaxes(gridcolor=gridcolor, griddash='dot')
    return fig

class ECOSAGraph:
    def __init__(self, df):
        self.df = df
        self.graph = None
    
    def get_nodes(self):
        parties = self.df.Parties.dropna()
        # unique_parties = []
        # for party in parties.str.split(';', expand=True).stack().unique():
        #     unique_parties.append(party.strip())
        return [e.strip() for e in parties.str.split(';', expand=True).stack().unique()]

    def get_edges(self):
        edges = []
        records = self.df.to_dict('records')
        for record in records:
            raw_parties = record['Parties']
            # if pd.isna(raw_parties):
            if len(raw_parties) == 0:
                print('empty')
                continue
            attrs = {
                'title': record['Title'],
                'date': record['Date'].strftime('%Y-%m-%d'), # was tter
                'sector': record['Sector'],
                'policy_domain': record['Policy Domain'],
                'form_of_cooperation': record['Form of Cooperation'],
                'quotes': record['Quotes'],
                'military_alliance': record['Military Alliance'],
                'free_trade_agreement': record['Free Trade Agreement']
            }
            if isinstance(raw_parties, str):
                parties = [p.strip() for p in raw_parties.split(';')]
            else:
                parties = [p.strip() for p in raw_parties]  
            for party in parties:
                for other_party in parties:
                    if party == other_party:
                        continue
                    if (other_party, party, attrs) in edges:
                        continue
                    edges.append((party, other_party, attrs))      
        return edges

    def create_graph(self): 
        self.graph = nx.Graph()
        nodes = self.get_nodes()
        edges = self.get_edges()

        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        return self.graph

    def plot_graph(self, layout_fn=nx.spring_layout, metric=None):
        if 'seed' in inspect.signature(layout_fn).parameters:
            pos = layout_fn(self.graph, seed=1997)
        else:
            pos = layout_fn(self.graph)
        nx.set_node_attributes(self.graph, pos, 'pos')

        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = self.graph.nodes[edge[0]]['pos']
            x1, y1 = self.graph.nodes[edge[1]]['pos']
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = [self.graph.nodes[node]['pos'][0] for node in self.graph.nodes()]
        node_y = [self.graph.nodes[node]['pos'][1] for node in self.graph.nodes()]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title=f'{metric} Centrality' if (metric == 'Degree') or (metric == 'Betweenness') else 'Node Connections',
                    xanchor='left',
                    titleside='right'
                )
            )
        )

        node_metric = []
        node_text = []
        if metric == 'Betweenness':
            for node in self.graph.nodes():
                bc = nx.betweenness_centrality(self.graph)[node]
                node_metric.append(bc)
                node_text.append(f'Betweenness Centrality: {bc:.4f}')
        elif metric == 'Degree':
            for node in self.graph.nodes():
                dc = nx.degree_centrality(self.graph)[node]
                node_metric.append(dc)
                node_text.append(f'Degree: {dc:.4f}')
        else:
            for node, adjacencies in enumerate(self.graph.adjacency()):
                node_name = list(self.graph.nodes)[node]
                node_metric.append(len(adjacencies[1]))
                node_text.append(f'{node_name} has connections: {str(len(adjacencies[1]))}')

        node_trace.marker.color = node_metric
        node_trace.text = node_text

        fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(

                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )
        return fig
