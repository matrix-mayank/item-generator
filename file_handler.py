"""
File handler for manual uploads in Reading Comprehension Item Generator.
Handles PDF, TXT, and DOCX file uploads.
"""

import os
import re

# Try to import werkzeug, use fallback if not available
try:
    from werkzeug.utils import secure_filename
except ImportError:
    def secure_filename(filename):
        """Fallback implementation of secure_filename"""
        # Remove path components
        filename = os.path.basename(filename)
        # Replace unsafe characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    """
    Extract text content from uploaded file.
    Supports TXT, PDF, and DOCX files.
    
    Args:
        filepath: Path to the uploaded file
    
    Returns:
        Extracted text content as string
    """
    filename = filepath.lower()
    
    # TXT files
    if filename.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    # PDF files
    elif filename.endswith('.pdf'):
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "Error: PyPDF2 not installed. Please install it to read PDF files."
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    # DOCX files
    elif filename.endswith('.docx'):
        try:
            import docx
            doc = docx.Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            return "Error: python-docx not installed. Please install it to read DOCX files."
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    else:
        return "Error: Unsupported file format"

def save_uploaded_file(file, upload_folder):
    """
    Save uploaded file to server.
    
    Args:
        file: Flask file object
        upload_folder: Directory to save files
    
    Returns:
        tuple: (success: bool, filepath or error message: str)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Create upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    # Secure the filename
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    
    # Check file size (if possible)
    try:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    except:
        pass  # If we can't check size, proceed anyway
    
    # Save file
    try:
        file.save(filepath)
        return True, filepath
    except Exception as e:
        return False, f"Error saving file: {str(e)}"

def process_manual_upload(file, upload_folder):
    """
    Process manual upload: save file and extract text.
    
    Args:
        file: Flask file object
        upload_folder: Directory to save files
    
    Returns:
        tuple: (success: bool, text content or error message: str)
    """
    # Save file
    success, result = save_uploaded_file(file, upload_folder)
    
    if not success:
        return False, result
    
    filepath = result
    
    # Extract text
    try:
        text = extract_text_from_file(filepath)
        
        if not text or len(text.strip()) == 0:
            return False, "File is empty or could not extract text"
        
        return True, text
    except Exception as e:
        return False, f"Error processing file: {str(e)}"
