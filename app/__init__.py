import os
from flask import Flask

def create_app():
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(project_root, 'templates')

    app = Flask(__name__, template_folder=template_dir)

    # Set upload folder path in config
    upload_folder = os.path.join(project_root, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)  # create if missing
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['PROCESSED_FOLDER'] = os.path.join(project_root, 'processed')

    from app.routes.upload import upload_bp
    from app.routes.search import search_bp

    print("Registering blueprints...")
    app.register_blueprint(upload_bp)
    print("Registered upload_bp")
    app.register_blueprint(search_bp)
    print("Registered search_bp")




    return app
