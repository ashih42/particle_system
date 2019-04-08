# particle_system
A [particle system](https://en.wikipedia.org/wiki/Particle_system) in Python using OpenGL and OpenCL. (42 Silicon Valley)

## Prerequisites

You are on macOS with `python3` and `brew` installed.

## Installing

```
./setup/setup.sh
```

### Installing PyOpenCL

* Git clone [pyopencl](https://github.com/inducer/pyopencl) and run `configure.py`
```
git clone https://github.com/inducer/pyopencl
cd pyopencl
python3 configure.py
```
* Edit `siteconf.py`
  * CL_ENABLE_GL = True
* Pip install
```
- pip3 install -e .
```

## Running

Initialize with `n` particles.

```
source setup/env.sh;
python3 main.py n
```

## Controls

### Top-level Controls

* `Tab` Select next particle mode.
* `G` Toggle gravity on/off.
* `P` Select perspective or orthographic projection.
* `Escape` Terminate the renderer.

### Particle Controls

* `Page Up` Increase sprite size.
* `Page Down` Decrease sprite size.
* `L` Toggle particle lifetime decay on/off.
* `X` Toggle particle size proportional to lifetime.

### Shading Controls

* `Move Mouse` Set light source position.
* `C` Select next color profile.
* `T` Toggle texture on/off.

### Generator Controls

* `Z` Set generator as sphere or cube.
* `Left Control` + `Move Mouse` Move generator.
* `Left Arrow` Move generator toward camera left.
* `Right Arrow` Move generator toward camera right.
* `Down Arrow` Move generator toward camera down.
* `Up Arrow` Move generator toward camera up.
* `Home` Move generator toward camera back.
* `End` Move generator toward camera front.

### Camera Controls

* `Left Shift` + `Move Mouse` Rotate camera.
* `W` Move camera toward camera front.
* `S` Move camera toward camera back.
* `A` Move camera toward camera left.
* `D` Move camera toward camera right.
* `Q` Move camera toward camera down.
* `E` Move camera toward camera up.
