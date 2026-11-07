#!/usr/bin/env python3
"""Run the synthetic browser/Git persistence lab. No project or public writes."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/intake'))
from git_store import Writer, StoreError, Conflict, initialize_lab
import song_data_contract as contract


def serve(repo, port=0):
    writer = Writer(repo)
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass

        def respond(self, status, value, content_type='application/json'):
            body = value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
            raw = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type',content_type+'; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def correct_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.correct_host():
                return self.respond(403,{'error':'loopback host required'})
            if self.path != '/':
                return self.respond(404,{'error':'not found'})
            try:
                song = writer.current('fixture-representative')
                template = (ROOT/'releases/luminous-v7.0.0-rc.1/template.html').read_text()
                page = contract.render_song_html(template,song,'synthetic-git-adapter.1')
                config = '<script>window.BANDSHEET_WRITER='+json.dumps({'token':token})+';</script>'
                page = page.replace('<script id="bandsheet-revision"',config+'<script id="bandsheet-revision"')
                self.respond(200,page,'text/html')
            except (StoreError,ValueError) as error:
                self.respond(503,{'error':str(error)})

        def do_POST(self):
            expected_origin = f'http://127.0.0.1:{self.server.server_port}'
            if not self.correct_host() or self.headers.get('Origin') != expected_origin or not secrets.compare_digest(self.headers.get('X-Bandsheet-Token',''),token):
                return self.respond(403,{'error':'same-origin writer token required'})
            if self.path != '/api/save':
                return self.respond(404,{'error':'not found'})
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 2_000_000:
                    return self.respond(413,{'error':'invalid request size'})
                if self.headers.get_content_type() != 'application/json':
                    return self.respond(415,{'error':'JSON required'})
                request = contract.parse_json(self.rfile.read(length).decode('utf-8'))
                result = writer.save(request)
                self.respond(200,result)
            except Conflict as error:
                self.respond(409,{'error':str(error)})
            except (ValueError,UnicodeError) as error:
                self.respond(422,{'error':str(error)})
            except Exception:
                self.respond(503,{'error':'writer failure; request is not acknowledged'})
    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/','mode':'synthetic-local-test-remote'}),flush=True)
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    init = sub.add_parser('init');init.add_argument('--directory',required=True)
    run = sub.add_parser('serve');run.add_argument('--repo',required=True);run.add_argument('--port',type=int,default=0)
    verify = sub.add_parser('verify');verify.add_argument('--repo',required=True)
    args = parser.parse_args()
    if args.command == 'init':
        repo = initialize_lab(args.directory,contract.load_json(ROOT/'tests/fixtures/song-data/representative.json'))
        print(json.dumps({'repo':str(repo),'authority':'local-test-remote-only'}))
    elif args.command == 'verify':
        print(json.dumps(Writer(args.repo).verify(),indent=2))
    else:
        serve(args.repo,args.port)
