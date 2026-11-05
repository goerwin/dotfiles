#!/usr/bin/env python3
"""Open a worktree and a foreground Herdr tab with an interactive Codex handoff."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from goerwin_tools import herdr_adapter


def run(argv, *, as_json=False, timeout=30):
    """Execute an argument list without shell interpolation."""
    env = os.environ.copy()
    # Structural tab launches must not inherit the source terminal as a parent.
    env.pop('HC_TERMINAL_ID', None)
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f'{argv[0]} failed ({result.returncode})')
    return json.loads(result.stdout) if as_json else result.stdout.strip()


def app(command, parameters):
    """Use Herdr's structured command interface."""
    result = run(['herdr-app', 'do', command, json.dumps(parameters)], as_json=True, timeout=90)
    if result.get('error'):
        raise RuntimeError(str(result['error']))
    return result


def save(path, receipt):
    """Persist launch IDs before performing focus and verification operations."""
    path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')


def launch(args, receipt_path, receipt):
    """Create exactly one visible agent tab; never retry an uncertain launch."""
    task = args.task_file.read_text(encoding='utf-8').strip()
    if not task:
        raise RuntimeError('The handoff file is empty')
    for executable in ['goerwin-wt', 'herdr-app', 'hc', 'codex']:
        if not shutil.which(executable):
            raise RuntimeError(f'Required executable is unavailable: {executable}')

    # Check socket access before creating a checkout. Inspect again after resolution.
    run(['herdr-app', 'ls'], as_json=True)
    target_path = Path(args.target).expanduser()
    if not target_path.is_absolute():
        target_path = args.cwd / target_path
    explicit_path = Path(args.target).expanduser().is_absolute() or args.target.startswith(('./', '../', '~'))
    if target_path.is_dir() and (explicit_path or (target_path / '.git').exists()):
        if args.base:
            raise RuntimeError('A base is only valid for a branch target, not a worktree path')
        target, cwd = str(target_path.resolve()), str(target_path.resolve())
    else:
        target, cwd = args.target, str(args.cwd)
    command = ['goerwin-wt', 'switch', target]
    if args.base:
        command.append(args.base)
    command.extend(['-C', cwd, '--json'])
    resolved = run(command, as_json=True, timeout=1800)
    folder, branch = resolved['path'], resolved['branch']
    reused = resolved.get('reused', False)
    folder = os.path.realpath(folder)
    state = herdr_adapter.presentation()
    space = herdr_adapter.local_space(state, folder)
    argv = ['codex', '--no-daemon', '--model', args.model,
            '-c', 'model_reasoning_effort=' + json.dumps(args.effort)]
    title = args.tab_name or f'{branch or Path(folder).name} · {args.model} {args.effort}'
    parameters = {'folder': folder, 'argv': argv, 'task': task}
    if space:
        command = 'tab.new'
        parameters.update({'space': space['id'], 'name': title})
    else:
        command = 'space.new'
        parameters.update({'name': branch or Path(folder).name, 'tab': title, 'machine': ''})
    receipt.update({'status': 'launching', 'worktree': folder, 'branch': branch,
                    'reused_worktree': reused, 'model': args.model,
                    'effort': args.effort, 'tab_name': title})
    save(receipt_path, receipt)
    opened = app(command, parameters)
    receipt.update(opened)
    receipt['status'] = 'created'
    save(receipt_path, receipt)
    terminal, tab = opened.get('terminal'), opened.get('tab')
    if not terminal or not tab:
        raise RuntimeError('Herdr omitted launch IDs; inspect Herdr before attempting another launch')
    app('tab.select', {'id': tab})
    app('pane.focus', {'terminal': terminal})
    run(['herdr-app'])
    ui = run(['herdr-app', 'status'], as_json=True)
    agent = run(['hc', 'get', terminal], as_json=True)
    foreground = agent.get('foreground') or {}
    actual_argv = foreground.get('argv') or []
    visible = ui.get('tab') == tab and ui.get('agent') == terminal
    started = (agent.get('state') == 'live' and foreground.get('name') == 'codex'
               and os.path.realpath(foreground.get('cwd') or '') == folder
               and '--no-daemon' in actual_argv
               and args.model in actual_argv
               and 'model_reasoning_effort=' + json.dumps(args.effort) in actual_argv)
    independent = not agent.get('parent') or agent.get('die_with_parent') is False
    receipt.update({'status': 'verified' if visible and started and independent else 'needs-inspection',
                    'focused': visible, 'agent_started': started,
                    'independent_session': independent,
                    'terminal_state': agent.get('state'),
                    'agent_status': agent.get('status'),
                    'foreground_program': foreground.get('name')})
    save(receipt_path, receipt)
    if agent.get('state') == 'finished' or not visible or not independent:
        raise RuntimeError('Agent exited, focus was not confirmed, or session depends on its parent; inspect the recorded terminal')


def main():
    """Resolve the requested checkout, launch the handoff, and print its receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', help='Branch, PR number/URL, or existing worktree directory')
    parser.add_argument('base', nargs='?', help='Base for a new branch')
    parser.add_argument('-C', '--cwd', type=Path, default=Path.cwd(), help='Source repository')
    parser.add_argument('--task-file', type=Path, required=True, help='UTF-8 handoff context file')
    parser.add_argument('--tab-name', help='Visible Herdr tab title')
    parser.add_argument('--model', default='gpt-6.1-sol')
    parser.add_argument('--effort', default='high', choices=['low', 'medium', 'high', 'xhigh', 'max', 'ultra'])
    args = parser.parse_args()
    receipt_path = Path(tempfile.mkdtemp(prefix='goerwin-handoff-')) / 'launch.json'
    receipt = {'receipt': str(receipt_path), 'task_file': str(args.task_file.resolve()), 'status': 'preparing'}
    save(receipt_path, receipt)
    print(json.dumps({'receipt': str(receipt_path)}), flush=True)
    try:
        launch(args, receipt_path, receipt)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as error:
        receipt.update({'status': 'needs-inspection' if receipt.get('terminal') or receipt.get('status') == 'launching' else 'failed',
                        'error': str(error)})
        save(receipt_path, receipt)
        print(json.dumps(receipt, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
