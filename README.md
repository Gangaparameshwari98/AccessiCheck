# AccessiCheck - Instant Website Accessibility Scanner

A simple Python-based tool that scans websites for common accessibility issues and provides suggestions for fixing them.

## Features

- Scan any website URL for accessibility issues
- Checks for 5 key accessibility problems:
  - Missing alt text on images
  - Poor color contrast
  - Missing form labels
  - No heading structure
  - Links without descriptive text
- Generates an accessibility score
- Provides specific suggestions for fixing each issue

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

1. Run the application:

```
python app.py
```

2. Open your web browser and go to `http://127.0.0.1:5000/`
3. Enter a website URL and click "Scan Website"
4. View the accessibility issues and suggestions for fixing them

## Requirements

- Python 3.6+
- Flask
- Requests
- BeautifulSoup4
- Pillow
- Webcolors
- Matplotlib