
@file_bp.route('/upload_documents', methods=['POST'])
@login_required
@admin_required
def upload_excel():
    try:
        logg_obj.Info_Log("-----------upload_documents----------------")
        # Get campaign details from form data
        campaign_name = request.form.get('campaign_name')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        # Validate required fields
        if not all([campaign_name, from_date, to_date]):
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': 'Missing required fields: campaign_name, from_date, to_date'}), 400

        # Check if campaign name already exists
        if db.documents.find_one({'campaign_name': campaign_name}):
            logg_obj.Info_Log("Campaign name already exists")
            return jsonify({'error': 'Campaign name already exists'}), 400

        # Check if file is present
        if 'file' not in request.files:
            logg_obj.Info_Log("No file part")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            logg_obj.Info_Log("No selected file")
            return jsonify({'error': 'No selected file'}), 400

        # Validate file type
        if not allowed_file(file.filename):
            logg_obj.Info_Log("Invalid file type")
            return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Get user ID from token
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        # Create unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        # Save file to temporary location
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, unique_filename)
        file.save(file_path)

        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Store file in GridFS
        metadata = {
            'user_id': user_id,
            'campaign_name': campaign_name,
            'from_date': from_date,
            'to_date': to_date,
            'upload_date': current_timestamp(),
            'file_type': Path(filename).suffix.lower()
        }

        file_id = db.store_file(file_content, unique_filename, metadata)

        # Create document record with reference to GridFS file
        document = {
            'user_id': user_id,
            'campaign_name': campaign_name,
            'from_date': from_date,
            'to_date': to_date,
            'filename': filename,
            'file_id': file_id,  # Store GridFS file ID
            'upload_date': current_timestamp(),
            'file_type': Path(filename).suffix.lower()
        }

        # Save to MongoDB
        result = db.documents.insert_one(document)

        # Clean up temporary file
        os.remove(file_path)

        logg_obj.Info_Log("Document uploaded successfully")
        return jsonify({
            'message': 'Document uploaded successfully',
            'document_id': str(result.inserted_id)
        })

    except Exception as e:
        logg_obj.Error_Log(str(e))
        return jsonify({'error': 'Failed to upload document', 'details': str(e)}), 500

@file_bp.route('/document_list', methods=['GET'])
# @login_required
def get_documents():
    docs = list(db.documents.find({}, {'_id': 0}))
    return jsonify(docs)

@file_bp.route('/view_document/<file_id>', methods=['GET'])
def view_document(file_id: str):
    data, meta = db.get_file(file_id)
    filename = f"{meta['campaign_name']}.{meta['file_type']}"
    import mimetypes
    mime, _ = mimetypes.guess_type(filename)
    return data, 200, {
        'Content-Type': mime or 'application/octet-stream',
        'Content-Disposition': f'inline; filename="{filename}"'
    }

@file_bp.route('/delete_document/<file_id>', methods=['DELETE'])
@login_required
def delete_document(file_id: str):
    try:
        doc = db.documents.find_one({"file_id": file_id})
        if not doc:
            return jsonify({"error": "Document not found"}), 404

        # Delete from GridFS (MongoDB)
        if not db.delete_file(file_id):
            return jsonify({"error": "File not found in GridFS"}), 404

        # Delete metadata from the database
        result = db.documents.delete_one({"file_id": file_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Document not found in DB"}), 404
        return jsonify({"message": "Document deleted successfully"}), 200

    except Exception as e:
        print(str(e))
        return {}