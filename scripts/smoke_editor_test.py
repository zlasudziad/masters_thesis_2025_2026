import importlib
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'phantom' package can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

m = importlib.import_module('phantom.editor')
app = m.main(run=False, canvas_w=200, canvas_h=120)
if app is None:
    print('app is None')
else:
    print('app created:', app is not None)
    print('layers:', [l.name for l in app.layers])
    for l in app.layers:
        print(l.name, 'size=', getattr(l.pil_image, 'size', None))
