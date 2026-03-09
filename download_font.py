import os
import urllib.request
import sys

def download_font():
    # 1. 创建 fonts 目录
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
        print(f"Created directory: {font_dir}")
    
    # 2. 字体下载链接 (文泉驿微米黑，来自稳定源)
    # 使用 GitHub 镜像或者 SourceForge 的直链通常比较慢，这里使用一个常用的开源字体仓库直链
    # 备选：Google Fonts Noto Sans SC (通常是 OTF，Pygame 支持良好)
    # 这里选择 WenQuanYi Micro Hei，因为它通常是 TTC/TTF 格式，兼容性极佳
    
    font_url = "https://github.com/anthonyfok/fonts-wqy-microhei/raw/master/wqy-microhei.ttc"
    font_name = "wqy-microhei.ttc"
    save_path = os.path.join(font_dir, font_name)
    
    if os.path.exists(save_path):
        print(f"Font already exists at: {save_path}")
        return save_path

    print(f"Downloading {font_name} from {font_url}...")
    print("This might take a few seconds...")
    
    try:
        def report_hook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\rDownloading... {percent}%")
            sys.stdout.flush()

        urllib.request.urlretrieve(font_url, save_path, report_hook)
        print(f"\nSuccessfully downloaded font to: {save_path}")
        return save_path
    
    except Exception as e:
        print(f"\nError downloading font: {e}")
        # 备选方案：如果 GitHub 下载失败（可能是网络问题），提示用户
        print("建议：如果下载失败，请手动搜索 'wqy-microhei.ttc' 下载并放入 'fonts' 文件夹。")
        return None

if __name__ == "__main__":
    download_font()
