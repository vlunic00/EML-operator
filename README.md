# EML Phylogenetic Real-Time Engine

A high-performance evolutionary algorithm system for discovering mathematical expressions by repeatedly applying the **EML operator** to find target numeric values. This project combines a Python GUI with a multi-threaded Rust backend to search for mathematical expressions in real-time.

## 🎯 Overview

The **EML Operator** (`eml(x, y) = e^x - ln(y)`) is applied to pairs of values in a "gene pool" to evolve new mathematical expressions. The system treats this as a phylogenetic search problem—starting with initial constants, it discovers new values through operator composition, building a library of "species" (named constants).

### Key Features

- **Real-time visualization** of the search process via a Tkinter GUI
- **Multi-threaded backend** leveraging all CPU cores for parallel computation
- **Milestone tracking** that automatically identifies and catalogs significant discoveries (like *e* ≈ 2.71828)
- **Phylogenetic library** maintaining a history of discovered constants and their relationships
- **Cross-platform support** (Windows, macOS, Linux)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Python Frontend (Tkinter)              │
│  • Interactive button interface         │
│  • Real-time milestone display          │
│  • Phylogenetic library sidebar         │
└────────────────┬────────────────────────┘
                 │ (subprocess)
                 │ (stdout streaming)
                 ↓
┌─────────────────────────────────────────┐
│  Rust Backend (Multi-threaded)          │
│  • Parallel brute-force search          │
│  • Thread-safe gene pool                │
│  • Real-time result streaming           │
└─────────────────────────────────────────┘
```

### Communication Protocol

The Python frontend launches the Rust backend as a subprocess and communicates via:

**Command-line arguments:**
```
backend.exe <target_real> <target_imag> <name1> <value1> <name2> <value2> ...
```

**stdout protocol:**
- `THREAD_LIVE: Core N` — Thread startup notification
- `DEBUG: ...` — Periodic progress updates (every 1M combinations)
- `MILESTONE: name = eml(a,b)` — New significant value discovered
- `FINAL: eml(a,b)` — Target found! Search complete

## 📊 The EML Operator

The core mathematical function:

```
eml(x, y) = e^x - ln(y)
```

Where:
- **e** is Euler's number (≈ 2.71828)
- **^** is exponentiation
- **ln** is the natural logarithm
- **x, y** are Complex64 numbers

**Validation:** If `|y| < 1e-9`, the function returns NaN (to avoid undefined logarithm).

## 🔧 Project Structure

```
Operator Visualization/
├── main.py                      # Python GUI frontend
├── backend/
│   ├── Cargo.toml               # Rust project manifest
│   ├── src/
│   │   └── main.rs              # Multi-threaded search engine
│   └── target/release/
│       └── backend.exe          # Compiled binary (Windows)
├── operator/                    # Python virtual environment
│   ├── pyvenv.cfg
│   ├── Lib/site-packages/       # Installed Python packages
│   └── Scripts/                 # Virtual environment scripts
├── EML Operator.pdf             # Reference research paper (arXiv)
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (virtual environment already configured in `operator/`)
- **Rust 1.70+** (if building the backend)
- **Windows/macOS/Linux** (cross-platform support)

### Running the Application

1. **Ensure dependencies are installed** (already configured in the `operator/` venv):
   ```bash
   cd "C:\Users\vedro\Documents\Development\Operator Visualization"
   .\operator\Scripts\Activate.ps1
   ```

2. **Build the Rust backend** (skip if binary already compiled):
   ```bash
   cd backend
   cargo build --release
   cd ..
   ```

3. **Run the Python frontend**:
   ```bash
   python main.py
   ```

4. **Usage:**
   - Click operator buttons (`+ - * / ln(x)`) to start a search
   - Watch real-time milestone discoveries in the display panel
   - The phylogenetic library builds up on the right sidebar
   - Results show the discovered formula when found

### Test Values

