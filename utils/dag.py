# utils/dag.py

import networkx as nx
import logzero
from logzero import logger

def generate_dag(calculated_fields_df, original_fields_df, data_sources_df):
    G = nx.DiGraph()

    # Add data sources as nodes
    for _, ds in data_sources_df.iterrows():
        G.add_node(ds['Caption'], type='Data Source')

    # Add original fields as nodes and connect to data sources
    for _, field in original_fields_df.iterrows():
        G.add_node(field['Field Name'], type='Original Field')
        # Connect to data source
        if field['Data Source Caption'] != 'Unknown Source':
            G.add_edge(field['Data Source Caption'], field['Field Name'])

    # Add calculated fields as nodes and connect to dependencies
    for _, calc in calculated_fields_df.iterrows():
        G.add_node(calc['Field Name'], type='Calculated Field')
        # Connect to data source
        if calc['Data Source Caption'] != 'Unknown Source':
            G.add_edge(calc['Data Source Caption'], calc['Field Name'])
        # Connect to dependencies
        for dep in calc['Dependencies']:
            G.add_edge(dep, calc['Field Name'])

    logger.info("Dependency DAG generated successfully.")
    return G
