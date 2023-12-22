import re
import solcx

import os, time
import tqdm
# path = r"C:\Users\yuanruifan\Desktop\testsrc"
path = r"H:\Shared\Smart_Contract_Source_Code"
# 识别solidity版本的模式
pattern = re.compile("^pragma\ssolidity\s(.*);")

def check_compiler()->bool:
    """
    测试，使用solcx.set_solc_version_pragma(方法是否有效
    """


def getSolidityVersion(filepath)->set:
    """
    获取合约文件中指定的编译器版本，注意： 多数文件只有一个版本申明，有一些有两个，甚至多个申明； 有的甚至没有申明
    :param filepath:
    :return:
    """
    solidity_version_set = set()
    with open(filepath,"r",encoding="utf-8") as f:
        for line in f.readlines():
            # 用正则表达式匹配solidity的版本
            match_result = pattern.match(line)
            if match_result:
                # solidity_version_set.add(match_result.group(1).split(";")[0])
                solidity_version_set.add(match_result.group(1))
                # print("%s-->%s"%(os.path.split(file)[1],match_result.group(1)))
    return solidity_version_set

# for root, dirs, files in os.walk(path):
#     for file in files:
#         # print("Index: %d"%index)
#         if file.endswith("txt") or file.endswith("sol"):
#             resutls = getSolidityVersion(os.path.join(root,file))
#             print("file: %s, len: %s"%(file,len(resutls)))


# index =1
with open("test.csv","w") as outs:
    for root, dirs, files in os.walk(path):
        for file in files:
            # print("Index: %d"%index)
            if file.endswith("txt") or file.endswith("sol"):
              resutls = getSolidityVersion(os.path.join(root,file))
              if len("".join(resutls)) >100:
                outs.write(file+","+";".join(resutls)+"\n")
            # index = index +1



print("OK!!!!!")