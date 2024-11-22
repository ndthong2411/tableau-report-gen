# utils/report.py

import pandas as pd
from xhtml2pdf import pisa
import base64
from datetime import datetime
import logzero
from logzero import logger


def generate_html_report(selected_sections, report, templates_path="reports/templates/report_template.html"):
    html_report = "<html><head><title>Tableau Report</title></head><body>"
    html_report += f"<h1>Tableau Workbook Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>"

    for section in selected_sections:
        html_report += f"<h2>{section}</h2>"
        if section == "Version Information":
            version_info = {
                "Version": report['metadata'].get('version', 'Unknown'),
                "Source Platform": report['metadata'].get('source_platform', 'Unknown'),
                "Source Build": report['metadata'].get('source_build', 'Unknown'),
            }
            html_report += f"<pre>{version_info}</pre>"
        elif section == "Calculated Fields":
            calculated_fields_df = report['metadata'].get('calculated_fields', pd.DataFrame())
            if not calculated_fields_df.empty:
                html_report += calculated_fields_df.to_html(index=False)
            else:
                html_report += "<p>No calculated fields found.</p>"
        elif section == "Worksheets":
            worksheets_df = report['metadata'].get('worksheets', pd.DataFrame())
            if not worksheets_df.empty:
                html_report += worksheets_df.to_html(index=False)
            else:
                html_report += "<p>No worksheets found.</p>"
        elif section == "Dashboards":
            dashboards_df = report['metadata'].get('dashboards', pd.DataFrame())
            if not dashboards_df.empty:
                html_report += dashboards_df.to_html(index=False)
            else:
                html_report += "<p>No dashboards found.</p>"
        elif section == "Data Sources":
            data_sources_dict = report['data'].get('data_sources', {})
            if data_sources_dict:
                for ds_name, ds_data in data_sources_dict.items():
                    html_report += f"<h3>{ds_name}</h3>"
                    if isinstance(ds_data, pd.DataFrame):
                        html_report += ds_data.to_html(index=False)
                    else:
                        html_report += f"<p>{ds_data}</p>"
            else:
                html_report += "<p>No data sources found.</p>"
        elif section == "Dependency DAG":
            # The DAG is handled separately and embedded as an image in the main app
            html_report += "<p>See the Dependency DAG visualization within the app.</p>"

    html_report += "</body></html>"
    return html_report


def convert_html_to_pdf(source_html):
    try:
        # Create a binary buffer to receive PDF data.
        result = BytesIO()
        # Convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            src=source_html,            # the HTML to convert
            dest=result)                # file handle to receive the PDF
        # Check for errors
        if pisa_status.err:
            logger.error(f"Error during PDF generation: {pisa_status.err}")
            return None
        logger.info("Successfully converted HTML to PDF using xhtml2pdf.")
        return result.getvalue()
    except Exception as e:
        logger.error(f"Failed to convert HTML to PDF using xhtml2pdf: {e}")
        return None
