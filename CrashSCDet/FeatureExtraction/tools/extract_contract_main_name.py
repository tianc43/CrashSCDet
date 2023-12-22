from bs4 import BeautifulSoup
import os, time


exist_set = set()
all_set = set()

print("读取所有的合约记录")

for root,dirs,files in os.walk(r"H:\Shared\Smart_Contract_Source_Code"):
    for file in files:
        if file.endswith("txt"):
            all_set.add(os.path.splitext(file)[0].strip())

print("所有合约文件名称读取完毕，共计%d" % (len(all_set)))


print("读取已经标记的合约")

with open(r"H:\Shared\MyWorkingComputer\FeatureExtraction\tools\ContractMainFile.csv","r") as f:
    for line in f.readlines():
        exist_set.add(line.split(",")[0].strip())
print("已经统计好了的合约，共计%d" % (len(exist_set)))

print("Diff= %s" % (len(all_set) - len(exist_set)))

differnce_set = all_set.difference(exist_set)


def getMainName(path:str, f):
    soup= BeautifulSoup(open(path,"r",encoding="utf-8"), 'html.parser')
    divscope= soup.find(name="div", id="ContentPlaceHolder1_contractCodeDiv")
    # 找到第一个span， 里面的内容就是main name
    main_name= divscope.find(name="span", class_="h6 font-weight-bold mb-0").string
    # print("contract_addr:%s, contract_main_name: %s" % (os.path.split(path)[1].split("-")[0], main_name))
    f.write(os.path.split(path)[1].split("-")[0]+","+main_name+'\n')


# contract_addr =r"0xa2c4e011ef42a4eb5dc931a88797560bcb83aefe"
# path = r"H:\Shared\ContractTrans\ContractTrans\{contract_addr}\{contract_addr}-Main.html".format(
#         contract_addr=contract_addr)


# 遍历所有没找到main name 的合约集合

for contract_addr in differnce_set:
    with open("main_difference.csv", "w") as f:
        path = r"H:\Shared\ContractTrans\ContractTrans\{contract_addr}\{contract_addr}-Main.html".format(
                contract_addr=contract_addr)
        getMainName(path,f)


# for root, dirs, files in os.walk(r"H:\Shared\ContractTrans\ContractTrans"):
#     for file in files:
#         if file.endswith("Main.html"):
#             fullpath= os.path.join(root,file)
#             time.sleep(1)
#             print("Running%s"%file)
#             getMainName(fullpath)
#
