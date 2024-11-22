# app.py

import streamlit as st
import os
from parser.tableau_parser import TableauWorkbookParser
from utils.dag import generate_dag, plot_dag
from utils.report import generate_html_report, convert_html_to_pdf
from utils.helpers import image_to_base64
from components.uploader import file_uploader_component
import pandas as pd
import plotly.graph_objects as go
import logzero
from logzero import logger, logfile
from datetime import datetime
from io import BytesIO

def main():
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logzero
    logzero.logfile("logs/app.log", maxBytes=1e6, backupCount=3)
    logger.info("Streamlit app started.")
    
    st.title("📊 Tableau Workbook Parser and Report Generator")
    st.write("""
    Upload a Tableau Workbook (`.twbx` file) to parse its contents and generate comprehensive reports, 
    including calculated fields, worksheets, dashboards, and data sources. Additionally, visualize 
    dependencies between calculated fields and original columns using a Directed Acyclic Graph (DAG).
    """)

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
            st.write("File uploaded and saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            st.error("Failed to save the uploaded file.")
            return

        # Initialize the parser
        parser = TableauWorkbookParser(twbx_file=temp_twbx_path)
        parser.decompress_twbx()
        logger.info("Decompressed the .twbx file.")
        st.write("Decompressed the `.twbx` file successfully.")

        if parser.twb_content:
            parser.parse_twb()
            logger.info("Parsed the .twb content.")
            st.write("Parsed the `.twb` content successfully.")
            report = parser.get_report()
            logger.info("Report generated from parsed data.")
        else:
            logger.error("Failed to extract `.twb` content from the uploaded `.twbx` file.")
            st.error("Failed to extract `.twb` content from the uploaded `.twbx` file.")
            return

        # Sidebar options for report generation
        st.sidebar.header("Report Generation")
        
        report_sections = ["Version Information", "Calculated Fields", "Worksheets", "Dependency DAG"]
        # report_sections = ["Version Information", "Calculated Fields", "Worksheets", "Dashboards", "Data Sources", "Dependency DAG"]
        
        selected_sections = st.sidebar.multiselect("Select report sections to generate:", report_sections, default=report_sections)
        logger.info(f"Selected report sections: {selected_sections}")
        st.write("Selected report sections: " + ", ".join(selected_sections))

        # Display selected report sections
        for section in selected_sections:
            st.header(section)
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
                    st.dataframe(calculated_fields_df)
                else:
                    st.write("No calculated fields found.")
            elif section == "Worksheets":
                worksheets_df = report['metadata'].get('worksheets', pd.DataFrame())
                if not worksheets_df.empty:
                    st.dataframe(worksheets_df)
                else:
                    st.write("No worksheets found.")
            # elif section == "Dashboards":
            #     dashboards_df = report['metadata'].get('dashboards', pd.DataFrame())
            #     if not dashboards_df.empty:
            #         st.dataframe(dashboards_df)
            #     else:
            #         st.write("No dashboards found.")
            # elif section == "Data Sources":
            #     data_sources_dict = report['data'].get('data_sources', {})
            #     if data_sources_dict:
            #         for ds_name, ds_data in data_sources_dict.items():
            #             st.subheader(ds_name)
            #             if isinstance(ds_data, pd.DataFrame):
            #                 st.dataframe(ds_data)
            #             else:
            #                 st.write(ds_data)
            #     else:
            #         st.write("No data sources found.")
            elif section == "Dependency DAG":
                calculated_fields_df = report['metadata'].get('calculated_fields', pd.DataFrame())
                if not calculated_fields_df.empty:
                    G = generate_dag(calculated_fields_df)
                    fig = plot_dag(G)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("No calculated fields available to generate DAG.")

        # Report Export Options
        st.sidebar.header("Export Report")
        export_format = st.sidebar.selectbox("Select export format:", ["HTML", "PDF"])
        if st.sidebar.button("Generate and Download Report"):
            logger.info("Generate and Download Report button clicked.")
            st.write("Generating report...")
            # Generate HTML report
            html_report = generate_html_report(selected_sections, report)
            logger.info("HTML report generated.")

            # Handle Dependency DAG section
            if "Dependency DAG" in selected_sections and not report['metadata'].get('calculated_fields', pd.DataFrame()).empty:
                G = generate_dag(report['metadata']['calculated_fields'])
                fig = plot_dag(G)
                img_bytes = fig.to_image(format="png")
                img_base64 = image_to_base64(img_bytes)
                # Embed the image in HTML
                html_report = html_report.replace(
                    "<p>See the Dependency DAG visualization within the app.</p>",
                    f"<h3>Dependency DAG</h3><img src='data:image/png;base64,{img_base64}'/>"
                )
                logger.info("Dependency DAG embedded in HTML report.")

            if export_format == "HTML":
                # Provide download link for HTML
                st.markdown("### Download Report")
                st.download_button(
                    label="Download HTML Report",
                    data=html_report,
                    file_name=f"tableau_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )
                logger.info("HTML report ready for download.")
                st.write("HTML report is ready for download.")
            elif export_format == "PDF":
                # Convert HTML to PDF using xhtml2pdf
                try:
                    pdf = convert_html_to_pdf(html_report)
                    if pdf:
                        st.markdown("### Download Report")
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf,
                            file_name=f"tableau_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                        logger.info("PDF report ready for download.")
                        st.write("PDF report is ready for download.")
                    else:
                        st.error("Failed to generate PDF report.")
                        logger.error("Failed to generate PDF report: convert_html_to_pdf returned None.")
                except Exception as e:
                    logger.error(f"Failed to generate PDF: {e}")
                    st.error(f"Failed to generate PDF: {e}")

        # Optionally, add a button to download the original .twbx file
        st.sidebar.header("Download Original File")
        if st.sidebar.button("Download Uploaded `.twbx`"):
            try:
                with open(temp_twbx_path, "rb") as f:
                    st.sidebar.download_button(
                        label="Download `.twbx` File",
                        data=f,
                        file_name=os.path.basename(temp_twbx_path),
                        mime="application/octet-stream"
                    )
                logger.info("Original .twbx file ready for download.")
            except Exception as e:
                logger.error(f"Failed to download .twbx file: {e}")
                st.sidebar.error("Failed to download the original `.twbx` file.")

if __name__ == "__main__":
    main()
