"""
Power BI Testing Tool - Simple Web Application

Clean, minimal web interface for .pbix file testing
"""

import os
import sys
import json
import uuid
import zipfile
import threading
import time
from datetime import datetime
from pathlib import Path
import shutil
import tempfile

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
# Removed unused imports: xml.etree.ElementTree, PIL.Image, hashlib

app = Flask(__name__, template_folder='templates')
app.secret_key = 'powerbi-testing-simple'

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'pbix'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Global job storage
jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class PBIXAnalyzer:
    """Simple PBIX file analyzer"""
    
    def __init__(self, pbix_path):
        self.pbix_path = pbix_path
        
    def analyze(self):
        """Analyze .pbix file structure"""
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Extract PBIX (it's a ZIP file)
            with zipfile.ZipFile(self.pbix_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            results = {
                'file_info': self._get_file_info(),
                'structure': self._analyze_structure(temp_dir),
                'performance': self._analyze_performance(),
                'recommendations': []
            }
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
            
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_file_info(self):
        """Get basic file information"""
        stat = os.stat(self.pbix_path)
        return {
            'name': os.path.basename(self.pbix_path),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def _analyze_structure(self, temp_dir):
        """Analyze report structure"""
        structure = {
            'pages': 0,
            'visuals': 0,
            'page_names': [],
            'visual_types': [],
            'has_layout': False
        }
        
        try:
            # Look for Layout file
            layout_path = os.path.join(temp_dir, 'Report', 'Layout')
            if os.path.exists(layout_path):
                structure['has_layout'] = True
                
                with open(layout_path, 'r', encoding='utf-16-le') as f:
                    layout_content = f.read()
                
                # Parse JSON
                layout_json = json.loads(layout_content)
                
                if 'sections' in layout_json:
                    structure['pages'] = len(layout_json['sections'])
                    
                    for section in layout_json['sections']:
                        page_name = section.get('displayName', 'Unnamed Page')
                        structure['page_names'].append(page_name)
                        
                        if 'visualContainers' in section:
                            page_visuals = len(section['visualContainers'])
                            structure['visuals'] += page_visuals
                            
                            # Extract visual types
                            for visual in section['visualContainers']:
                                config = visual.get('config', '{}')
                                if isinstance(config, str):
                                    config = json.loads(config)
                                    
                                if 'singleVisual' in config:
                                    visual_type = config['singleVisual'].get('visualType', 'unknown')
                                    if visual_type not in structure['visual_types']:
                                        structure['visual_types'].append(visual_type)
        
        except Exception as e:
            structure['error'] = str(e)
        
        return structure
    
    def _analyze_performance(self):
        """Simple performance analysis"""
        file_size = os.path.getsize(self.pbix_path) / (1024 * 1024)  # MB
        
        performance = {
            'file_size_mb': round(file_size, 2),
            'size_score': 100,
            'estimated_load_time': round(file_size * 0.5, 1),  # Rough estimate
            'performance_grade': 'A'
        }
        
        # Score based on file size
        if file_size > 100:
            performance['size_score'] = 40
            performance['performance_grade'] = 'D'
        elif file_size > 50:
            performance['size_score'] = 60
            performance['performance_grade'] = 'C'
        elif file_size > 25:
            performance['size_score'] = 80
            performance['performance_grade'] = 'B'
        
        return performance
    
    def _generate_recommendations(self, results):
        """Generate simple recommendations"""
        recommendations = []
        
        file_size = results['performance']['file_size_mb']
        structure = results['structure']
        
        if file_size > 50:
            recommendations.append("Consider reducing file size by optimizing data or images")
        
        if structure['pages'] > 10:
            recommendations.append("Consider reducing the number of pages for better navigation")
        
        if structure['visuals'] > 50:
            recommendations.append("High number of visuals may impact performance")
        
        if len(structure['visual_types']) > 8:
            recommendations.append("Consider standardizing on fewer visual types")
        
        if not recommendations:
            recommendations.append("Great! No major issues found with your report")
        
        return recommendations

def run_analysis(job_id):
    """Background analysis function"""
    try:
        job = jobs[job_id]
        job['status'] = 'analyzing'
        job['progress'] = 20
        
        # Analyze file
        analyzer = PBIXAnalyzer(job['file_path'])
        results = analyzer.analyze()
        
        job['progress'] = 80
        job['status'] = 'generating_report'
        
        # Store results
        job['results'] = results
        job['progress'] = 100
        job['status'] = 'completed'
        job['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        job['status'] = 'error'
        job['error'] = str(e)
        job['progress'] = 0

@app.route('/')
def index():
    return render_template('simple_index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Generate job ID
        job_id = str(uuid.uuid4())[:8]
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{job_id}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Create job
        jobs[job_id] = {
            'id': job_id,
            'filename': filename,
            'file_path': file_path,
            'status': 'uploaded',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'results': None,
            'error': None
        }
        
        # Start analysis in background
        thread = threading.Thread(target=run_analysis, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('status', job_id=job_id))
    
    flash('Please upload a .pbix file')
    return redirect(url_for('index'))

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in jobs:
        flash('Job not found')
        return redirect(url_for('index'))
    
    return render_template('simple_status.html', job=jobs[job_id])

@app.route('/api/status/<job_id>')
def api_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    return jsonify({
        'status': job['status'],
        'progress': job['progress'],
        'error': job.get('error'),
        'completed': job['status'] == 'completed'
    })

@app.route('/results/<job_id>')
def results(job_id):
    if job_id not in jobs:
        flash('Job not found')
        return redirect(url_for('index'))
    
    job = jobs[job_id]
    if job['status'] != 'completed':
        return redirect(url_for('status', job_id=job_id))
    
    return render_template('simple_results.html', job=job)

@app.route('/api/jobs')
def api_jobs():
    job_list = []
    for job_id, job in jobs.items():
        job_list.append({
            'id': job_id,
            'filename': job['filename'],
            'status': job['status'],
            'created_at': job['created_at']
        })
    
    return jsonify(sorted(job_list, key=lambda x: x['created_at'], reverse=True))

if __name__ == '__main__':
    print("🚀 Power BI Testing Tool - Simple Web Version")
    print("📁 Upload your .pbix files at: http://localhost:5000")
    print("📊 Get instant analysis and recommendations")
    print("-" * 50)
    
    # Production-ready configuration
    import os
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('ENVIRONMENT', 'development') == 'development'
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 