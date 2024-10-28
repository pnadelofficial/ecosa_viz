import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import inspect

def load_data(file_path):
    df = pd.read_excel(file_path, sheet_name='Master sheet')
    return df

class ECOSAGraph:
    def __init__(self, df):
        self.df = df
        self.graph = None
    
    def get_nodes(self):
        parties = self.df.Parties.dropna()
        unique_parties = []
        for party in parties.str.split(',', expand=True).stack().unique():
            unique_parties.append(party.strip())
        return unique_parties

    def get_edges(self):
        edges = []
        records = self.df.to_dict('records')
        for record in records:
            raw_parties = record['Parties']
            if pd.isna(raw_parties):
                continue
            attrs = {
                'title': record['Title'],
                'date': record['Date'].strftime('%Y-%m-%d'), # was tter
                'sector': record['Sector'],
                'policy_domain': record['Policy Domain'],
                'form_of_cooperation': record['Form of Cooperation'],
                'quotes': record['Quote(s)'],
                'military_alliance': record['Military Alliance'],
                'free_trade_agreement': record['Free Trade Agreement']
            }
            parties = [p.strip() for p in raw_parties.split(',')]
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

    def plot_graph(self, layout_fn=nx.spring_layout):
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
                    title='Node Connections',
                    xanchor='left',
                    titleside='right'
                )
            )
        )

        node_adjacencies = []
        node_text = []
        for node, adjacencies in enumerate(self.graph.adjacency()):
            node_name = list(self.graph.nodes)[node]
            node_adjacencies.append(len(adjacencies[1]))
            node_text.append(f'{node_name} has connections: {str(len(adjacencies[1]))}')

        node_trace.marker.color = node_adjacencies
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
