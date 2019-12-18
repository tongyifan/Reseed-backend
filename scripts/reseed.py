import json
import os
import re

import click


def walk_dir(root_path):
    result = {}
    for file in os.listdir(root_path):
        print("正在索引：{}".format(file))
        path = os.sep.join([root_path, file])
        if os.path.isfile(path):
            try:
                result[file] = os.path.getsize(path)
            except FileNotFoundError:
                print("文件[{}]存在但读取时出现错误，本次索引可能不完整，请检查此文件详情后重试~".format(path))
                continue
        else:
            per_torrent = {}
            for root, dirs, file_list in os.walk(path):
                for filename in file_list:
                    apath = os.sep.join([root, filename])  # 合并成一个完整路径
                    try:
                        alength = os.path.getsize(apath)
                    except FileNotFoundError:
                        print("文件[{}]存在但读取时出现错误，本次索引可能不完整，请检查此文件详情后重试~".format(apath))
                        continue
                    per_torrent[apath.replace(path + os.sep, '')] = alength
            result[file] = per_torrent
    return {'base_dir': root_path, 'result': result}


@click.command()
@click.argument('path')
@click.option('--save-dir', default=os.getcwd(), help='索引文件保存的路径，默认为当前文件夹')
def main(path, save_dir):
    """
    PATH: 需要索引的路径，举例：/home/xxx/downloads/, D:\\\\Downloads
    """
    if not os.access(save_dir, os.W_OK):
        print("保存路径[{}]不可写入，请提升权限或更改目录！".format(save_dir))
        return
    elif not os.access(path, os.R_OK):
        print("索引路径[{}]不可读取，请检查路径是否正确！".format(path))
        return
    else:
        print("开始索引，时间根据路径下文件零散程度不等，请耐心等待...")

    result = walk_dir(path)

    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    path = re.sub(rstr, "_", path)  # 替换为下划线
    result_file = '{}.json'.format(os.path.join(save_dir, path))
    with open(result_file, 'w')as f:
        f.write(json.dumps(result))
    print("成功！保存路径：{}".format(result_file))


if __name__ == '__main__':
    main()
