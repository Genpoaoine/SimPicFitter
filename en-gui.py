import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import imagehash
from PIL import Image
from collections import defaultdict
import itertools
import shutil


class SimilarityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SimPicFitter - Image Similarity Scanner")  # Translated title
        self.root.geometry("620x450")

        self.folder_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Waiting for folder selection...")  # Translated status
        self.progress_val = tk.DoubleVar(value=0)
        self.eta_var = tk.StringVar(value="Estimated remaining time: --:--")  # Translated ETA

        # --- UI ---
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="1. Select the folder to scan:").pack(anchor="w")  # Translated label
        path_frame = tk.Frame(main_frame)
        path_frame.pack(fill="x", pady=5)
        tk.Entry(path_frame, textvariable=self.folder_path, state="readonly").pack(side="left", expand=True, fill="x")
        tk.Button(path_frame, text="Select Folder", command=self.select_folder).pack(side="right", padx=5)  # Translated button

        tk.Label(main_frame, text="2. Similarity sensitivity (lower threshold is stricter):").pack(anchor="w", pady=(10, 0))  # Translated label
        self.threshold_scale = tk.Scale(main_frame, from_=0, to_=20, orient="horizontal")
        self.threshold_scale.set(5)
        self.threshold_scale.pack(fill="x", pady=5)

        self.pb = ttk.Progressbar(main_frame, variable=self.progress_val, maximum=100)
        self.pb.pack(fill="x", pady=20)

        tk.Label(main_frame, textvariable=self.status_var, fg="blue", wraplength=550).pack()
        tk.Label(main_frame, textvariable=self.eta_var, font=("Microsoft YaHei", 10, "bold")).pack(pady=5)

        self.start_btn = tk.Button(main_frame, text="🚀 Start Analysis",  # Translated button text
                                   command=self.start_task_thread, bg="#4CAF50", fg="white", height=2)
        self.start_btn.pack(fill="x", pady=10)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)
            self.status_var.set(f"Pending: {path}")  # Translated status

    def format_time(self, seconds):
        if seconds < 0: return "Calculating..."
        mins, secs = divmod(int(seconds), 60)
        hrs, mins = divmod(mins, 60)
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    def start_task_thread(self):
        path = self.folder_path.get()
        if not path:
            messagebox.showwarning("Notice", "Please select a folder first")  # Translated message
            return
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.process_logic, args=(path,), daemon=True).start()

    def process_logic(self, folder_path):
        try:
            threshold = self.threshold_scale.get()
            exts = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(exts)]
            total = len(files)

            if total == 0:
                messagebox.showwarning("Notice", "No image files found in this folder")  # Translated message
                return

            # Step 1: Calculate hashes
            image_hashes = {}
            start_t = time.time()
            for i, p in enumerate(files):
                try:
                    with Image.open(p) as img:
                        image_hashes[p] = imagehash.phash(img.convert('RGB'), hash_size=8)
                except:
                    continue

                if (i + 1) % 20 == 0 or (i + 1) == total:
                    elapsed = time.time() - start_t
                    percent = ((i + 1) / total) * 100
                    eta = (elapsed / (i + 1)) * (total - (i + 1))
                    self.progress_val.set(percent)
                    self.status_var.set(f"Extracting fingerprints: {i + 1}/{total}")  # Translated status
                    self.eta_var.set(f"Hash ETA: {self.format_time(eta)}")  # Translated ETA
                    self.root.update_idletasks()

            # Step 2: Fast matching (LSH)
            self.status_var.set("Performing similarity matching via LSH algorithm...")  # Translated status
            hash_groups = defaultdict(list)
            for p, h in image_hashes.items():
                arr = h.hash.flatten()
                for k in range(4):  # Split 64 bits into 4 blocks
                    block = "".join(['1' if x else '0' for x in arr[k * 16:(k + 1) * 16]])
                    hash_groups[f"{k}_{block}"].append(p)

            similarity_map = defaultdict(set)
            compared = set()
            for candidates in hash_groups.values():
                if len(candidates) < 2: continue
                for p1, p2 in itertools.combinations(candidates, 2):
                    pair = tuple(sorted((p1, p2)))
                    if pair not in compared:
                        if image_hashes[p1] - image_hashes[p2] <= threshold:
                            similarity_map[p1].add(p2)
                            similarity_map[p2].add(p1)
                        compared.add(pair)

            # Step 3: Merge groups and save
            groups = self.merge_groups(similarity_map)
            if groups:
                self.status_var.set(f"Found {len(groups)} groups of similar images, separating files...")  # Translated status
                final_path = self.save_files(groups, folder_path)
                messagebox.showinfo("Completed", f"Processing successful!\nResult folder:\n{final_path}")  # Translated message
            else:
                messagebox.showinfo("End", "No similar images meeting the criteria were found.")  # Translated message

        except Exception as e:
            messagebox.showerror("Runtime Error", str(e))  # Translated message
        finally:
            self.start_btn.config(state="normal")
            self.progress_val.set(0)
            self.eta_var.set("Estimated remaining time: --:--")  # Translated ETA

    def merge_groups(self, sim_map):
        processed = set()
        final = []
        for f in sim_map:
            if f not in processed:
                g = set()
                q = [f]
                while q:
                    curr = q.pop()
                    if curr not in g:
                        g.add(curr)
                        processed.add(curr)
                        q.extend(sim_map[curr] - g)
                if len(g) > 1: final.append(list(g))
        return final

    def save_files(self, groups, base_path):
        # Create result folder directly in selected directory
        out_dir = os.path.join(base_path, "Optimized_Similar_Images")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        for i, group in enumerate(groups):
            sub_dir = os.path.join(out_dir, f"Group_{i + 1}")
            os.makedirs(sub_dir, exist_ok=True)
            for p in group:
                try:
                    shutil.copy2(p, os.path.join(sub_dir, os.path.basename(p)))
                except:
                    pass
        return out_dir


if __name__ == "__main__":
    rt = tk.Tk()
    SimilarityApp(rt)
    rt.mainloop()