"""Local panel entry point. Binding succeeds before opening the browser."""
import secrets
import threading
import webbrowser
from urllib.parse import urlsplit
from pathlib import Path

from .config import data_root
from .errors import MapperError
from .ui.controller import Controller


def protect_server(server):
    from flask import request, session, abort
    server.secret_key = secrets.token_bytes(32)
    server.config.update(MAX_CONTENT_LENGTH=141 * 1024**2,
                         SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                         SESSION_COOKIE_NAME='mapper_session_' + secrets.token_hex(6))

    @server.before_request
    def local_session():
        # Ignore forwarding headers. Only a request for this loopback listener is valid.
        host = request.host.split(':')[0]
        if host != '127.0.0.1':
            abort(403)
        origin = request.headers.get('Origin')
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme != 'http' or parsed.netloc != request.host:
                abort(403)
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            if not origin or not session.get('token'):
                abort(403)
            # A valid same-site signed session plus exact Origin protects callbacks.
        elif request.path == '/':
            session.setdefault('token', secrets.token_urlsafe(32))

    @server.after_request
    def private_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        return response


def create_app(root, *, offline=False, controller=None):
    from .ui.panel import create_panel
    controller = controller or Controller(root, offline=offline)
    try:
        app = create_panel(controller, Path(__file__).parent / 'ui' / 'assets')
        protect_server(app.server)
        app.mapper_controller = controller
        return app
    except BaseException:
        controller.close()
        raise


def run(root=None, *, port=8050, open_browser=True, offline=False):
    if type(port) is not int or not 1 <= port <= 65535:
        raise MapperError('INVALID_PORT')
    from werkzeug.serving import make_server, WSGIRequestHandler
    class Quiet(WSGIRequestHandler):
        def log_request(self, *args, **kwargs):
            pass  # URLs, cookies and request data never enter access logs.
    controller = Controller(data_root(root), offline=offline)
    server = None
    try:
        try:
            app = create_app(controller.root, controller=controller)
        except ImportError:
            raise MapperError('PANEL_DEPENDENCIES_MISSING') from None
        try:
            server = make_server('127.0.0.1', port, app.server, threaded=True, request_handler=Quiet)
        except (OSError, SystemExit):
            raise MapperError('PANEL_PORT_UNAVAILABLE') from None
        url = f'http://127.0.0.1:{server.server_port}'
        print(f'Panel lokalny: {url}', flush=True)
        ready = threading.Event()
        stop = threading.Event()
        original = server.service_actions
        def actions():
            original()
            ready.set()
        server.service_actions = actions
        def launch():
            if ready.wait(5) and not stop.is_set():
                try:
                    webbrowser.open(url)
                except (webbrowser.Error, OSError):
                    pass  # Clickable URL is already printed.
        if open_browser:
            threading.Thread(target=launch, daemon=True).start()
        try:
            server.serve_forever(poll_interval=.1)
        finally:
            stop.set()
    finally:
        if server:
            server.server_close()
        controller.close()
