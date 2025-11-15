# app.py
from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import traceback
import config

def create_app():
    app = Flask(__name__, static_folder="frontend", template_folder="templates")
    app.config.from_pyfile("config.py", silent=True)
    CORS(app)

    # import and register API blueprint
    from backend.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # serve index
    @app.route("/", methods=["GET"])
    def index():
        return app.send_static_file("index.html")

    # allow static files under /frontend
    @app.route("/frontend/<path:p>", methods=["GET"])
    def frontend_static(p):
        return send_from_directory("frontend", p)

    # Optional: JSON error handler for unexpected exceptions
    @app.errorhandler(Exception)
    def handle_exception(e):
        print("Global exception:", type(e).__name__, e)
        traceback.print_exc()
        from flask import jsonify
        return jsonify({"error": "internal_server_error", "type": type(e).__name__, "details": str(e)}), 500

    return app

# --- Ensure app exists at module level so decorators below always work ---
app = create_app()

# run only when executed directly
if __name__ == "__main__":
    os.makedirs("instance", exist_ok=True)
    app.run(debug=True)
