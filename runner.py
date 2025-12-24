import csv
import subprocess
import os
import sys

# 配置文件名和工具脚本
CSV_FILE = 'dataset/incident.csv'
TOOL_SCRIPT = './defi_tainter.py'
PYTHON_EXEC = sys.executable

def run_analysis():
    # 检查 CSV 文件是否存在
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        return

    # 检查 defi_tainter.py 是否存在
    if not os.path.exists(TOOL_SCRIPT):
        print(f"Error: {TOOL_SCRIPT} not found.")
        return

    print(f"Starting ETH-ONLY batch analysis from {CSV_FILE}...\n")

    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        count_run = 0
        count_skip = 0
        
        for row in reader:
            # 获取各列数据，并去除前后空格
            project = row.get('expolited_project', 'Unknown').strip()
            logic_addr = row['logic_addr'].strip()
            storage_addr = row['storage_addr'].strip()
            func_sign = row['func_sign'].strip()
            platform = row['platform'].strip()
            block_num = row['block_number'].strip()

            # --- 核心修改：筛选条件 ---
            if platform.upper() != 'ETH':
                # 如果不是 ETH，打印跳过信息并继续下一循环
                # print(f"[Skipping] {project} ({platform})") 
                count_skip += 1
                continue
            # -----------------------

            count_run += 1
            print("=" * 60)
            print(f"Running #{count_run}: {project}")
            print(f"  Platform: {platform} | Block: {block_num}")
            print(f"  Logic   : {logic_addr}")
            print(f"  Storage : {storage_addr}")
            print(f"  FuncSig : {func_sign}")
            print("-" * 60)

            # 构建命令
            cmd = [
                PYTHON_EXEC,
                TOOL_SCRIPT,
                '-bp', platform,
                '-la', logic_addr,
                '-sa', storage_addr,
                '-fs', func_sign,
                '-bn', block_num
            ]

            try:
                # 执行命令
                subprocess.run(cmd, check=False)
            except KeyboardInterrupt:
                print("\nBatch analysis interrupted by user.")
                sys.exit(0)
            except Exception as e:
                print(f"Error executing command: {e}")
            
            print("\n")

    print("=" * 60)
    print(f"Batch analysis completed.")
    print(f"Total ETH Contracts Analyzed: {count_run}")
    print(f"Total Non-ETH Contracts Skipped: {count_skip}")

if __name__ == "__main__":
    run_analysis()