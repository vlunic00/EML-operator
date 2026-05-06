import tkinter as tk
import subprocess
import threading
import os
import platform
import numpy as np

class EMLStreamingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EML Phylogenetic Real-Time Engine")
        self.root.geometry("1000x650")
        self.root.configure(bg="#0a0a0a")

        self.test_x, self.test_y = 0.577215, 1.282427
        self.library = {"1": 1.0, "x": self.test_x, "y": self.test_y}
        self.setup_ui()

    def setup_ui(self):
        # (Standard layout as before)
        content = tk.Frame(self.root, bg="#0a0a0a")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(content, text="EML LIVE EVOLUTION", fg="white", bg="#0a0a0a", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.formula_var = tk.StringVar(value="Waiting...")
        tk.Label(content, textvariable=self.formula_var, fg="#00FF00", bg="#111", font=("Consolas", 11), height=10, wraplength=450, justify=tk.LEFT).pack(pady=20, fill=tk.X)

        btn_frame = tk.Frame(content, bg="#0a0a0a")
        btn_frame.pack()
        for op in ["+", "-", "*", "/", "ln(x)"]:
            tk.Button(btn_frame, text=f"EVOLVE {op}", command=lambda o=op: self.start_search(o),
                      bg="#333", fg="white", width=10).pack(side=tk.LEFT, padx=5)

        side = tk.Frame(self.root, bg="#111", width=300)
        side.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(side, text="PHYLOGENETIC LIBRARY", fg="#555", bg="#111").pack(pady=10)
        self.lib_list = tk.Listbox(side, bg="#111", fg="#00FF00", borderwidth=0, font=("Consolas", 9))
        self.lib_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.update_sidebar()

    def update_sidebar(self):
        self.lib_list.delete(0, tk.END)
        for k in self.library: self.lib_list.insert(tk.END, f" ✔ {k}")

    def start_search(self, target_op):
        threading.Thread(target=self.run_rust_stream, args=(target_op,), daemon=True).start()

    def get_target_for_op(self, op):
    # This matches the label to the math Rust needs to solve
        vals = {
            "+": self.test_x + self.test_y, 
            "-": self.test_x - self.test_y, 
            "*": self.test_x * self.test_y, 
            "/": self.test_x / self.test_y,
            "ln(x)": np.log(self.test_x)
        }
        return vals.get(op, 0.0)

    def run_rust_stream(self, op):
        # 1. Be very specific about the folder structure
        # Change 'backend' to whatever your Rust project folder is named
        base_path = os.path.dirname(os.path.abspath(__file__))
        rust_project_dir = os.path.join(base_path, "backend") 
        
        binary = "backend.exe" if os.name == "nt" else "backend"
        path = os.path.join(rust_project_dir, "target", "release", binary)
        
        if not os.path.exists(path):
            # This will tell us exactly where Python is looking
            print(f"DEBUG: Python is looking for the exe here: {path}")
            self.formula_var.set("Error: Rust binary not found.\nCheck console for path.")
            return

        target_val = self.get_target_for_op(op)
        cmd = [path, str(target_val), "0.0"]
        for name, val in self.library.items():
            cmd.extend([name, str(val)])

        # 2. Launch with 'cwd' so Rust can find its own files if needed
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            cwd=rust_project_dir # Sets the environment to the Rust folder
        )

        # 2. Read the output in real-time
        def stream_reader():
            try:
                # This loop runs as long as Rust is printing
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if not line: continue
                    
                    print(f"Python caught: {line}") # Debug to your console

                    if line.startswith("MILESTONE:"):
                        # MILESTONE:e = eml(x,y) -> name: e, formula: eml(x,y)
                        _, data = line.split(":", 1)
                        name, formula = data.split("=", 1)
                        
                        # Update GUI using .after() to avoid thread crashes
                        self.root.after(0, lambda n=name.strip(), f=formula.strip(): 
                                    self.update_ui_with_milestone(n, f))

                    elif line.startswith("FINAL:"):
                        formula = line.split(":", 1)[1].strip()
                        self.root.after(0, lambda f=formula: 
                                    self.formula_var.set(f"FOUND {op}:\n{f}"))
                        break # Stop reading after the final result
            finally:
                process.terminate()

        # 3. Start the reader thread so the GUI stays responsive
        threading.Thread(target=stream_reader, daemon=True).start()

    def update_ui_with_milestone(self, name, formula):
        """Helper to update the sidebar and status label"""
        if name not in self.library:
            self.library[name] = formula # Or calculate the actual value if needed
            self.update_sidebar()
        self.formula_var.set(f"New Milestone: {name}\n{formula}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EMLStreamingApp(root)
    root.mainloop()