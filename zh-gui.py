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
        self.root.title("SimPicFitter-图片相似度查杀")
        self.root.geometry("620x450")

        self.folder_path = tk.StringVar()
        self.status_var = tk.StringVar(value="等待选择文件夹...")
        self.progress_val = tk.DoubleVar(value=0)
        self.eta_var = tk.StringVar(value="预计剩余时间: --:--")

        # --- UI ---
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="1. 选择要扫描的文件夹:").pack(anchor="w")
        path_frame = tk.Frame(main_frame)
        path_frame.pack(fill="x", pady=5)
        tk.Entry(path_frame, textvariable=self.folder_path, state="readonly").pack(side="left", expand=True, fill="x")
        tk.Button(path_frame, text="选择文件夹", command=self.select_folder).pack(side="right", padx=5)

        tk.Label(main_frame, text="2. 相似度灵敏度 (阈值越小越严格):").pack(anchor="w", pady=(10, 0))
        self.threshold_scale = tk.Scale(main_frame, from_=0, to_=20, orient="horizontal")
        self.threshold_scale.set(5)
        self.threshold_scale.pack(fill="x", pady=5)

        self.pb = ttk.Progressbar(main_frame, variable=self.progress_val, maximum=100)
        self.pb.pack(fill="x", pady=20)

        tk.Label(main_frame, textvariable=self.status_var, fg="blue", wraplength=550).pack()
        tk.Label(main_frame, textvariable=self.eta_var, font=("Microsoft YaHei", 10, "bold")).pack(pady=5)

        self.start_btn = tk.Button(main_frame, text="🚀 开始执行分析",
                                   command=self.start_task_thread, bg="#4CAF50", fg="white", height=2)
        self.start_btn.pack(fill="x", pady=10)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)
            self.status_var.set(f"待处理: {path}")

    def format_time(self, seconds):
        if seconds < 0: return "计算中..."
        mins, secs = divmod(int(seconds), 60)
        hrs, mins = divmod(mins, 60)
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    def start_task_thread(self):
        path = self.folder_path.get()
        if not path:
            messagebox.showwarning("提示", "请先选择文件夹")
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
                messagebox.showwarning("提示", "该文件夹下没发现图片文件")
                return

            # 第一步：计算哈希
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
                    self.status_var.set(f"正在提取指纹: {i + 1} / {total}")
                    self.eta_var.set(f"哈希预计剩余: {self.format_time(eta)}")
                    self.root.update_idletasks()

            # 第二步：快速匹配 (LSH)
            self.status_var.set("正在通过 LSH 算法进行相似性匹配...")
            hash_groups = defaultdict(list)
            for p, h in image_hashes.items():
                arr = h.hash.flatten()
                for k in range(4):  # 64位切成4块
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

            # 第三步：合并分组并保存
            groups = self.merge_groups(similarity_map)
            if groups:
                self.status_var.set(f"发现 {len(groups)} 组相似图，正在分离文件...")
                final_path = self.save_files(groups, folder_path)
                messagebox.showinfo("完成", f"处理成功！\n结果文件夹：\n{final_path}")
            else:
                messagebox.showinfo("结束", "未发现符合条件的相似图片。")

        except Exception as e:
            messagebox.showerror("运行报错", str(e))
        finally:
            self.start_btn.config(state="normal")
            self.progress_val.set(0)
            self.eta_var.set("预计剩余时间: --:--")

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
        # 结果文件夹直接创建在所选目录下
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