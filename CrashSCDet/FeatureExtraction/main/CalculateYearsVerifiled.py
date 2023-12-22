import pandas as pd
from collections import Counter
import re
# 该文件从宏观上统计所有合约文件的情况

data = pd.read_csv("./results-all-remove-zero-transaction.csv")
print(data.shape)

files = data.shape[0]
# 输出总共又多少个文件
print("总共有 %s 个文件"%(data.shape[0]))

# 输出总有有多少个合约
print("总共有 %s 个 contract, 每个文件平均: %.2f"%(data['CountContract'].sum(), data['CountContract'].sum()/files))


# 输出总有有多少个库
print("总共有 %s 个 library, 每个文件平均: %.2f "%(data['NOL'].sum(),data['NOL'].sum()/files ))


#输出总共有多少个接口
print("总共有 %s 个 interface, 每个文件平均: %.2f "%(data['NOI'].sum(),data['NOI'].sum()/files))


# NOE 输出总共有多少个event
print("总共有 %s 个events, 每个文件平均: %.2f"%(data['NOE'].sum(),data['NOE'].sum()/files))

# 输出总共有多少个modifier
print("总共有 %s 个 modifier, 每个文件平均: %.2f"%(data['NOMod'].sum(),data['NOMod'].sum()/files))

# 输出总共的代码行数 loc
print("总共有 %s 行代码， 每个文件平均: %.2f"%(data['CountLineCode'].sum(),data['CountLineCode'].sum()/files))


contract_year_dict = {}
year_pattern =re.compile("\d{4}")
# 统计每个文件分别是哪一年被verified 的
index =1
path_url=r"H:\Shared\Smart_Contract_Source_Code\{S_addr}.txt"
for addr in data['contractAddr']:
    full_path = path_url.format(S_addr=addr)
    # print("%s --Reading....%s"%(index,addr))
    with open(full_path, "r", encoding="utf-8") as f:
        f.readline()
        lines= f.readlines(4)
        strs = "".join(lines)
        year = year_pattern.search(strs).group(0)
        assert year
        contract_year_dict[addr]=year
    index = index +1
    if index%1000==0:
        print("index =%s"%index)


print(len(contract_year_dict))
print(Counter(contract_year_dict.values()))
