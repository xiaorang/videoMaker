# 文件管理
import os
import chardet

# 改变扩展名
def changeExt(aFile, aExt):
    return getPureName(aFile)+ aExt
# 无路径的文件名
def getFileName(aFile):
    return os.path.basename(aFile)
# 无后缀的纯文件名
def getPureName(aFile):
    return os.path.splitext(aFile)[0]
# 不带点的扩展名
def getPureExt(aFile):
    return os.path.splitext(aFile)[-1][1:]
# 无路径且无后缀的文件名
def getPureFileName(aFile):
    return getPureName(getFileName(aFile))
# 读取文件内容，自动编码匹配
def getFileText(aFileName):
    with open(aFileName, 'rb') as f:
        cur_encoding = chardet.detect(f.read())['encoding']
        # print (cur_encoding) #当前文件编码

    objId= getPureFileName(aFileName)
    with open(aFileName, encoding=cur_encoding) as f:
        str= f.read()
    return str
# 读取列表
def readObj(aFileName):
    with open(aFileName, 'r') as f:
        return eval(f.read())
# 保存文件
def saveObj(aObj, aFileName):
    with open(aFileName, 'w') as f:
        f.write(str(aObj))
# 逐行读取文件内容，并调用处理过程，自动编码匹配
def readFileLine(aFileName, doReadLine):
    with open(aFileName, 'rb') as f:
        cur_encoding = chardet.detect(f.read())['encoding']
        # print (cur_encoding) #当前文件编码

    objId= getPureFileName(aFileName)
    with open(aFileName, encoding=cur_encoding) as f:
        line= f.readline()
        while line:
            doReadLine(line)
            line= f.readline()
def getFileList(aPath, aExt):
    file_names = os.listdir(aPath)
    file_list = [os.path.join(aPath, file) for file in file_names]
    if aExt!='':
        file_list = filter(lambda x: x.endswith(aExt), file_list)
    return file_list

def getFileListSub(rootDir, aExt):
    file_list=[]
    def searchPath(aPath):
        nonlocal file_list
        for root, dirs, files in os.walk(aPath):       # 分别代表根目录、文件夹、文件
            for file in files:                         # 遍历文件
                file_path = os.path.join(root, file)   # 获取文件绝对路径  
                file_list.append(file_path)            # 将文件路径添加进列表
            # for dir in dirs:                           # 遍历目录下的子目录
                # dir_path = os.path.join(root, dir)     # 获取子目录路径
                # searchPath(dir_path)                   # 递归调用
    searchPath(rootDir)
    file_list = filter(lambda x: x.endswith(aExt), file_list)
    return file_list
# 清空目录
def clearDir(aPath):
    lst= getFileList(aPath, '')
    for f1 in lst:
        os.remove(f1)
# 清空目录及所有子目录（子目录不删除）
def clearTree(aPath):
    lst= getFileListSub(aPath, '')
    for f1 in lst:
        os.remove(f1)
# 获得子目录，如果不存在则创建
def makeSubPath(base, sub):
    ret= os.path.join(base, sub)
    if not os.path.exists(ret):
        os.makedirs(ret)
    return ret

if __name__=='__main__':
    clearDir(r'D:\2020综合\Now\视频制作\frame')
