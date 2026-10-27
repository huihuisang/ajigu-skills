"""Read installed skills through the local app-server without invoking a model."""

import json
import os
from pathlib import Path
import select
import subprocess
import time


def inventory(workspace, environment, output):
    with (output / 'codex-app-server.log').open('wb') as errors:
        process = subprocess.Popen(['codex', 'app-server', '--stdio'], cwd=workspace,
                                   env=environment, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors)
        pending = b''

        def send(value):
            process.stdin.write((json.dumps(value) + '\n').encode('utf-8'))
            process.stdin.flush()

        def receive(request_id):
            nonlocal pending
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    if not line:
                        continue
                    value = json.loads(line)
                    if value.get('id') == request_id:
                        if 'error' in value:
                            raise RuntimeError('The app-server rejected the inventory request.')
                        return value['result']
                if select.select([process.stdout], [], [], 1)[0]:
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError('The app-server exited before returning its inventory.')
                    pending += chunk
            raise TimeoutError('The app-server inventory request timed out.')

        try:
            send({'id': 0, 'method': 'initialize', 'params': {
                'clientInfo': {'name': 'ajigu-plugin-check', 'version': '0.1.0'},
                'capabilities': {'experimentalApi': True}}})
            receive(0)
            send({'method': 'initialized'})
            send({'id': 1, 'method': 'skills/list', 'params': {
                'cwds': [str(workspace)], 'forceReload': True}})
            result = receive(1)
            (output / 'codex-runtime-skills.json').write_text(
                json.dumps(result, indent=2) + '\n', encoding='utf-8')
            return result
        finally:
            try:
                process.stdin.close()
            except BrokenPipeError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            process.stdout.close()
