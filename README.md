# Tetra3 Star-Pattern Database File Generator

This repository provides a Python command-line utility (`tetra3_pipeline.py`) to generate
**custom Tetra3 star-pattern database files** from raw catalogs such as Hipparcos, Tycho, or BSC5.  

My personal purpose in writing this tool was to generate **custom star databases for the official** [PiFinder project](https://www.pifinder.io/),
where I needed different database files to match **different camera lenses** (for example, 12.5 mm and 16 mm lenses
on the Raspberry Pi HQ Camera).

While the official [Tetra3 project](https://github.com/esa/tetra3) provides the solver itself, this script is designed to make
**database generation reproducible, configurable, and easy to run** on Windows, macOS, and Linux.

---

## Features
- Generate a `.npz` star-pattern database tailored to your **field of view (FOV)** and **magnitude limit**.
- Supports **Hipparcos**, **Tycho-2**, and **BSC5** star catalogs.
- Includes a `solve` command to test your images with the generated DB.
- CSV logging of solve results.
- Example configs for **PiFinder-style setups**.

---

## Installation

```bash
# clone this repo
git clone https://github.com/<your-username>/tetra3-pipeline.git
cd tetra3-pipeline

# install requirements
pip install -r requirements.txt

requirements.text contains:

numpy
astropy
opencv-python
git+https://github.com/esa/tetra3.git

```

Download a catalog file (e.g. `hip_main.dat`) and place it in `./catalogs/`.

---

## Usage

### Generate a database

**Windows (PowerShell):**
```powershell
python .\tetra3_pipeline.py generate-db --star-catalog hip_main --catalog-dir ".\catalogs" `
  --min-fov 30 --max-fov 36 --star-max-magnitude 8.0 `
  -o db_12p5mm_from_hip.npz
```

**macOS / Linux (bash):**
```bash
python3 ./tetra3_pipeline.py generate-db --star-catalog hip_main --catalog-dir "./catalogs" \
  --min-fov 30 --max-fov 36 --star-max-magnitude 8.0 \
  -o db_12p5mm_from_hip.npz
```

- `--min-fov` / `--max-fov`: range in degrees (set to match your lens + sensor).  
- `--star-max-magnitude`: depth of catalog; higher = deeper but slower DB.  
- `-o`: output `.npz` file.  

---

### Solve images

**Windows:**
```powershell
python .\tetra3_pipeline.py solve ".\examples" --database .\db_12p5mm_from_hip.npz `
  --fov-estimate 35 --fov-max-error 1.5 `
  --min-sum 500 --max-axis-ratio 1.5 --min-distance 4 `
  --csv results.csv
```

**macOS / Linux:**
```bash
python3 ./tetra3_pipeline.py solve "./examples" --database ./db_12p5mm_from_hip.npz \
  --fov-estimate 35 --fov-max-error 1.5 \
  --min-sum 500 --max-axis-ratio 1.5 --min-distance 4 \
  --csv results.csv
```

The results will be logged in `results.csv`.

---

## PiFinder Examples

For Raspberry Pi HQ cam with:

- **12.5 mm lens**  
  FOV ≈ 30–36°, mag limit ≈ 8  
  ```bash
  python tetra3_pipeline.py generate-db --star-catalog hip_main --catalog-dir "./catalogs" \
    --min-fov 30 --max-fov 36 --star-max-magnitude 8 \
    -o db_pifinder_12p5mm.npz
  ```

- **16 mm lens**  
  FOV ≈ 24–28°, mag limit ≈ 8  
  ```bash
  python tetra3_pipeline.py generate-db --star-catalog hip_main --catalog-dir "./catalogs" \
    --min-fov 24 --max-fov 28 --star-max-magnitude 8 \
    -o db_pifinder_16mm.npz
  ```

These custom DBs can be copied to your PiFinder device.

---

## Troubleshooting

- **`Could not import 'tetra3'`** → install from source (`pip install .` inside the cloned tetra3 repo).  
- **`hip_main.dat not found`** → place the raw file in `./catalogs/`.  
- **PowerShell parsing errors** → paste as one line, or use backticks (`` ` ``) for line continuation.  
- **Slow DB generation** → reduce `--star-max-magnitude` or narrow your FOV range.  



