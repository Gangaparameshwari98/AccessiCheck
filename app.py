import requests
from bs4 import BeautifulSoup
import re
import os
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse
import base64
from PIL import Image, ImageDraw
from io import BytesIO
import webcolors
import matplotlib.colors as mcolors

app = Flask(__name__)

class AccessibilityScanner:
    def __init__(self, url):
        self.url = url
        self.issues = []
        self.score = 100
        self.soup = None
        self.screenshot = None
        self.highlighted_screenshot = None
    
    def scan(self):
        try:
            # Fetch the webpage
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            self.soup = BeautifulSoup(response.text, 'html.parser')
            
            # Run accessibility checks
            self._check_alt_text()
            self._check_color_contrast()
            self._check_form_labels()
            self._check_heading_structure()
            self._check_link_text()
            
            # Calculate score (each issue reduces score by 5 points)
            self.score = max(0, 100 - (len(self.issues) * 5))
            
            return {
                'url': self.url,
                'issues': self.issues,
                'score': self.score
            }
        except Exception as e:
            return {
                'url': self.url,
                'error': str(e),
                'issues': [],
                'score': 0
            }
    
    def _check_alt_text(self):
        images = self.soup.find_all('img')
        for img in images:
            if not img.get('alt'):
                self.issues.append({
                    'type': 'missing_alt_text',
                    'element': str(img)[:100] + '...' if len(str(img)) > 100 else str(img),
                    'description': 'Image missing alt text',
                    'fix': 'Add alt="[descriptive text]" to the image tag'
                })
    
    def _check_color_contrast(self):
        # This is a simplified check - a real implementation would need to extract actual colors
        # from CSS and compute contrast ratios
        elements = self.soup.find_all(['p', 'span', 'div', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for element in elements:
            style = element.get('style', '')
            if 'color' in style and 'background' in style:
                # This is a simplified check - in reality you'd need to compute contrast ratios
                self.issues.append({
                    'type': 'color_contrast',
                    'element': str(element)[:100] + '...' if len(str(element)) > 100 else str(element),
                    'description': 'Potential color contrast issue',
                    'fix': 'Ensure text color contrasts well with background (ratio of at least 4.5:1)'
                })
    
    def _check_form_labels(self):
        inputs = self.soup.find_all(['input', 'select', 'textarea'])
        for input_element in inputs:
            input_id = input_element.get('id')
            if input_id:
                label = self.soup.find('label', attrs={'for': input_id})
                if not label:
                    self.issues.append({
                        'type': 'missing_label',
                        'element': str(input_element)[:100] + '...' if len(str(input_element)) > 100 else str(input_element),
                        'description': f'Form input missing associated label',
                        'fix': f'Add <label for="{input_id}">Description</label> for this input'
                    })
            elif input_element.get('type') not in ['submit', 'button', 'hidden']:
                self.issues.append({
                    'type': 'missing_label',
                    'element': str(input_element)[:100] + '...' if len(str(input_element)) > 100 else str(input_element),
                    'description': 'Form input missing label and id',
                    'fix': 'Add id to input and <label for="id"> or wrap input with <label>'
                })
    
    def _check_heading_structure(self):
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            self.issues.append({
                'type': 'no_headings',
                'element': 'page',
                'description': 'Page has no heading structure',
                'fix': 'Add proper heading structure starting with H1'
            })
        else:
            # Check if H1 exists
            if not self.soup.find('h1'):
                self.issues.append({
                    'type': 'missing_h1',
                    'element': 'page',
                    'description': 'Page missing H1 heading',
                    'fix': 'Add an H1 heading as the main title of the page'
                })
            
            # Check for proper heading hierarchy
            heading_levels = [int(h.name[1]) for h in headings]
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i-1] + 1:
                    self.issues.append({
                        'type': 'heading_skip',
                        'element': str(headings[i])[:100] + '...' if len(str(headings[i])) > 100 else str(headings[i]),
                        'description': f'Heading level skipped from H{heading_levels[i-1]} to H{heading_levels[i]}',
                        'fix': 'Maintain proper heading hierarchy without skipping levels'
                    })
    
    def _check_link_text(self):
        links = self.soup.find_all('a')
        for link in links:
            link_text = link.get_text().strip()
            if not link_text:
                self.issues.append({
                    'type': 'empty_link',
                    'element': str(link)[:100] + '...' if len(str(link)) > 100 else str(link),
                    'description': 'Link has no text',
                    'fix': 'Add descriptive text to the link'
                })
            elif link_text.lower() in ['click here', 'here', 'link', 'more', 'read more']:
                self.issues.append({
                    'type': 'non_descriptive_link',
                    'element': str(link)[:100] + '...' if len(str(link)) > 100 else str(link),
                    'description': f'Non-descriptive link text: "{link_text}"',
                    'fix': 'Replace with text that describes where the link goes'
                })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'})
    
    # Add http:// if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    scanner = AccessibilityScanner(url)
    results = scanner.scan()
    
    return jsonify(results)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Suppress Flask development server warning
    import os
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    
    app.run(debug=True, host='127.0.0.1', port=5000)