from .admin import admin_bp
from .crewmembers import crewmember_bp
from .user import user_bp
from .objects import objects_bp
from .job_template import job_template_bp
from .lsyrept import lsyrept_bp
from .ofp_file import ofp_file_bp

def init_app(app):
    app.register_blueprint(crewmember_bp, url_prefix='/crewmembers')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(objects_bp, url_prefix='/objects')
    app.register_blueprint(job_template_bp, url_prefix='/job-template')

    # command-line only blueprints
    app.register_blueprint(lsyrept_bp)
    app.register_blueprint(ofp_file_bp)
