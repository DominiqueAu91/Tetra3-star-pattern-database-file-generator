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


In each case, generate your `.npz` with `max_fov` set close to that HFOV and `min_fov=value` with value  > max_fov/1.5. In my case, PiHQ Camera and 12.5mm lens I choose max_fov = 30° and min_fov = 25°.

---
#### Choosing a suitable magnitude limit

A good rule of thumb:  
- **Set the database star magnitude limit ~0.5–1 mag fainter than your camera can reliably detect in your typical exposure**.  
- This ensures the DB has all stars you will see, but not millions of faint stars that only bloat the file and slow solving.

Typical values (for 0.5 s exposure, rural Bortle 3–4 sky):  
- **IMX477 + 12.5 mm f/1.3** → stars to ~mag 9.0 → use `star_max_magnitude ≈ 9`  
- **IMX296 + 16 mm f/2** → stars to ~mag 8.0–8.5 → use `star_max_magnitude ≈ 8`

---
### Generate a database (PiFinder context)

PiFinder uses **Cedar Detect**, a fork of Tetra3, for star pattern recognition.  
Cedar’s guidelines are to set the database `max_fov` to match the **horizontal field of view (HFOV) of your sensor/lens combination** (not the diagonal).  
This ensures the generated star patterns scale properly and keeps the database size efficient.

> Example:  
> - Pi HQ Camera (IMX477) + 12.5 mm lens → HFOV ≈ 28.5°  
> - IMX296 + 16 mm lens → HFOV ≈ 17–18°  


---

#### Which database does PiFinder actually use?

Although you may find multiple `.npz` files under `/home/pifinder/PiFinder/astro_data/`,  

PiFinder loads the following file at runtime:

`/home/pifinder/PiFinder/python/PiFinder/tetra3/tetra3/data/default_database.npz`

If you want PiFinder to use your own custom database, you must replace this file with your own `.npz`.

---

#### How to replace the database on PiFinder

1. **Copy your custom locally generated `.npz` to the PiFinder**, e.g. into `/home/pifinder/astro_data/` using Windows shell:
   ```bash
   scp my_custom_db.npz pifinder@pifinder.local:/home/pifinder/astro_data/

2. **SSH into the PiFinder:**
   `ssh pifinder@pifinder.local     # password: solveit`

3. **Backup the original database:**
   
 ` cd /home/pifinder/PiFinder/python/PiFinder/tetra3/tetra3/data
mv default_database.npz default_database.bak.npz`

4. **Replace it with your custom one:**
   `cp /home/pifinder/astro_data/my_custom_db.npz /home/pifinder/PiFinder/python/PiFinder/tetra3/tetra3/data/default_database.npz`

5. **Restart PiFinder service**
   
  ` sudo systemctl restart pifinder`

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
## Plate Solving Detectability Calculations

To compare the effectiveness of different lenses and sensors for PiFinder, we estimated the limiting magnitude
and the number of stars available for plate solving under a **good rural sky (Bortle 4)** with **0.5 s exposures**.

### Methodology

- **Star flux scaling**  
  Star signal ∝ Aperture_Area × QE × Exposure_Time