The application includes default test values:
- **x** = 0.577215 (Euler-Mascheroni constant γ)
- **y** = 1.282427 (Khinchin's constant, approximately)

Target values calculated from these:
- `"+"`: x + y ≈ 1.859642
- `"-"`: x - y ≈ -0.705212
- `"*"`: x × y ≈ 0.740728
- `"/"`: x ÷ y ≈ 0.450122
- `"ln(x)"`: ln(x) ≈ -0.549765

## 🧬 Evolutionary Algorithm

The search process works as follows:

### Per-Thread Search Loop

1. **Random Selection:** Randomly pick two species from the gene pool
2. **Computation:** Apply `eml(species_a, species_b)`
3. **Target Check:** If result ≈ target (within 1e-5), announce `FINAL`
4. **Milestone Detection:** If result ≈ *e* or ≈ 0, add as new species in pool
5. **Pool Growth:** Periodically add new computed values to the pool
6. **Repeat:** Continue until target found or termination

### Thread Coordination

- **Shared State:** Gene pool managed via `Arc<RwLock<Vec<Species>>>`
- **Atomic Flag:** `is_found` flag prevents wasted computation after success
- **Per-Core Seeding:** Each thread uses unique LCG seeds for reproducible randomness
- **Scaling:** Automatically spawns threads for all available CPU cores

## 💻 Technical Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Frontend** | Python, Tkinter, NumPy | 3.14 |
| **Backend** | Rust | 2021 edition |
| **Complex Math** | `num-complex` | 0.4 |
| **CPU Detection** | `num_cpus` | 1.13 |
| **Build System** | Cargo | (integrated) |
| **Virtual Environment** | venv | (configured) |

### Optional Dependencies (in venv)
The `operator/` venv includes additional packages for extended functionality:
- **Manim** — Mathematical animation visualization
- **Plotly** — Interactive data visualization
- **SciPy** — Scientific computing
- **NumPy** — Numerical computing
- **Pillow** — Image processing
- **PyDub** — Audio processing
- **Modern GL** — Graphics rendering
- And many more (full list in `operator/Lib/site-packages/`)

## 📐 Code Examples

### Python Frontend (Simplified)

```python
def run_rust_stream(self, op):
    target_val = self.get_target_for_op(op)
    cmd = [path_to_backend, str(target_val), "0.0"]
    for name, val in self.library.items():
        cmd.extend([name, str(val)])
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, ...)
    for line in process.stdout:
        if line.startswith("MILESTONE:"):
            # Parse and update UI
        elif line.startswith("FINAL:"):
            # Display result
```

### Rust Backend (Simplified)

```rust
fn eml(x: Complex64, y: Complex64) -> Complex64 {
    if y.norm() < 1e-9 { return Complex64::new(f64::NAN, f64::NAN); }
    x.exp() - y.ln()
}

while !found.load(Ordering::Relaxed) {
    let (a, b) = randomly_select_two_species();
    let result = eml(a.value, b.value);
    
    if (result - target).norm() < 1e-5 {
        println!("FINAL: eml({},{})", a.name, b.name);
        found.store(true, Ordering::SeqCst);
    }
}
```

## 🔬 Research Context

The paper referenced in `EML Operator.pdf` (arXiv identifier) describes the theoretical foundation for this evolutionary operator approach. The "phylogenetic" terminology stems from treating mathematical expression discovery as an evolutionary tree growth problem.

## 📋 Performance Notes

- **Parallelization:** Utilizes all available CPU cores for maximum throughput
- **Memory Efficiency:** Gene pool management with read-write locks eliminates memory contention
- **Streaming Updates:** Real-time stdout feedback provides responsive UI updates
- **Cross-platform Randomness:** Deterministic LCG-based RNG ensures reproducible searches

## 🛠️ Development

### Building the Rust Backend

```bash
cd backend
cargo build --release
```

The release binary is placed at `backend/target/release/backend.exe` (Windows) or `backend/target/release/backend` (Unix).

## 📚 References

The theoretical framework for this work is outlined in the referenced arXiv paper. The EML operator provides an interesting mechanism for evolutionary symbolic computation.

---

**Status:** Active development  
**Last Updated:** May 2026
