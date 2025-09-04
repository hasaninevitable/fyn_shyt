import os
from flask import Flask, send_from_directory

def create_app():
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    app.secret_key = 'hasn'  # Add this line with a unique secret key

    app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.config['PROCESSED_FOLDER'] = os.path.join(project_root, 'processed')

    from app.routes.upload import upload_bp
    from app.routes.search import search_bp
    from app.routes.viewer import viewer_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(viewer_bp)

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app
