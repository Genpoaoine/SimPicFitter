# SimPicFitter 🖼️

**SimPicFitter** 是一个基于 Python 的桌面应用程序，旨在帮助用户快速从海量图片库（支持 20,000+ 图片）中识别并自动归类相似或重复的照片。

**SimPicFitter** is a Python-based desktop application designed to help users quickly identify and automatically categorize similar or duplicate photos from large image libraries (supporting over 20,000 images).

---

<div id="english"></div>

## 🌟 Features

- **High Performance**: Optimized with **LSH (Locality Sensitive Hashing)**. It breaks down $O(N^2)$ complexity, making it possible to process tens of thousands of images in minutes rather than hours.
- **pHash Algorithm**: Uses Perceptual Hashing to detect images that have been resized, compressed, or slightly edited.
- **User Friendly**: A clean Tkinter-based GUI for folder selection and sensitivity adjustment.
- **Smart ETA**: Real-time progress tracking with estimated time of arrival (ETA) prediction.
- **Safe Output**: Automatically creates an `Optimized_Similar_Images` folder within your source directory and **copies** (instead of moves) similar images into groups.

## 🛠️ Tech Stack

- **Language**: Python 3.x
- **Core Libs**: `ImageHash`, `Pillow`, `NumPy`
- **GUI**: `Tkinter`
- **Threading**: Background processing to keep the UI responsive.

## 🚀 Getting Started

### Prerequisites

Make sure you have Python installed, then install the dependencies:

```bash
pip install imagehash Pillow numpy
```
