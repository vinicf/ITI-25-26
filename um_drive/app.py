from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace

# --- Basic Flask App and API Setup ---
app = Flask(__name__)
# Initialize the API with metadata for the Swagger UI
api = Api(app, 
          version='1.0', 
          title='File Management API', 
          description='A simple API to upload, list, and delete files.',
          doc='/swagger/' # URL for the Swagger UI
)

# --- Namespace for organizing file-related endpoints ---
# Namespaces help group related resources together in the Swagger UI
files_ns = Namespace('files', description='File operations')
api.add_namespace(files_ns)

# --- In-memory "database" ---
# You should use a local storage or even better use the NFS dir
FILES = {}

# --- Define the data model for the API ---
# This model tells Flask-RESTX what the JSON payload for a file should look like.
# It's used to generate documentation and validate incoming data.
file_model = files_ns.model('File', {
    'name': fields.String(required=True, description='The name of the file'),
    'content': fields.String(required=True, description='The content of the file')
})

# --- Resource for handling the collection of files (/files) ---
@files_ns.route('/')
class FileList(Resource):
    """Handles operations on the list of files."""

    @files_ns.doc('list_files')
    @files_ns.response(200, 'Success')
    def get(self):
        """List all available files"""
        print('Available files:\n', FILES)
        return FILES, 200

    @files_ns.doc('upload_file')
    @files_ns.expect(file_model) # Documents the expected input payload
    @files_ns.response(201, 'File successfully uploaded')
    def post(self):
        """Upload a new file"""
        # Flask-RESTX automatically parses and validates the JSON based on the model
        file_data = request.json
        file_name = file_data['name']
        print('Adding', file_name, 'to files.')
        FILES[file_name] = file_data['content']
        return {'message': f'File {file_name} uploaded'}, 201

# --- Resource for handling a single file (/files/<fileName>) ---
@files_ns.route('/<string:fileName>')
@files_ns.response(404, 'File not found')
@files_ns.param('fileName', 'The name of the file') # Documents the URL parameter
class File(Resource):
    """Handles operations on a single file."""

    @files_ns.doc('get_file')
    @files_ns.response(200, 'Success')
    def get(self, fileName):
        """Fetch a single file's content"""
        if fileName not in FILES:
            return {'message': 'File not found'}, 404
        return {'name': fileName, 'content': FILES[fileName]}, 200


    @files_ns.doc('delete_file')
    @files_ns.response(200, 'File successfully deleted')
    def delete(self, fileName):
        """Delete a file"""
        if fileName not in FILES:
            return {'message': 'File not found'}, 404
        
        del FILES[fileName]
        print(f"File {fileName} deleted.")
        return {'message': f'File {fileName} deleted'}, 200


if __name__ == '__main__':
    # The original app.run() is used here
    app.run(host="0.0.0.0", port=5000, debug=True)
