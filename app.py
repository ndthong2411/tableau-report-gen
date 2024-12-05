# app.py

import streamlit as st
import os
from parser.tableau_parser import TableauWorkbookParser
from utils.dag import generate_dag
from utils.report import generate_html_report, convert_html_to_pdf
from utils.helpers import image_to_base64
from components.uploader import file_uploader_component
import pandas as pd
import logzero
from logzero import logger
from datetime import datetime
from graphviz import Digraph

# Function to plot DAG using Graphviz
def plot_dag_graphviz(G):
    dot = Digraph(comment='Dependency DAG')
    for node in G.nodes:
        dot.node(node)
    for edge in G.edges:
        dot.edge(edge[0], edge[1])
    return dot

def main():
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logzero for app.log
    logzero.logfile("logs/app.log", maxBytes=1e6, backupCount=3)
    logger.info("Streamlit app started.")

    # Set Streamlit page configuration
    st.set_page_config(
        page_title="📊 Tableau Workbook Parser and Report Generator",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # App Title and Description
    st.title("📊 Tableau Workbook Parser and Report Generator")
    st.write("""
    Upload a Tableau Workbook (`.twbx` file) to parse its contents and generate comprehensive reports, 
    including version information, calculated fields, original fields, worksheets, and data sources. Additionally, visualize 
    dependencies between calculated fields and original columns using a Directed Acyclic Graph (DAG).
    """)

    # Sidebar: Upload and Settings
    st.sidebar.header("Upload and Settings")

    # File uploader component
    uploaded_file = file_uploader_component()

    if uploaded_file is not None:
        # Save the uploaded file to a temporary location
        temp_twbx_path = "temp_uploaded.twbx"
        try:
            with open(temp_twbx_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            logger.info(f"Uploaded file saved to {temp_twbx_path}")
            st.sidebar.success("File uploaded successfully.")
            st.write("✅ **File uploaded and saved successfully.**")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            st.error("❌ Failed to save the uploaded file.")
            return

        # Initialize the parser
        parser = TableauWorkbookParser(twbx_file=temp_twbx_path)
        try:
            parser.decompress_twbx()
            logger.info("Decompressed the .twbx file.")
            st.write("🗜️ **Decompressed the `.twbx` file successfully.**")
        except Exception as e:
            logger.error(f"Failed to decompress `.twbx` file: {e}")
            st.error("❌ Failed to decompress the `.twbx` file.")
            return

        if parser.twb_content:
            try:
                parser.parse_twb()
                logger.info("Parsed the .twb content.")
                st.write("📄 **Parsed the `.twb` content successfully.**")
                report = parser.get_report()
                logger.info("Report generated from parsed data.")
            except Exception as e:
                logger.error(f"Failed to parse `.twb` content: {e}")
                st.error("❌ Failed to parse the `.twb` content.")
                return
        else:
            logger.error("Failed to extract `.twb` content from the uploaded `.twbx` file.")
            st.error("❌ Failed to extract `.twb` content from the uploaded `.twbx` file.")
            return

        # Sidebar: Report Generation
        st.sidebar.header("Report Generation")
        
        # Define report sections in desired order
        report_sections = ["Version Information", "Calculated Fields", "Original Fields", "Worksheets", "Data Sources", "Dependency DAG"]
        
        # Sidebar checkboxes for report generation
        selected_sections = []
        for section in report_sections:
            if st.sidebar.checkbox(f"Include {section}", value=True):
                selected_sections.append(section)
        
        logger.info(f"Selected report sections: {selected_sections}")
        st.write("### Selected Report Sections")
        st.write(", ".join(selected_sections))
        
        st.markdown("---")  # Divider
        
        # Display selected report sections in the main area
        for section in report_sections:
            if section in selected_sections:
                st.header(section)  # Ensure this is called only once per section
                try:
                    if section == "Version Information":
                        version_info = {
                            "Version": report['metadata'].get('version', 'Unknown'),
                            "Source Platform": report['metadata'].get('source_platform', 'Unknown'),
                            "Source Build": report['metadata'].get('source_build', 'Unknown'),
                        }
                        st.json(version_info)
                    
                    elif section == "Calculated Fields":
                        calculated_fields_df = report['metadata'].get('calculated_fields', pd.DataFrame())
                        if not calculated_fields_df.empty:
                            # st.subheader("Calculated Fields")
                            # Adjust index to start from 1
                            calculated_fields_df = calculated_fields_df.reset_index(drop=True)
                            calculated_fields_df.index = calculated_fields_df.index + 1
                            
                            if len(calculated_fields_df) > 10:
                                st.dataframe(calculated_fields_df.head(10))
                                with st.expander("📂 Show more Calculated Fields"):
                                    st.dataframe(calculated_fields_df)
                            else:
                                st.dataframe(calculated_fields_df)
                        else:
                            st.write("No calculated fields found.")

                    elif section == "Original Fields":
                        original_fields_df = report['metadata'].get('original_fields', pd.DataFrame())
                        if not original_fields_df.empty:
                            # st.subheader("Original Fields")
                            # Adjust index to start from 1
                            original_fields_df = original_fields_df.reset_index(drop=True)
                            original_fields_df.index = original_fields_df.index + 1
                            
                            if len(original_fields_df) > 10:
                                st.dataframe(original_fields_df.head(10))
                                with st.expander("📂 Show more Original Fields"):
                                    st.dataframe(original_fields_df)
                            else:
                                st.dataframe(original_fields_df)
                        else:
                            st.write("No original fields found.")

                    elif section == "Worksheets":
                        worksheets_df = report['metadata'].get('worksheets', pd.DataFrame())
                        if not worksheets_df.empty:
                            # st.subheader("Worksheets")
                            # Adjust index to start from 1
                            worksheets_df = worksheets_df.reset_index(drop=True)
                            worksheets_df.index = worksheets_df.index + 1
                            
                            if len(worksheets_df) > 10:
                                st.dataframe(worksheets_df.head(10))
                                with st.expander("📂 Show more Worksheets"):
                                    st.dataframe(worksheets_df)
                            else:
                                st.dataframe(worksheets_df)
                        else:
                            st.write("No worksheets found.")

                    elif section == "Data Sources":
                        df_data_sources = report['data'].get('data_sources', pd.DataFrame())
                        if not df_data_sources.empty:
                            # st.subheader("Data Sources")
                            # Adjust index to start from 1
                            df_data_sources = df_data_sources.reset_index(drop=True)
                            df_data_sources.index = df_data_sources.index + 1
                            
                            if len(df_data_sources) > 10:
                                st.dataframe(df_data_sources.head(10))
                                with st.expander("📂 Show more Data Sources"):
                                    st.dataframe(df_data_sources)
                            else:
                                st.dataframe(df_data_sources)
                        else:
                            st.write("No data sources found.")

                    elif section == "Dependency DAG":
                        calculated_fields_df = report['metadata'].get('calculated_fields', pd.DataFrame())
                        original_fields_df = report['metadata'].get('original_fields', pd.DataFrame())
                        data_sources_df = report['data'].get('data_sources', pd.DataFrame())

                        if not calculated_fields_df.empty and not original_fields_df.empty:
                            # st.subheader("Dependency DAG")

                            # Dropdown to select worksheet
                            worksheets = report['metadata'].get('worksheets', pd.DataFrame()).get('Worksheet Name', [])
                            worksheets = worksheets.dropna().unique().tolist()
                            selected_worksheet = st.selectbox("Select Worksheet for DAG:", ["All"] + list(worksheets))

                            # Generate DAG based on selection
                            if selected_worksheet == "All":
                                G = generate_dag(calculated_fields_df, original_fields_df, data_sources_df)
                            else:
                                # Filter based on selected worksheet if applicable
                                if 'Worksheet Name' in calculated_fields_df.columns:
                                    filtered_calc_fields = calculated_fields_df[calculated_fields_df['Worksheet Name'] == selected_worksheet]
                                else:
                                    filtered_calc_fields = calculated_fields_df.copy()
                                G = generate_dag(filtered_calc_fields, original_fields_df, data_sources_df)

                            # Generate Graphviz dot format
                            dot = plot_dag_graphviz(G)

                            # Display using Streamlit's Graphviz
                            st.graphviz_chart(dot)
                        else:
                            st.write("Insufficient data to generate Dependency DAG.")
                except Exception as e:
                    logger.error(f"Error displaying section '{section}': {e}")
                    st.error(f"❌ An error occurred while displaying the '{section}' section.")

    st.markdown("---")  # Divider

    # Sidebar: Report Export Options
    st.sidebar.header("Export Report")
    export_format = st.sidebar.selectbox("Select export format:", ["HTML", "PDF"])

    # Create a placeholder for download buttons
    download_placeholder = st.sidebar.empty()

    if st.sidebar.button("Generate and Download Report"):
        logger.info("Generate and Download Report button clicked.")
        # Use the placeholder to manage the loading spinner and download button
        with download_placeholder.container():
            with st.spinner('🔄 Generating report...'):
                try:
                    # Generate HTML report
                    html_report = generate_html_report(selected_sections, report)
                    logger.info("HTML report generated.")

                    # Handle Dependency DAG section
                    if "Dependency DAG" in selected_sections and not report['metadata'].get('calculated_fields', pd.DataFrame()).empty:
                        G = generate_dag(report['metadata']['calculated_fields'], report['metadata']['original_fields'], report['data']['data_sources'])
                        dot = plot_dag_graphviz(G)
                        img_bytes = dot.pipe(format='png')
                        img_base64 = image_to_base64(img_bytes)
                        # Embed the image in HTML
                        html_report = html_report.replace(
                            "<p>See the Dependency DAG visualization within the app.</p>",
                            f"<h3>Dependency DAG</h3><img src='data:image/png;base64,{img_base64}'/>"
                        )
                        logger.info("Dependency DAG embedded in HTML report.")

                    # Generate download links
                    if export_format == "HTML":
                        # Provide download link for HTML
                        st.markdown("### 📥 Download Report")
                        st.download_button(
                            label="📄 Download HTML Report",
                            data=html_report,
                            file_name=f"tableau_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                        logger.info("HTML report ready for download.")
                    elif export_format == "PDF":
                        # Convert HTML to PDF using xhtml2pdf or any other library
                        try:
                            pdf = convert_html_to_pdf(html_report)
                            if pdf:
                                st.markdown("### 📥 Download Report")
                                st.download_button(
                                    label="📄 Download PDF Report",
                                    data=pdf,
                                    file_name=f"tableau_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf"
                                )
                                logger.info("PDF report ready for download.")
                            else:
                                st.error("❌ Failed to generate PDF report.")
                                logger.error("Failed to generate PDF report: convert_html_to_pdf returned None.")
                        except Exception as e:
                            logger.error(f"Failed to generate PDF: {e}")
                            st.error(f"❌ Failed to generate PDF: {e}")
                except Exception as e:
                    logger.error(f"Failed during report generation: {e}")
                    st.error(f"❌ An error occurred during report generation: {e}")

    # Sidebar: Download Original File
    st.sidebar.header("Download Original File")
    if st.sidebar.button("⬇️ Download Uploaded `.twbx`"):
        try:
            with open(temp_twbx_path, "rb") as f:
                st.sidebar.download_button(
                    label="⬇️ Download `.twbx` File",
                    data=f,
                    file_name=os.path.basename(temp_twbx_path),
                    mime="application/octet-stream"
                )
            logger.info("Original .twbx file ready for download.")
        except Exception as e:
            logger.error(f"Failed to download .twbx file: {e}")
            st.sidebar.error("❌ Failed to download the original `.twbx` file.")

if __name__ == "__main__":
    main()
