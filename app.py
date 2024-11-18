import streamlit as st
import networkx as nx
import pandas as pd
import re
from utils import ECOSAGraph, load_data, clean_cols

st.title("ECOSA Graph Visualization")

# TODO
## FTA/MA stats??
## Some consistancy in the data
## Automating Wayback Machine archiving

if 'data' not in st.session_state:
    df = load_data('ECOSA.xlsm')
    st.session_state['org_data'] = df

    df['Policy Domain'] = df.apply(lambda x: x['Policy Domain'].split(', '), axis=1)
    df['Sector'] = df.apply(lambda x: re.sub('\(.*\)', '', x['Sector']).split(', '), axis=1)
    df['Parties'] = df['Parties'].str.split(', ')
    df = df.explode('Policy Domain')
    df = df.explode('Sector')
    df = df.explode('Parties')
    df = clean_cols(df)
    st.session_state['data'] = df

policy_domain = st.multiselect("Choose Policy Domain", st.session_state['data']['Policy Domain'].unique(), placeholder="View all")
form_of_cooperation = st.multiselect("Choose Form of Cooperation", st.session_state['data']['Form of Cooperation'].unique(), placeholder="View all")
sector = st.multiselect("Choose Sector", st.session_state['data']['Sector'].unique(), placeholder="View all")
country = st.multiselect("Choose Country", st.session_state['data']['Parties'].unique(), placeholder="View all")
year = st.multiselect("Choose Year", st.session_state['data']['Date'].dt.year.unique(), placeholder="View all")

if policy_domain == []:
    policy_domain = list(st.session_state['data']['Policy Domain'].unique())
if form_of_cooperation == []:
    form_of_cooperation = list(st.session_state['data']['Form of Cooperation'].unique())
if sector == []:
    sector = list(st.session_state['data']['Sector'].unique())
if country == []:
    country = list(st.session_state['data']['Parties'].unique())
if year == []:
    year = list(st.session_state['data']['Date'].dt.year.unique())

filtered_data = st.session_state['data'][
    (st.session_state['data']['Policy Domain'].isin(policy_domain)) &
    (st.session_state['data']['Form of Cooperation'].isin(form_of_cooperation)) &
    (st.session_state['data']['Sector'].isin(sector)) &
    (st.session_state['data']['Parties'].isin(country)) &
    (st.session_state['data']['Date'].dt.year.isin(year))
] if policy_domain or form_of_cooperation or sector or year or country else st.session_state['data']

filtered_data = st.session_state['org_data'].iloc[list(set(filtered_data.index))]
egraph = ECOSAGraph(filtered_data)
graph = egraph.create_graph()
fig = egraph.plot_graph(layout_fn=nx.spring_layout, metric='Node')

# Remove these stats
# Replace with precalculated stats on these PER agreement
# fta_ma_fields = ['Yes ', 'No', 'Some members']  
# with st.expander("**Free Trade Agreements in selection**"):
#     st.write("**Note**: Percentages are calculated based number of edges in the selection.")
#     for key in fta_ma_fields:
#         val = (filtered_data['Free Trade Agreement'].value_counts()/len(filtered_data)).to_dict()[key]
#         st.write(f"{key}: {val*100:.2f}%")
# with st.expander("**Military Alliances in selection**"):
#     for key in fta_ma_fields:
#         val = (filtered_data['Military Alliance'].value_counts()/len(filtered_data)).to_dict()[key]
#         st.write(f"{key}: {val*100:.2f}%")

event = st.plotly_chart(fig, on_select="rerun") 
if event:
    selection = event['selection']
    if len(selection['points']) > 0:
        for point in selection['points']:
            name = point['text'].split("has")[0].strip()
            agreements = filtered_data[filtered_data['Parties'].str.contains(name, regex=False)].to_dict(orient='records')
            st.write(f"There are **{len(agreements)}** agreement(s) including **{name}**, in the selection:")
            degree_centrality = nx.degree_centrality(graph)[name]
            st.markdown(f"**Degree Centrality** in the network: {degree_centrality:.4f}", help="Degree centrality is a measure of how many connections a node has.") 
            betweenness_centrality = nx.betweenness_centrality(graph)[name]
            st.markdown(f"**Betweenness Centrality** in the network: {betweenness_centrality:.4f}", help="Betweenness centrality is a measure of how many shortest paths pass through a node.")
            
            last_title = ''
            for agreement in agreements:
                if agreement['Title'] != last_title:
                    with st.expander(agreement['Title'], expanded=False):
                        st.write("**Date**: ", agreement["Date"].strftime('%Y-%m-%d'))
                        st.write("**Parties**: ", ', '.join(agreement["Parties"]))
                        st.write("**Sector**: ",', '.join(agreement["Sector"]) if len(agreement["Sector"]) > 1 else agreement["Sector"][0])
                        st.write("**Policy Domain**: ",', '.join(agreement["Policy Domain"]) if len(agreement["Policy Domain"]) > 1 else agreement["Policy Domain"][0])
                        st.write("**Form of Cooperation**: ", agreement["Form of Cooperation"])
                        st.write("**Quote(s)**: ", agreement["Quote(s)"])
                        st.write("**Military Alliance**: ", agreement["Military Alliance"])
                        st.write("**Free Trade Agreement**: ", agreement["Free Trade Agreement"])
                        if not pd.isna(agreement["Corpus"]):
                            st.write("#### Corpus")
                            st.write(agreement["Corpus"])
                    last_title = agreement['Title']
    else:
        with st.expander("All agreements"):
            agreements = filtered_data.to_dict(orient='records')
            st.write(f"There are **{len(agreements)}** agreement(s) in the selection:")
            tabs = st.tabs([a['Title'] for a in agreements])
            for i, tab in enumerate(tabs):
                with tab:
                    agreement = agreements[i]
                    st.write("**Date**: ", agreement["Date"].strftime('%Y-%m-%d'))
                    st.write("**Parties**: ", ', '.join(agreement["Parties"]))
                    st.write("**Sector**: ",', '.join(agreement["Sector"]) if len(agreement["Sector"]) > 1 else agreement["Sector"][0])
                    st.write("**Policy Domain**: ",', '.join(agreement["Policy Domain"]) if len(agreement["Policy Domain"]) > 1 else agreement["Policy Domain"][0])
                    st.write("**Form of Cooperation**: ", agreement["Form of Cooperation"])
                    st.write("**Quote(s)**: ", agreement["Quote(s)"])
                    st.write("**Military Alliance**: ", agreement["Military Alliance"])
                    st.write("**Free Trade Agreement**: ", agreement["Free Trade Agreement"])
                    if not pd.isna(agreement["Corpus"]):
                        st.write("#### Corpus")
                        st.write(agreement["Corpus"])

