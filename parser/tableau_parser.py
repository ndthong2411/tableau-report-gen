# parser/tableau_parser.py

import zipfile
import os
import pandas as pd
import xml.etree.ElementTree as ET
from tableauhyperapi import HyperProcess, Connection, Telemetry
from io import BytesIO
import re
import logzero
from logzero import logger, logfile


class TableauWorkbookParser:
    def __init__(self, twbx_file):
        self.twbx_file = twbx_file
        self.metadata = {}
        self.data = {}
        self.twb_content = None  # To store the extracted .twb content

    def decompress_twbx(self):
        try:
            with zipfile.ZipFile(self.twbx_file, 'r') as z:
                # Find the .twb file within the .twbx archive
                twb_files = [f for f in z.namelist() if f.endswith('.twb')]
                if not twb_files:
                    logger.error("No .twb file found in the .twbx archive.")
                    return
                twb_file = twb_files[0]  # Assuming only one .twb file
                with z.open(twb_file) as twb:
                    self.twb_content = twb.read()
                    logger.info(f"Extracted .twb file: {twb_file}")
        except zipfile.BadZipFile:
            logger.error("The provided file is not a valid .twbx archive.")
        except Exception as e:
            logger.error(f"An error occurred while decompressing the .twbx file: {e}")

    def parse_twb(self):
        if not self.twb_content:
            logger.error("No .twb content to parse. Ensure decompression is done first.")
            return

        try:
            # Parse the XML structure from in-memory bytes
            tree = ET.ElementTree(ET.fromstring(self.twb_content))
            root = tree.getroot()

            # Extract namespaces
            namespaces = self.get_namespaces(root)
            logger.info(f"Namespaces found: {namespaces}")

            # Extract version information from the root attributes
            self.metadata['version'] = root.attrib.get('version', 'Unknown')
            self.metadata['source_platform'] = root.attrib.get('source-platform', 'Unknown')
            self.metadata['source_build'] = root.attrib.get('source-build', 'Unknown')
            logger.info(f"Tableau Version: {self.metadata['version']}")

            # Extract calculated fields
            self.metadata['calculated_fields'] = self.extract_calculated_fields(root, namespaces)

            # Extract worksheets
            self.metadata['worksheets'] = self.extract_worksheets(root, namespaces)

            # Extract dashboards
            self.metadata['dashboards'] = self.extract_dashboards(root, namespaces)

            # Extract data sources
            self.data['data_sources'] = self.extract_data_sources(root, namespaces)

            logger.info("Parsing of .twb file completed successfully.")
        except ET.ParseError as pe:
            logger.error(f"Error parsing XML: {pe}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during parsing: {e}")

    def get_namespaces(self, root):
        namespaces = dict([
            node for _, node in ET.iterparse(
                BytesIO(self.twb_content), events=['start-ns']
            )
        ])
        logger.info(f"Registered namespaces: {namespaces}")
        return namespaces

    def extract_calculated_fields(self, root, namespaces):
        calculated_fields = []
        column_tag = './/{{{}}}column'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/column'
        for column in root.findall(column_tag):
            calc_tag = './/{{{}}}calculation'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/calculation'
            calc = column.find(calc_tag)
            if calc is not None and calc.attrib.get('class') == 'tableau':
                field_name = column.attrib.get('caption', 'Unknown Field')
                formula = calc.attrib.get('formula', '')
                alias_tag = './/{{{}}}alias'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/alias'
                alias = column.find(alias_tag)
                alias_value = alias.attrib.get('value') if alias is not None else ''
                datasource_tag = './/{{{}}}datasource-dependencies'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/datasource-dependencies'
                datasource_dependencies = column.find(datasource_tag)
                data_source_name = datasource_dependencies.attrib.get('datasource') if datasource_dependencies is not None else 'Unknown Source'
                
                # Extract dependencies from the formula using regex (assuming column names are within square brackets)
                dependencies = re.findall(r'\[([^\]]+)\]', formula)
                
                calculated_fields.append({
                    'Field Name': field_name,
                    'Formula': formula,
                    'Alias': alias_value,
                    'Data Source': data_source_name,
                    'Dependencies': dependencies
                })
        df_calculated = pd.DataFrame(calculated_fields)
        logger.info(f"Extracted {len(df_calculated)} calculated fields.")
        return df_calculated

    def extract_worksheets(self, root, namespaces):
        worksheets_info = []
        worksheet_tag = './/{{{}}}worksheet'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/worksheet'
        datasource_tag = './/{{{}}}datasource-dependencies'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/datasource-dependencies'
        for worksheet in root.findall(worksheet_tag):
            ws_name = worksheet.attrib.get('name', 'Unnamed Worksheet')
            datasource_dependencies = worksheet.find(datasource_tag)
            if datasource_dependencies is not None:
                for column in datasource_dependencies.findall('.//{{{}}}column'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/column'):
                    column_name = column.attrib.get('caption', 'Unknown Column')
                    data_source = datasource_dependencies.attrib.get('datasource', 'Unknown Source')
                    datatype = column.attrib.get('datatype', 'Unknown')
                    role = column.attrib.get('role', 'Unknown')
                    worksheets_info.append({
                        'Worksheet Name': ws_name,
                        'Column Name': column_name,
                        'Data Source': data_source,
                        'Datatype': datatype,
                        'Role': role
                    })
            else:
                worksheets_info.append({
                    'Worksheet Name': ws_name,
                    'Column Name': 'No Data Source',
                    'Data Source': 'None',
                    'Datatype': 'N/A',
                    'Role': 'N/A'
                })
        df_worksheets = pd.DataFrame(worksheets_info)
        logger.info(f"Extracted information for {len(df_worksheets['Worksheet Name'].unique())} worksheets.")
        return df_worksheets

    def extract_dashboards(self, root, namespaces):
        dashboards_info = []
        dashboard_tag = './/{{{}}}dashboard'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/dashboard'
        dashboards_found = root.findall(dashboard_tag)
        logger.info(f"Number of dashboards found: {len(dashboards_found)}")
        
        for dashboard in dashboards_found:
            dashboard_name = dashboard.attrib.get('name', 'Unnamed Dashboard')
            worksheets_tag = './/{{{}}}worksheet'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/worksheet'
            worksheets = dashboard.findall(worksheets_tag)
            logger.info(f"Dashboard '{dashboard_name}' has {len(worksheets)} worksheets.")
            
            for ws in worksheets:
                ws_name = ws.attrib.get('name', 'Unnamed Worksheet')
                dashboards_info.append({
                    'Dashboard Name': dashboard_name,
                    'Worksheet Used': ws_name,
                    'Metadata': 'Additional metadata can be added here'
                })
        
        if not dashboards_info:
            logger.warning("No dashboards information extracted. Check if the XML contains <dashboard> elements with 'name' attributes.")
        
        df_dashboards = pd.DataFrame(dashboards_info)
        logger.info(f"Extracted information for {len(df_dashboards['Dashboard Name'].unique())} dashboards.")
        return df_dashboards

    def extract_data_sources(self, root, namespaces):
        data_sources = {}
        datasource_tag = './/{{{}}}datasource'.format(namespaces.get('tableau', '')) if 'tableau' in namespaces else './/datasource'
        for ds in root.findall(datasource_tag):
            ds_name = ds.attrib.get('name', 'Unnamed DataSource')
            ds_file = ds.attrib.get('file', None)
            if ds_file:
                hyper_file_path = os.path.join(os.path.dirname(self.twbx_file), ds_file)
                df = self.read_hyper_file(hyper_file_path)
                data_sources[ds_name] = df if df is not None else 'Placeholder for connection-only data source'
            else:
                data_sources[ds_name] = 'Placeholder for connection-only data source'
        logger.info(f"Extracted {len(data_sources)} data sources.")
        return data_sources

    def read_hyper_file(self, hyper_file_path):
        try:
            with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
                with Connection(endpoint=hyper.endpoint, database=hyper_file_path) as connection:
                    catalog = connection.catalog
                    schemas = catalog.get_schema_names()
                    for schema in schemas:
                        tables = catalog.get_table_names(schema=schema)
                        for table in tables:
                            logger.info(f"Reading data from table: {table}")
                            query = f"SELECT * FROM {table}"
                            data_frame = connection.execute_list_query(query)
                            columns = [col.name for col in catalog.get_table_definition(table).columns]
                            df = pd.DataFrame(data_frame, columns=columns)
                            return df  # Assuming one table per .hyper file
            return None
        except Exception as e:
            logger.error(f"Failed to read .hyper file {hyper_file_path}: {e}")
            return None

    def get_report(self):
        return {
            'metadata': self.metadata,
            'data': self.data
        }
