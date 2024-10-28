import streamlit as st
import networkx as nx
import pandas as pd
from utils import ECOSAGraph, load_data

st.title("ECOSA Graph Visualization")

if 'data' not in st.session_state:
    st.session_state['data'] = load_data('ECOSA.xlsm')

policy_domain = st.selectbox("Choose Policy Domain", st.session_state['data']['Policy Domain'].unique())
form_of_cooperation = st.selectbox("Choose Form of Cooperation", st.session_state['data']['Form of Cooperation'].unique())

if 'policy_domain' not in st.session_state:
    st.session_state['policy_domain'] = None
if 'form_of_cooperation' not in st.session_state:
    st.session_state['form_of_cooperation'] = None

if st.button("Confirm filter"):
    st.session_state['policy_domain'] = policy_domain
    st.session_state['form_of_cooperation'] = form_of_cooperation
 
if st.button("Reset"):
    st.session_state['policy_domain'] = None
    st.session_state['form_of_cooperation'] = None

layout = st.selectbox("Choose Layout", 
                      [
                          nx.spring_layout, 
                          nx.spiral_layout, 
                          nx.spectral_layout, 
                          nx.shell_layout, 
                          nx.random_layout,
                          nx.kamada_kawai_layout,
                        ],
                        format_func=lambda x: x.__name__.replace('_', ' ').title() 
                )

filtered_data = st.session_state['data'][
    (st.session_state['data']['Policy Domain'] == policy_domain) &
    (st.session_state['data']['Form of Cooperation'] == form_of_cooperation)
] if st.session_state['policy_domain'] and st.session_state['form_of_cooperation'] else st.session_state['data']

egraph = ECOSAGraph(filtered_data)
graph = egraph.create_graph()
fig = egraph.plot_graph(layout_fn=layout)
event = st.plotly_chart(fig, on_select="rerun") 
if event:
    selection = event['selection']
    for point in selection['points']:
        name = point['text'].split("has")[0].strip()
        agreements = filtered_data[filtered_data['Parties'].str.contains(name, regex=False)].to_dict(orient='records')
        for agreement in agreements:
            with st.expander(agreement['Title'], expanded=False):
                st.write("**Date**: ", agreement["Date"].strftime('%Y-%m-%d'))
                st.write("**Parties**: ", agreement["Parties"])
                st.write("**Sector**: ",agreement["Sector"])
                st.write("**Policy Domain**: ",agreement["Policy Domain"])
                st.write("**Form of Cooperation**: ", agreement["Form of Cooperation"])
                st.write("**Quote(s)**: ", agreement["Quote(s)"])
                st.write("**Military Alliance**: ", agreement["Military Alliance"])
                st.write("**Free Trade Agreement**: ", agreement["Free Trade Agreement"])
                if pd.isna(agreement["Corpus"]):
                    st.write("#### Corpus")
                    st.write(agreement["Corpus"])