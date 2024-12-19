# utils/dag.py

import pandas as pd
import networkx as nx
import logzero
from logzero import logger

def generate_dag(calculated_fields_df, original_fields_df, data_sources_df, selected_worksheet=None):
    G = nx.DiGraph()

    # Add Data Sources
    for _, ds in data_sources_df.iterrows():
        data_source_name = ds.get('Caption', 'Unknown Data Source')
        if data_source_name is None or (isinstance(data_source_name, float) and pd.isna(data_source_name)):
            data_source_name = 'Unknown Data Source'
        data_source_name = str(data_source_name)
        G.add_node(data_source_name, type='Data Source')

    # Filter based on selected worksheet if provided
    if selected_worksheet and selected_worksheet != "All":
        # Get columns related to the selected worksheet
        worksheet_columns = original_fields_df[original_fields_df['Worksheet Name'] == selected_worksheet]['Field Name'].tolist()
        # Also include calculated fields used in this worksheet
        calculated_in_ws = calculated_fields_df[calculated_fields_df['Dependencies'].apply(lambda deps: any(dep in worksheet_columns for dep in deps))]['Field Name'].tolist()
    else:
        worksheet_columns = original_fields_df['Field Name'].tolist()
        calculated_in_ws = calculated_fields_df['Field Name'].tolist()

    # Add Original Fields
    for _, field in original_fields_df.iterrows():
        field_name = field.get('Field Name', 'Unknown Original Field')
        data_source_caption = field.get('Data Source Caption', 'Unknown Source')

        if selected_worksheet and selected_worksheet != "All" and field_name not in worksheet_columns:
            continue  # Skip fields not in the selected worksheet

        if field_name is None or (isinstance(field_name, float) and pd.isna(field_name)):
            field_name = 'Unknown Original Field'
        data_source_caption = str(data_source_caption)

        G.add_node(field_name, type='Original Field')
        if data_source_caption != 'Unknown Source':
            G.add_edge(data_source_caption, field_name, label='originates_from')

    # Add Calculated Fields
    for _, calc in calculated_fields_df.iterrows():
        calc_field_name = calc.get('Field Name', 'Unknown Calculated Field')
        data_source_caption = calc.get('Data Source Caption', 'Unknown Source')
        dependencies = calc.get('Dependencies', [])

        if selected_worksheet and selected_worksheet != "All" and calc_field_name not in calculated_in_ws:
            continue  # Skip calculated fields not used in the selected worksheet

        if calc_field_name is None or (isinstance(calc_field_name, float) and pd.isna(calc_field_name)):
            calc_field_name = 'Unknown Calculated Field'
        data_source_caption = str(data_source_caption)

        G.add_node(calc_field_name, type='Calculated Field')
        if data_source_caption != 'Unknown Source':
            G.add_edge(data_source_caption, calc_field_name, label='originates_from')

        for dep in dependencies:
            if dep is None or (isinstance(dep, float) and pd.isna(dep)):
                dep = 'Unknown Dependency'
            dep = str(dep)
            G.add_edge(dep, calc_field_name, label='depends_on')

    logger.info("Dependency DAG generated successfully.")
    return G
