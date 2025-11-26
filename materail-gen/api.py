#!/usr/bin/env python3
"""
Flask API for processing Excel files and returning resume data
"""

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
import os
import tempfile
import json
import time
import logging
import traceback
from werkzeug.utils import secure_filename
from get_all_resumen import get_all_resumen, get_all_resumen_text_only, get_all_resumen_with_details
from gpt_matcher import GPTConstructionMatcher, ConstructionItem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Configuration
DATABASE_PATH = '/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATA_BASE.xlsx'  # Default database file
MATERIALS_LIST_PATH = os.getenv('MATERIALS_LIST_PATH', 'materials_list.txt')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Required: Set in environment
UPLOAD_FOLDER = tempfile.gettempdir()

# Validate required environment variables
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is required")
    raise ValueError("OPENAI_API_KEY environment variable is required")

logger.info(f"API initialized. Materials list path: {MATERIALS_LIST_PATH}")


# Configure upload settings
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
ALLOWED_TEXT_EXTENSIONS = {'txt'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_text_file(filename):
    """Check if the file is a text file"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TEXT_EXTENSIONS




@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload an Excel file and get all resume data as text
    
    Returns:
        JSON response with resume data formatted as text
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload .xlsx or .xls file'}), 400
    
    try:
        # Save file to temporary location
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            temp_path = tmp_file.name
            file.save(temp_path)
        
        # Process the file
        resumenes = get_all_resumen(temp_path)
        
        # Format as text
        text_output = []
        text_output.append(f"Total materials: {len(resumenes)}")
        text_output.append("=" * 80)
        text_output.append("")
        
        for i, item in enumerate(resumenes, 1):
            text_output.append(f"{i}. Codigo: {item['codigo']}")
            text_output.append(f"   Resumen: {item['resumen']}")
            text_output.append("")
        
        result_text = "\n".join(text_output)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return jsonify({
            'success': True,
            'count': len(resumenes),
            'text': result_text,
            'data': resumenes
        }), 200
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return jsonify({
            'error': f'Error processing file: {str(e)}'
        }), 500


@app.route('/api/upload/text-only', methods=['POST'])
def upload_file_text_only():
    """
    Upload an Excel file and get only resume text (no codes)
    
    Returns:
        JSON response with resume text only
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload .xlsx or .xls file'}), 400
    
    try:
        # Save file to temporary location
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            temp_path = tmp_file.name
            file.save(temp_path)
        
        # Process the file
        resumen_texts = get_all_resumen_text_only(temp_path)
        
        # Format as text
        text_output = []
        text_output.append(f"Total materials: {len(resumen_texts)}")
        text_output.append("=" * 80)
        text_output.append("")
        
        for i, resumen in enumerate(resumen_texts, 1):
            text_output.append(f"{i}. {resumen}")
            text_output.append("")
        
        result_text = "\n".join(text_output)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return jsonify({
            'success': True,
            'count': len(resumen_texts),
            'text': result_text,
            'data': resumen_texts
        }), 200
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return jsonify({
            'error': f'Error processing file: {str(e)}'
        }), 500


@app.route('/api/upload/details', methods=['POST'])
def upload_file_with_details():
    """
    Upload an Excel file and get all resume data with full details
    
    Returns:
        JSON response with complete material details
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload .xlsx or .xls file'}), 400
    
    try:
        # Save file to temporary location
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            temp_path = tmp_file.name
            file.save(temp_path)
        
        # Process the file
        resumen_details = get_all_resumen_with_details(temp_path)
        
        # Format as text
        text_output = []
        text_output.append(f"Total materials: {len(resumen_details)}")
        text_output.append("=" * 80)
        text_output.append("")
        
        for i, item in enumerate(resumen_details, 1):
            text_output.append(f"{i}. Codigo: {item['codigo']}")
            text_output.append(f"   Tipo: {item['tipo']}")
            text_output.append(f"   Unidad: {item['ud']}")
            text_output.append(f"   Resumen: {item['resumen']}")
            text_output.append(f"   Precio: {item['precio']}€")
            text_output.append(f"   Sub-materials: {item['num_sub_materials']}")
            text_output.append("")
        
        result_text = "\n".join(text_output)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return jsonify({
            'success': True,
            'count': len(resumen_details),
            'text': result_text,
            'data': resumen_details
        }), 200
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return jsonify({
            'error': f'Error processing file: {str(e)}'
        }), 500


@app.route('/api/search-with-file', methods=['POST', 'OPTIONS'])
def search_with_file():
    """
    Search for materials using the default database and description.
    
    Accepts form-data with:
        - description: Text description to search for
        - top_k: Number of results to return (default: 5)
    
    Returns:
        Server-Sent Events stream with progress and final results
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        # Get description
        description = request.form.get('description', '').strip()
        if not description:
            logger.warning("Search request missing description")
            return jsonify({'error': 'Description cannot be empty'}), 400
        
        top_k = int(request.form.get('top_k', 5))
        
        logger.info(f"Search request: description='{description[:50]}...', top_k={top_k}")
        
        def generate():
            """Generator function to stream progress"""
            try:
                # Step 1: Initialize
                logger.info("Step 1: Loading materials from database")
                yield f"data: {json.dumps({'type': 'log', 'message': '🔧 Loading materials from database...', 'step': 1, 'total': 3})}\n\n"
                
                # Load from database
                try:
                    resumenes = get_all_resumen(DATABASE_PATH)
                except Exception as e:
                    error_msg = f"Error loading database: {str(e)}"
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                    return
                
                # Create matcher and populate items
                matcher = GPTConstructionMatcher(api_key=OPENAI_API_KEY, model="gpt-4o")
                
                valid_items = []
                # Use a counter for item numbering
                count = 1
                for item in resumenes:
                    desc = item.get('resumen', '')
                    # Filter out items starting with XXXX
                    if desc and isinstance(desc, str) and not desc.strip().startswith('XXXX'):
                        valid_items.append(ConstructionItem(
                            number=count,
                            code=item['codigo'],
                            description=desc
                        ))
                        count += 1
                
                matcher.items = valid_items
                logger.info(f"Loaded materials list: {len(matcher.items)} items (filtered from {len(resumenes)})")
                
                yield f"data: {json.dumps({'type': 'log', 'message': f'✅ Loaded {len(matcher.items)} materials', 'step': 2, 'total': 3})}\n\n"
                
                # Step 2: Call GPT
                logger.info(f"Step 2: Querying GPT with description: {description[:100]}")
                yield f"data: {json.dumps({'type': 'log', 'message': '🤖 Querying GPT-4o...', 'step': 3, 'total': 3})}\n\n"
                
                result = matcher.find_best_match(description, top_k=top_k)
                
                if 'error' in result:
                    error_msg = f"Error: {result['error']}"
                    logger.error(f"GPT matcher error: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                    return
                
                logger.info(f"GPT matcher returned {len(result.get('matches', []))} matches")
                
                # Format as text
                text_output = []
                text_output.append(f"Search query: {description}")
                text_output.append(f"Found {len(result['matches'])} matching materials")
                text_output.append("=" * 80)
                text_output.append("")
                
                # Prepare results data
                results_data = []
                for i, match in enumerate(result['matches'], 1):
                    text_output.append(f"{i}. Codigo: {match['code']}")
                    text_output.append(f"   Description: {match['description']}")
                    text_output.append(f"   Confidence Score: {match['confidence_score']}/100")
                    text_output.append(f"   Reasoning: {match['reasoning']}")
                    text_output.append("")
                    
                    results_data.append({
                        'number': match['number'],
                        'codigo': match['code'],
                        'resumen': match['description'],
                        'confidence_score': match['confidence_score'] / 100,  # Convert to 0-1 scale
                        'reasoning': match['reasoning']
                    })
                
                result_text = "\n".join(text_output)
                
                # Send final results
                final_data = {
                    'type': 'complete',
                    'success': True,
                    'query': description,
                    'count': len(results_data),
                    'text': result_text,
                    'data': results_data,
                    'model_used': result.get('model_used', 'gpt-4o'),
                    'total_tokens': result.get('total_tokens', 0)
                }
                
                logger.info(f"Search completed successfully: {len(results_data)} results, {result.get('total_tokens', 0)} tokens")
                yield f"data: {json.dumps(final_data)}\n\n"
                
            except Exception as e:
                error_message = f"Error: {str(e)}"
                error_trace = traceback.format_exc()
                logger.error(f"Search with file error: {error_message}\n{error_trace}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
        
        # Create response with proper SSE headers
        response = Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        return response
            
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Search endpoint error: {str(e)}\n{error_trace}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'}), 200


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


@app.route('/')
def serve_frontend():
    """Serve the frontend HTML"""
    return send_from_directory('static', 'index.html')


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation endpoint"""
    return jsonify({
        'message': 'Resume Data API',
        'endpoints': {
            '/api/health': {
                'method': 'GET',
                'description': 'Health check endpoint'
            },
            '/api/upload': {
                'method': 'POST',
                'description': 'Upload Excel file and get resume data with codes',
                'parameters': {
                    'file': 'Excel file (.xlsx or .xls)'
                },
                'returns': 'JSON with text output and data array'
            },
            '/api/upload/text-only': {
                'method': 'POST',
                'description': 'Upload Excel file and get resume text only (no codes)',
                'parameters': {
                    'file': 'Excel file (.xlsx or .xls)'
                },
                'returns': 'JSON with text output and data array'
            },
            '/api/upload/details': {
                'method': 'POST',
                'description': 'Upload Excel file and get full material details',
                'parameters': {
                    'file': 'Excel file (.xlsx or .xls)'
                },
                'returns': 'JSON with text output and detailed data array'
            },
            '/api/search-with-file': {
                'method': 'POST',
                'description': 'Search for materials using the default database and description',
                'parameters': {
                    'description': 'Text description to search for',
                    'top_k': 'Number of results to return (default: 5)'
                },
                'returns': 'Server-Sent Events stream with matching materials'
            }
        },
        'usage': {
            'curl_example': "curl -X POST -F 'file=@/path/to/file.xlsx' http://161.22.47.36:5001/api/upload",
            'search_example': "curl -X POST -F 'description=limpieza de alicatado' -F 'top_k=5' http://161.22.47.36:5001/api/search-with-file"
        }
    }), 200


if __name__ == '__main__':
    # Use debug mode only if FLASK_ENV is not production
    debug_mode = os.getenv('FLASK_ENV', 'development') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=5001)

