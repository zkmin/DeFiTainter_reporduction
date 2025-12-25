# DeFiTainter 部署与使用指南

本仓库是 [DeFiTainter](https://github.com/kongqp/DeFiTainter) 的部署实现，基于 [Gigahorse Toolchain](https://github.com/nevillegrech/gigahorse-toolchain) 进行以太坊智能合约的反编译与污点分析。

## 重要说明

由于 `gigahorse-toolchain` 原仓库更新频繁且变动较大，直接替换可能会导致预编译内容过多而耗尽内存。请务必基于本仓库内的 `gigahorse-toolchain` 版本进行配置，**不要**直接拉取官方最新版。

------

## 1. 环境要求 (Prerequisites)

- **操作系统**: Ubuntu 24.04
- **内存**: **非常关键！**
  - 虚拟机内存 **最少 8GB**，否则编译时会卡死。
  - 建议配置越高越好（原论文实验环境为 512GB 内存）。
  - *如果物理内存不足，请参考下文“常见问题”中的 Swap 设置。*
- **Python**: 3.12
- **核心组件**:
  - `libboost-all-dev`
  - Souffle 2.3

------

## 2. 安装步骤 (Installation)

将仓库拉取到本地

`git clone https://github.com/kongqp/DeFiTainter`

### 2.1 基础依赖安装

进入项目根目录，安装系统级依赖：

```
sudo apt update
sudo apt install -y build-essential cmake flex bison libffi-dev libncurses5-dev \
libsqlite3-dev zlib1g-dev mcpp python3 python3-venv python3-pip libboost-all-dev
```

### 2.2 安装 Souffle 2.3

**注意**：必须安装 2.3 版本。

1. 进入 `gigahorse-toolchain` 目录并下载源码：

   ```
   cd gigahorse-toolchain
   wget https://github.com/souffle-lang/souffle/releases/download/2.3/souffle-2.3.tar.gz
   tar -zxvf souffle-2.3.tar.gz
   cd souffle-2.3
   ```

2. 编译并安装：

   ```
   sudo cmake --install build
   cmake -S . -B build -DCMAKE_CXX_COMPILER=/usr/bin/g++
   cmake --build build -- -j$(nproc)
   sudo cmake --install build
   ```

3. 验证安装：

   ```
   souffle --version
   ```

### 2.3 配置 Souffle-Addon

由于自带文件缺失，需要手动克隆指定版本的 `souffle-addon`。

1. 回到 `gigahorse-toolchain` 目录：

   ```
   # 确保在 gigahorse-toolchain 目录下
   git clone https://github.com/plast-lab/souffle-addon.git
   cd souffle-addon
   # 切换到兼容的特定 Commit
   git checkout 992145cd85da891dd28322cd16460f5e23e6dee4
   make
   ```

2. 配置环境变量：

   ```
   # 将路径修改为你实际的绝对路径 (/home/km/... 请按需修改)
   echo 'export LD_LIBRARY_PATH=/home/km/DeFiTainter/gigahorse-toolchain/souffle-addon:$LD_LIBRARY_PATH' >> ~/.bashrc
   echo 'export LIBRARY_PATH=/home/km/DeFiTainter/gigahorse-toolchain/souffle-addon:$LIBRARY_PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

### 2.4 验证 Gigahorse

在 `gigahorse-toolchain` 目录下运行测试：

```
./gigahorse.py examples/long_running.hex
```

- 反编译结果存放于 `.temp` 目录。
- 执行元数据存放于 `results.json`。

### 2.5 Python 环境配置

回到 `DeFiTainter` 根目录。由于 Ubuntu 24.04 限制 pip 直接安装，需使用虚拟环境：

```
cd ../ # 回到 DeFiTainter 根目录
python3 -m venv .venv
source .venv/bin/activate
# 在激活的环境中安装 requirements.txt (如果存在) 或手动安装缺少的包
# pip install web3 pandas ...
```

------

## 3. 配置修正 (Critical Fixes)

在运行前，**必须**执行以下代码和文件名的修正，否则无法运行：

1. 修复文件名空格问题：

   将 gigahorse-toolchain/clients/price_manipulation _analysis.dl 重命名为 price_manipulation_analysis.dl（去掉了中间的空格）。

2. 修复 Python 代码引用：

   修改 defi_tainter.py 第 73 行（根据重命名后的文件修改引用路径）。

3. 修复 Web3 函数名：

   在 defi_tainter.py 中，将过时的 toChecksumAddress 修改为新版 API to_checksum_address。

4. **创建合约存储目录**：

   ```
   mkdir -p /home/km/DeFiTainter/gigahorse-toolchain/contracts
   ```

5. 配置 RPC 节点：

   修改脚本中的区块链节点 URL（默认链接可能失效），需要替换为您自己在 Alchemy 或 Infura 注册的 API 链接。

6. 修复字节码截断错误 (关键 BUG)： 问题：原脚本默认假设 RPC 返回的字节码带 0x 前缀并执行 code[2:] 切片。当 RPC 返回不带前缀的纯 Hex 字符串时，该操作会错误删除指令首字节（如 0x60 PUSH1），导致合约代码无效。 解决：修改 defi_tainter.py 第 70 行左右的 download_bytecode 函数写入逻辑：
   ```
   # 原代码: f.write(code[2:])
   # 修改为 (更稳健的写法):
   if code.startswith("0x"):
     f.write(code[2:])
   else:
     f.write(code)
   ```
------

## 4. 运行指南 (Usage)

### 4.1 单次运行

使用 `defi_tainter.py` 进行单个合约分析：

```
python3 defi_tainter.py -bp <CHAIN_ID> -la <LOGIC_ADDR> -sa <STORAGE_ADDR> -fs <FUNC_SIG> -bn <BLOCK_NUM>
```

| **参数 Flag** | **全称**            | **含义**   | **描述**                                                     |
| ------------- | ------------------- | ---------- | ------------------------------------------------------------ |
| **-bp**       | Blockchain Platform | 区块链平台 | 如 ETH, BSC, Polygon 等。                                    |
| **-la**       | Logic Address       | 逻辑地址   | **关键**：在代理模式下，必须填写 Implementation 合约地址（实际代码所在）。 |
| **-sa**       | Storage Address     | 存储地址   | 在代理模式下，指 Proxy 合约地址（资金/状态所在）。           |
| **-fs**       | Function Signature  | 函数签名   | 目标函数的签名或哈希，如 `swap(uint256)`。                   |
| **-bn**       | Block Number        | 区块高度   | 分析的上下文区块高度，建议设为攻击发生前。                   |

### 4.2 批量运行

项目中包含 `dataset` 文件夹，内含 csv 格式的实验数据。可以使用 `runner.py` 脚本批量执行。

```
python3 runner.py
```

- **注意**：目前的 `runner.py` 默认仅配置了 ETH 的执行逻辑，如需运行其他链，请修改脚本代码。
- **首次运行**：速度较慢，因为需要编译 `.dl` 文件。

### 4.3 结果输出

分析完成后，元数据将写入 `results.json`，格式为三元组列表 `[filename, properties, flags]`：

- **properties**: 检测到的问题及非空 Datalog 输出关系。
- **flags**: 辅助信息（如 `ERROR`, `TIMEOUT`）。

------

## 5. 常见问题与解决方案 (Troubleshooting)

### Q1: 内存耗尽导致系统卡死/崩溃

现象：编译工具链消耗极大内存，8GB 物理内存通常不够。

解决：创建 Swap 分区（虚拟内存）。

```
# 1. 创建 8GB Swap 文件
sudo fallocate -l 8G /swapfile
# 2. 设置权限
sudo chmod 600 /swapfile
# 3. 格式化为 Swap
sudo mkswap /swapfile
# 4. 启用 Swap
sudo swapon /swapfile
# 5. 验证
free -h
```

*注：重启后失效。如需永久生效，请配置 `/etc/fstab`。*

### Q2: 分析结果始终为 False / Analytics_PublicFunction 为 0

现象：

运行 gigahorse.py 分析合约时，Analytics_PublicFunction 值为 0，表示未识别到公开函数，导致后续污点分析无法进行。

原因：

`defi_tainter.py` 在下载代码时错误截断了首字节（例如将 `PUSH1` 指令切除），导致保存的 `.hex` 文件变成无效代码。
* **验证方法**：对比 `cast code <地址>` 的输出与本地 `.hex` 文件，看是否缺失了开头的 `60` 或其他字节。

解决：

参考本文档“3. 配置修正”第 6 点，修改 `defi_tainter.py` 的写入逻辑。
