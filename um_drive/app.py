from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace
# Importações necessárias para o Prometheus
from prometheus_client import Counter, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import os

# --- 1. Definição das Métricas do Prometheus ---
# Cria um contador para rastrear o total de requisições HTTP, rotulado pelo endpoint e método.
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total de requisições HTTP por endpoint e método', 
    ['endpoint', 'method']
)

# --- 2. Configuração Básica da App Flask e API ---
app = Flask(__name__)
api = Api(app, 
          version='1.0', 
          title='File Management API', 
          description='A simple API to upload, list, and delete files.',
          doc='/swagger/' # URL para o Swagger UI
)

files_ns = Namespace('files', description='Operações de ficheiros')
api.add_namespace(files_ns)

# --- "Base de Dados" em memória ---
# You should use a local storage or even better use the NFS dir
FILES = {}

# --- Modelo de Dados da API ---
file_model = files_ns.model('File', {
    'name': fields.String(required=True, description='O nome do ficheiro'),
    'content': fields.String(required=True, description='O conteúdo do ficheiro')
})

# --- 3. Resource para a Coleção de Ficheiros (/files) ---
@files_ns.route('/')
class FileList(Resource):
    """Lida com operações na lista de ficheiros."""

    @files_ns.doc('list_files')
    @files_ns.response(200, 'Sucesso')
    def get(self):
        """Lista todos os ficheiros disponíveis"""
        # Rastreia a requisição GET para o endpoint '/files/'
        REQUEST_COUNT.labels(endpoint='/files/', method='GET').inc()
        print('Available files:\n', FILES)
        return FILES, 200

    @files_ns.doc('upload_file')
    @files_ns.expect(file_model) 
    @files_ns.response(201, 'Ficheiro carregado com sucesso')
    def post(self):
        """Carrega um novo ficheiro"""
        # Rastreia a requisição POST para o endpoint '/files/'
        REQUEST_COUNT.labels(endpoint='/files/', method='POST').inc()
        
        # Flask-RESTX automaticamente analisa e valida o JSON baseado no modelo
        file_data = request.json
        file_name = file_data['name']
        print('Adding', file_name, 'to files.')
        FILES[file_name] = file_data['content']
        return {'message': f'Ficheiro {file_name} carregado'}, 201

# --- 4. Resource para um Único Ficheiro (/files/<fileName>) ---
@files_ns.route('/<string:fileName>')
@files_ns.response(404, 'Ficheiro não encontrado')
@files_ns.param('fileName', 'O nome do ficheiro')
class File(Resource):
    """Lida com operações num único ficheiro."""

    @files_ns.doc('get_file')
    @files_ns.response(200, 'Sucesso')
    def get(self, fileName):
        """Busca o conteúdo de um único ficheiro"""
        # Rastreia a requisição GET para o endpoint '/files/<fileName>'
        REQUEST_COUNT.labels(endpoint='/files/<fileName>', method='GET').inc()
        
        if fileName not in FILES:
            return {'message': 'Ficheiro não encontrado'}, 404
        return {'name': fileName, 'content': FILES[fileName]}, 200


    @files_ns.doc('delete_file')
    @files_ns.response(200, 'Ficheiro apagado com sucesso')
    def delete(self, fileName):
        """Apaga um ficheiro"""
        # Rastreia a requisição DELETE para o endpoint '/files/<fileName>'
        REQUEST_COUNT.labels(endpoint='/files/<fileName>', method='DELETE').inc()

        if fileName not in FILES:
            return {'message': 'Ficheiro não encontrado'}, 404
        
        del FILES[fileName]
        print(f"Ficheiro {fileName} apagado.")
        return {'message': f'Ficheiro {fileName} apagado'}, 200


if __name__ == '__main__':
    # 5. Configuração do Middleware para expor as métricas
    # O DispatcherMiddleware combina a sua aplicação Flask (para a API) com a aplicação do Prometheus (para /metrics).
    app_with_metrics = DispatcherMiddleware(
        app.wsgi_app, 
        {'/metrics': make_wsgi_app()}
    )
    
    # Executa a aplicação com o DispatcherMiddleware
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5000, app_with_metrics, use_reloader=True, threaded=True)