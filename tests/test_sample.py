import base64
import pandas as pd
from tableau_report_gen.utils.helpers import image_to_base64
from tableau_report_gen.utils.report import generate_html_report

def test_image_to_base64():
    """
    Test that image_to_base64 correctly encodes a given byte string.
    """
    sample_bytes = b'test'
    encoded = image_to_base64(sample_bytes)
    expected = base64.b64encode(sample_bytes).decode('utf-8')
    assert encoded == expected, "The base64 encoding does not match the expected value."

def test_generate_html_report_empty():
    """
    Test generate_html_report with a minimal report input.
    """
    # Prepare a dummy report with a minimal set of data.
    selected_sections = ["Version Information"]
    report = {
        "metadata": {
            "version": "dummy",
            "source_platform": "dummy",
            "source_build": "dummy",
            "calculated_fields": pd.DataFrame(),
            "original_fields": pd.DataFrame(),
            "worksheets": pd.DataFrame()
        },
        "data": {
            "data_sources": pd.DataFrame()
        }
    }
    
    html = generate_html_report(selected_sections, report)
    # Check if expected strings are present in the HTML output.
    assert "Tableau Workbook Report" in html, "HTML report header is missing."
    assert "Version Information" in html, "The 'Version Information' section is missing."
