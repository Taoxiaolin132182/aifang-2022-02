import os

# 项目根目录
root_path = "C://Git2021"

def find_git(path):
    if os.path.isdir(path):
        dirs = os.listdir(path)
        for i in range(len(dirs)):
            current_dir = dirs[i]
            if current_dir == ".git":
                update_git_url(path + "/" + ".git")
                break

def update_git_url(path):
    file_name = path + "/" + "config"
    content = ""
    with open(file_name,'r') as fr:
        content = fr.read()
    content = content.replace("gmm01","aidolphin")

    with open(file_name,'w') as fw:
        fw.write(content)

root_dirs = os.listdir(root_path)

# print(root_dirs)

for i in range(len(root_dirs)):

    find_git(root_path + "/" + root_dirs[i])