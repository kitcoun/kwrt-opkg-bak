import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime

# 定义要跳过的目录列表
SKIP_DIRECTORIES = ["firmware","Parent directory",'luci', 'packages', 'base',"routing","telephony"]

# 定义需要特殊处理的文件后缀
SPECIAL_EXTENSIONS = ['.bin', '.trx', '.img']

def get_first_folder_name(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', id='list')
    if table:
        rows = table.find('tbody').find_all('tr')
        if len(rows) >= 2:
            second_row = rows[1]
            link = second_row.find('a')
            if link:
                name = link.text.split('-', 1)[-1].rstrip('/') if '-' in link.text else link.text
                return name
    return "openwrt_firmware"  # 默认文件夹名称

def get_firmware_info(url):
    # 获取网页内容并解析
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 查找指定的表格内容
    table = soup.find('table', id='list')
    if not table:
        return []
    
    firmware_info = []
    for row in table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        if len(columns) >= 3:
            link = columns[0].find_all('a')[0]
            if link:
                name = link.text.rstrip('/')
                href = link['href']
                date = columns[2].text.strip()
                # 检查是否为要跳过的目录
                if name not in SKIP_DIRECTORIES:
                    firmware_info.append({'name': name, 'href': href, 'date': date})
    
    return firmware_info

def download_file(url, path):
    # 下载文件的函数
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except Exception as e:
        print(f"下载文件 {url} 时出错: {str(e)}")
        return False

def update_firmware(base_url, save_dir):
    firmware_info = get_firmware_info(base_url)
    
    for item in firmware_info:
        full_url = base_url + item['href']
        if full_url.endswith('/'):
            # 如果是目录,递归调用
            sub_dir = os.path.join(save_dir, item['name'])
            os.makedirs(sub_dir, exist_ok=True)
            update_firmware(full_url, sub_dir)
        else:
            # 如果是文件,下载或更新
            file_name, file_ext = os.path.splitext(item['href'])
            
            # # 检查是否为特定后缀
            # if file_ext.lower() in SPECIAL_EXTENSIONS:
            #     new_file_name = f"{file_name}-{item['date']}{file_ext}"
            # else:
            #     new_file_name = file_name
            
            file_path = os.path.join(save_dir, item['href'])
            # new_file_path = os.path.join(save_dir, new_file_name)
            new_file_path = os.path.join(save_dir, file_name)
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            
            # # 检查文件是否存在及日期是否一致
            # existing_date = get_existing_file_date(save_dir, item['href'])
            # if existing_date == item['date']:
            #     print(f"文件 {item['href']} 已存在且日期一致,跳过")
            #     continue
            # else:
            #     # 文件名称一致但日期不一致,根据后缀决定是否重命名
            #     if file_ext.lower() in SPECIAL_EXTENSIONS:
            #         if os.path.exists(file_path):
            #             os.rename(file_path, new_file_path)
            #         print(f"文件 {item['href']} 日期不一致,已重命名为 {new_file_name}")
            #     else:
            #         print(f"文件 {item['href']} 日期不一致,准备更新")
                    
            # 下载文件
            max_retries = 3
            for attempt in range(max_retries):
                if download_file(full_url, new_file_path+file_ext):
                    # print(f"成功下载文件: {new_file_name}")
                    print(f"成功下载文件: {file_name}")
                    break
                else:
                    print(f"尝试 {attempt + 1}/{max_retries} 失败,等待后重试...")
                    time.sleep(10)
            else:
                print(f"下载 {full_url} 失败,已达到最大重试次数")
                continue
            
            # # 更新文件信息
            # update_file_info(save_dir, file_name, item['date'])

# def get_existing_file_date(save_dir, file_name):
#     info_file = os.path.join(save_dir, 'file_info.txt')
#     if os.path.exists(info_file):
#         with open(info_file, 'r') as f:
#             for line in f:
#                 if line.startswith(file_name):
#                     return line.split()[-1]
#     return None

# def update_file_info(save_dir, file_name, date):
#     info_file = os.path.join(save_dir, 'file_info.txt')
    
#     # 读取现有文件内容
#     existing_lines = []
#     if os.path.exists(info_file):
#         with open(info_file, 'r') as f:
#             existing_lines = f.readlines()

#     # 查找并更新或添加文件信息
#     updated = False
#     for i, line in enumerate(existing_lines):
#         if line.startswith(file_name):
#             existing_lines[i] = f"{file_name} {date}\n"
#             updated = True
#             break

#     if not updated:
#         existing_lines.append(f"{file_name} {date}\n")

#     # 写入更新后的内容
#     with open(info_file, 'w') as f:
#         f.writelines(existing_lines)

#     print(f"已更新文件信息: {file_name} {date}")


if __name__ == "__main__":
    base_url = "https://dl.openwrt.ai/"
    first_folder_name = get_first_folder_name(base_url)
    save_dir = os.path.join(os.getcwd(), first_folder_name)
    update_firmware(base_url, save_dir)