- **Sky background per pixel**  
  Sky background ∝ QE × Exposure_Time × (Pixel_Size² / f#²)

- **Signal-to-noise ratio (SNR)**  
  SNR ∝ Signal / sqrt(Background)

- **Magnitude difference**  
  Δm = 2.5 × log10(SNR_ratio)

- **Star counts**  
  Estimated from cumulative Hipparcos/Tycho catalogs, scaled to the field-of-view (FOV).

---

### Input Parameters

| Setup | Sensor | Pixel size | QE (green) | Lens | f/# | Aperture D | Area A |
|-------|--------|------------|------------|------|-----|------------|--------|
| A | IMX477 (HQ Cam) | 1.55 µm | ~0.75 | 12.5 mm | 1.3 | 9.6 mm | 72.6 mm² |
| B | IMX296 (mono) | 3.45 µm | ~0.64 | 16 mm | 2.0 | 8.0 mm | 50.3 mm² |

---

### Step 1 — Relative star signal

Signal ratio (A/B) = (72.6 × 0.75) / (50.3 × 0.64) ≈ **1.69**

→ IMX477 setup records ~1.7× more star photons.

---

### Step 2 — Relative sky background

Background ratio (A/B) = (0.75 × (1.55² / 1.3²)) / (0.64 × (3.45² / 2.0²)) ≈ **0.56**

→ IMX477 setup has ~44% less sky noise per pixel.

---

### Step 3 — Relative SNR

SNR ratio = 1.69 / sqrt(0.56) ≈ **2.26**

→ IMX477 setup has ~2.3× higher SNR for faint stars.

---

### Step 4 — Magnitude depth

Δm = 2.5 × log10(2.26) ≈ **0.89 mag**

→ IMX477 reaches ~0.9 mag deeper than IMX296 at 0.5 s.

---

### Step 5 — Field-of-view star counts

- **IMX477 + 12.5 mm f/1.3**  
  - FOV ≈ 28.5° × 21.4° (≈610 deg²)  
  - Limiting magnitude ≈ 9.2  
  - Star density ≈ 4.4 stars/deg²  
  - → ~2,700 stars per frame (range 1,300–5,300 depending on sky region)

- **IMX296 + 16 mm f/2**  
  - FOV ≈ 18.0° × 13.4° (≈241 deg²)  
  - Limiting magnitude ≈ 8.4  
  - Star density ≈ 2.1 stars/deg²  
  - → ~500 stars per frame (range 250–1,000 depending on sky region)

---

### Interpretation

- **IMX477 + 12.5 mm f/1.3**  
  - Deeper by ~0.9 mag  
  - Larger field (≈2.5× area of IMX296 setup)  
  - Thousands of stars per frame  
  - → Very robust plate solving everywhere in the sky

- **IMX296 + 16 mm f/2**  
  - Shallower limit (~mag 8.4)  
  - Narrower field (~241 deg²)  
  - A few hundred stars per frame  
  - → Usually sufficient, but less reliable in sparse regions (e.g. near galactic poles)

---

### Conclusion

For plate solving with 0.5 s exposures under rural skies:
- **IMX477 + 12.5 mm f/1.3** offers superior robustness, with ~2,700 stars per frame and deeper limiting magnitude.  
- **IMX296 + 16 mm f/2** is usable but closer to the edge, with ~500 stars per frame. Increasing exposure to 1–2 s improves reliability across the whole sky.

---
## PiFinder Examples

For Raspberry Pi HQ cam with:

- **12.5 mm lens**  
  FOV ≈ 30–36°, mag limit ≈ 9  
  ```bash
  python tetra3_pipeline.py generate-db --star-catalog hip_main --catalog-dir "./catalogs" \
    --min-fov 30 --max-fov 36 --star-max-magnitude 9 \
    -o db_pifinder_12p5mm.npz
  ```

- **16 mm lens**  
  FOV ≈ 10–20°, mag limit ≈ 8  
  ```bash
  python tetra3_pipeline.py generate-db --star-catalog hip_main --catalog-dir "./catalogs" \
    --min-fov 10 --max-fov 20 --star-max-magnitude 8 \
    -o db_pifinder_16mm.npz
  ```

These custom DBs can be copied to your PiFinder device.

---

## Troubleshooting

- **`Could not import 'tetra3'`** → install from source (`pip install .` inside the cloned tetra3 repo).  
- **`hip_main.dat not found`** → place the raw file in `./catalogs/`.  
- **PowerShell parsing errors** → paste as one line, or use backticks (`` ` ``) for line continuation.  
- **Slow DB generation** → reduce `--star-max-magnitude` or narrow your FOV range.  



