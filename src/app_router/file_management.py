import os
import pandas as pd
from flask import Blueprint, request, jsonify

from src.logger.log import Log_class
from src.user_utils.auth import login_required, admin_required
from src.user_utils.utils import extract_text_from_txt, extract_text_from_pdf, extract_text_from_docx, to_snake_case

file_bp = Blueprint('file_bp', __name__)
logg_obj = Log_class("logs", "file_bp.txt")

#-------------------------------------------------------#
#----------------Upload-Knowledge-Base------------------#
#-------------------------------------------------------#
@file_bp.route('/upload_knowledge_base', methods=['POST'])
@login_required
@admin_required
def upload_knowledge_base_api():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        text = ""
        filename = file.filename
        ext = filename.rsplit('.', 1)[-1].lower()

        try:
            if ext == 'txt':
                text = extract_text_from_txt(file.stream)
            elif ext == 'pdf':
                text = extract_text_from_pdf(file.stream)
            elif ext == 'docx':
                text = extract_text_from_docx(file.stream)
            else:
                return jsonify({"error": "Unsupported file format"}), 400
            text = text.replace("\n"," ").replace("  "," ")
        except Exception as e:
            return jsonify({"error": f"Failed to extract text: {str(e)}"}), 500

        return jsonify({
            "filename": filename,
            "extracted_text": text.strip()
        })
    except Exception as e:
        return jsonify({"error": f"Failed extract-text: {str(e)}"}), 500

#-----------------------upload_contact_data-------------------------#
@file_bp.route('/upload_contact_data', methods=['POST'])
@login_required
@admin_required
def upload_contact_data_api():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        filename = file.filename

        if filename == '':
            return jsonify({"error": "No file selected"}), 400

        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ['xlsx', 'xls', 'csv']:
            return jsonify({"error": "Unsupported file format"}), 400

        try:
            # Choose how to read the file based on extension
            if ext in ['xlsx', 'xls']:
                df = pd.read_excel(file, engine='openpyxl' if ext == 'xlsx' else 'xlrd')
            elif ext == 'csv':
                df = pd.read_csv(file)

            # Convert to list of row-wise JSONs
            # Rename columns
            df.columns = [to_snake_case(col) for col in df.columns]
            data_json = df.to_dict(orient='records')
            return jsonify(data_json)

        except Exception as e:
            return jsonify({"error": f"Failed to read file: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"upload_contact_data: {str(e)}"}), 500




