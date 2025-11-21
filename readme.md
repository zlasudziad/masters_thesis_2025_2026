I'm a biomedical engineer who's currently attempting to finish their master's thesis after a health-related break. Joy.

**Disclaimer**: the entirety of this code was written in ungodly hours of 11 PM - 5 AM usually since I do have a 9-5 and
a desire to have some semblance of life after work, so please excuse any rough edges, weird design choices, 
and general lack of polish. I'm just trying to get this thing done half a year after I should have, and if that means
sacrificing code quality and working in ADHD-fueled bursts of energy at night, so be it.

Shoutout to my thesis reviewer who might open this repo and think "what the actual _ is this traumadumping in the readme"
should they decide to look at the previous commits.

This repository contains scripts and small tools used during the work on my master's thesis (Wrocław University of Science and Technology). It's set to
public so that I can share it with my supervisor (once it's somewhat presentable). Maybe attach the link to the actual thesis.
Technically, I probably should create a fresh repo for that, but eh, all the people who will potentially look at this repo
and care about the version history already know what kind of person I am.


Note that all the code here is written with the intention to be used in a highly specific task (retinal OCT image simulation and analysis
and, hopefully, segmentation once it's ready and polished enough),
so if you stumbled across this repo, please be aware that it may not be directly, or at all applicable to your use case. 
It's also suboptimal in many ways, probably sucks performance-wise, and I make no guarantees about anything at all. 

If you have any questions about my thesis itself, feel free to contact me (Discord: @lesnodziadyzm is probably the best way to get to me).

What is uploaded here is a version that is cleaned of comments that shouldn't be talked about in polite company, but 
still might contain rough edges, hardcoded paths, and other things that are not ideal. To be fair, this code
isn't really intended for public use since:

1 - it's part of an ongoing master's thesis with specific goals in mind.

2 - it's going to get increasingly specific as I add stuff here, but if you find 
it useful, that's great.

3 - I prioritize getting this thing FINALLY done over writing perfect, reusable code in this case. 

Oh, and the OCT image under /real_OCT is of my right eye. Feel free to admire my myoptic retina.

---



Quick setup (PowerShell)
1. Create and activate a virtual environment (recommended):

    python -m venv .venv; .\.venv\Scripts\Activate

2. Install dependencies (the repo `requirements.txt` covers some packages; add OpenCV and SciPy):

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m pip install opencv-python scipy

Running the tools
- Interactive gamma-fit GUI (select rectangles):

    python scripts/get_shape_scale.py

  The script will open a file picker (if `tkinter` is available) or ask for paths in the console. For each named layer it shows an OpenCV window where you can click-and-drag a rectangle. Press Enter or `q` to accept a selection. The output is a JSON file you choose (commonly `gamma_parameters.json`).

- Layer editor (drag layers and auto-save positions):

    python scripts/run_editor.py

  When you close the editor it auto-saves layer positions to `json_outputs/layer_positions.json` and writes `phantom.png` as a composite image.
  By layer positions I mean the top coordinates of each layer since they all overlap.

Notes & troubleshooting
- Required: `Pillow`, `numpy`, `svgpathtools`, `matplotlib`, plus `opencv-python` (not headless) and `scipy`.
- If the file picker does not open, your Python may lack the Tk runtime; install the official Python distribution from python.org or use the console prompts.
- Example inputs will be added later.
- Fun fact: originally this thing was written in MATLAB but I switched to Python like 1/3 into the thesis because I hate MATLAB. I know it's popular in DSP. I also know it's faster for computation-heavy tasks. Python has a huge advantage of not making my sanity slowly erode away as I stare at that godawful IDE for hours on end. Mine at least has Gojo in the background.

![not joking](gojo.png)

Not even joking. If you recognize the art, shame on you (love the artist though, @_lildev__ on X). If you're my supervisor or the reviewer and reading this, please don't look them up. 

Tests
- Run the unit tests with:

    python -m pytest -q