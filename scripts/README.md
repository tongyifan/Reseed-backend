# 一些小脚本的使用说明

## reseed.py
见[Wiki-使用说明#Python源码使用教程](https://github.com/tongyifan/Reseed-backend/wiki/%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E#python%E6%BA%90%E7%A0%81%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B)

## 6v.py
顾名思义，是下载六维种子的脚本。

1. 下载`6v.py`
2. 安装依赖`Requests`和`BeautifulSoup`
    ```bash
    pip3 install requests bs4
    ```
3. 修改源码开头的`COOKIES`和`DOWNLOAD_DIR`
4. 在`6v.py`同一目录创建一个文本文件`6v.txt`，将网页中生成的一系列种子链接复制进去并保存
5. 进入命令行，运行
    ```bash
    python3 6v.py
    ```
