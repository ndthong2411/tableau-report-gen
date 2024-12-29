# Tableau Report Gen  

A Streamlit application to parse Tableau Workbook (`.twbx`) files and generate comprehensive reports, including version information, calculated fields, original fields, worksheets, data sources, and a Dependency DAG visualization.  

## Features  

- **Upload Tableau Workbook:** Easily upload your `.twbx` files.  
- **Comprehensive Reports:** Generate detailed reports covering various aspects of your workbook.  
- **Dependency DAG:** Visualize dependencies between calculated fields and original columns.  
- **Export Options:** Download reports in HTML or PDF formats.  

## Installation  

### System Dependencies  

This package requires [Graphviz](https://graphviz.org/) to be installed on your system.  

- **Windows:**  
  - Download the installer from the [Graphviz Download Page](https://graphviz.org/download/) and follow the installation instructions.  
  - Ensure that the `bin` directory (e.g., `C:\Program Files\Graphviz\bin`) is added to your system's `PATH`.  

- **macOS:**  
  Install Graphviz via Homebrew:  
  ```bash  
  brew install graphviz  
  ```  

- **Linux:**  
  Install Graphviz via APT:  
  ```bash  
  sudo apt-get install graphviz  
  ```  

### Python Package  

Install the package using `pip`:  
```bash  
pip install tableau-reprot-gen  
```  

## Usage  

After installation, you can run the Streamlit app via the command line:  
```bash  
trggo
```  

This will launch the app in your default web browser. Follow the on-screen instructions to upload your `.twbx` file and generate reports.  

## License  

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  

