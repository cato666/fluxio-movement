"""Artifacts required by the worker, used only when its analyzer is stubbed."""
import json
from pathlib import Path


def write_analysis(output_dir, result):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'annotated.mp4').write_bytes(b'annotated-test-video')
    (output / 'analysis.json').write_text(json.dumps(result), encoding='utf-8')
    return result
