import os
import re
import shutil
import time


def process_images():
    # 硬编码Windows文件夹位置（请修改为你的实际路径）
    source_directory = r"E:\pixiv"  # 替换为你的实际路径

    print(f"[{time.strftime('%H:%M:%S')}] 开始处理目录: {source_directory}")

    # 验证源目录是否存在
    if not os.path.isdir(source_directory):
        print(f"[{time.strftime('%H:%M:%S')}] 错误: 目录 '{source_directory}' 不存在或不可访问!")
        return

    # 创建目标子文件夹（在源目录下）
    variant_folder = os.path.join(source_directory, "variant_files")
    master_folder = os.path.join(source_directory, "master_files")
    timestamp_folder = os.path.join(source_directory, "timestamp_files")

    os.makedirs(variant_folder, exist_ok=True)
    os.makedirs(master_folder, exist_ok=True)
    os.makedirs(timestamp_folder, exist_ok=True)

    print(f"[{time.strftime('%H:%M:%S')}] 创建文件夹:")
    print(f"  - {variant_folder}")
    print(f"  - {master_folder}")
    print(f"  - {timestamp_folder}")

    # 获取源目录下所有文件
    try:
        files = [
            f for f in os.listdir(source_directory)
            if os.path.isfile(os.path.join(source_directory, f))
        ]
        print(f"[{time.strftime('%H:%M:%S')}] 找到 {len(files)} 个文件")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 错误: 读取目录失败 - {str(e)}")
        return

    # 处理每个文件
    processed_count = 0
    for filename in files:
        file_path = os.path.join(source_directory, filename)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        # 1. 处理第一种文件：含 _p0/_p1/_p2...
        if re.search(r"_p\d+$", name):
            dst_path = os.path.join(variant_folder, filename)
            try:
                shutil.move(file_path, dst_path)
                print(f"[{time.strftime('%H:%M:%S')}] ✓ 移动变体文件: {filename} -> variant_files/")
                processed_count += 1
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ 移动失败: {filename} - {str(e)}")

        # 2. 处理第二种文件：含 _master1200
        elif "_master1200" in name:
            new_name = name.replace("_master1200", "") + ext
            dst_path = os.path.join(master_folder, new_name)
            try:
                shutil.move(file_path, dst_path)
                print(f"[{time.strftime('%H:%M:%S')}] ✓ 移动主图文件: {filename} -> master_files/{new_name}")
                processed_count += 1
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ 移动失败: {filename} - {str(e)}")

        # 3. 处理第三种文件：含时间戳
        elif re.search(r"_\d{8}_\d{6}$", name) or re.search(r"\d{8}_\d{6}", name):
            # 提取ID
            id_match = re.search(r"(\d+)(?=_\d{8}_\d{6})", name)
            if not id_match:
                id_match = re.search(r"(\d{6,})", name)
            img_id = id_match.group(1) if id_match else "unknown"

            # 生成唯一新文件名
            counter = 0
            while True:
                new_name = f"{img_id}_p{counter}{ext}"
                dest_path = os.path.join(timestamp_folder, new_name)
                if not os.path.exists(dest_path):
                    break
                counter += 1

            # 移动并重命名
            try:
                shutil.move(file_path, dest_path)
                print(f"[{time.strftime('%H:%M:%S')}] ✓ 移动时间戳文件: {filename} -> timestamp_files/{new_name}")
                processed_count += 1
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ 移动失败: {filename} - {str(e)}")

        # 其他文件（不处理）
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠ 跳过未识别文件: {filename}")

    # 处理完成统计
    print(f"\n[{time.strftime('%H:%M:%S')}] 处理完成!")
    print(f"共处理 {processed_count} 个文件")
    print(f"文件已分类到以下文件夹:")
    print(f"  - 变体文件: {variant_folder}")
    print(f"  - 主图文件: {master_folder}")
    print(f"  - 时间戳文件: {timestamp_folder}")


if __name__ == "__main__":
    print("=" * 50)
    print("图片文件整理工具")
    print("=" * 50)
    process_images()
    print("=" * 50)
    input("按Enter键退出...")  # 防止窗口立即关闭