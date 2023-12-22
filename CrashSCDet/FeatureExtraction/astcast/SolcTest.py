import json
import solcx, re
import solcast
from solcast.nodes import NodeBase, IterableNodeBase
from typing import *
from db import *
from dbmodules import *
from tools.basic_information import BasicInformation



contract_name = "0x75764e5aed7fe9269d89b7c293727422a0454228"
# contract_name = "0x00138bd67465733ae1bedfd2105a6ffa83af97d8"
# contract_name = "0x00a4a3e9279678ca1b564bca66396bb5801192da"
# contract_name = "0x000000005fbe2cc9b1b684ec445caf176042348e"

# 0x00a4a3e9279678ca1b564bca66396bb5801192da
# avaliables = solcx.get_installed_solc_versions()
#
# def tryToDefine():


contract_src_path = "D:\\\contractsrcs\\\%s.txt"%(contract_name)
allow_path="D:\\contractsrcs"

# contract_src_path = "H:\\\Shared\\\Smart_Contract_Source_Code\\\%s.txt"%(contract_name)
# allow_path="H:\\Shared\\Smart_Contract_Source_Code"


dbsession = DBOperator().getNewSession()
socl_input_json_str = """{
  "language":"Solidity",
  "sources":
  {
    "%s.sol":
    {
      "urls":
      [
      "%s"
      ]
    }
  },
  "settings":
  {
    "evmVersion": "byzantium",
    "outputSelection": {
      "*": {
        "*": ["abi","devdoc","userdoc", "metadata","evm.bytecode.sourceMap"]
      },
      "*": {
        "": ["ast","evm.bytecode.sourceMap"]
      }
    }
  }
}""" % (contract_name,contract_src_path)

def setMostSuitableVersion(versions: str) -> str:
    """
    根据合约文件中提供的版本信息，选择最合适的编译器
    """
    # 确保传入的不是空串
    assert str
    # 将数据库中的数据分割出来
    lst = versions.split(";")
    if len(lst) == 1:
        # 只有一个
        solcx.set_solc_version_pragma(lst[0])
    else:
        # 合约中提到了多种类型的多个版本
        tempset = set()
        for vv in lst:
            tempset.add(solcx.set_solc_version_pragma(vv))
        # 最大的版本认为是最合适的
        # TODO: 由于solidity版本之间的差异较大，当前这个假设不一定成立，如果遇到编译问题，再处理
        mostSuitableVersion = max(tempset)
        solcx.set_solc_version_pragma(mostSuitableVersion.__str__())

# 找到该合约的内容，并且确保该合约能够被编译
object: ProcessingState = dbsession.query(ProcessingState)\
    .filter(ProcessingState.contractAddr==contract_name,ProcessingState.fullyextracted!=-1)\
    .one()
assert object
# setMostSuitableVersion(object.solc_versions)

solcx.set_solc_version("0.5.0")


input_json = json.loads(socl_input_json_str)
output_json = solcx.compile_standard(input_json, allow_paths=allow_path)
# print(output_json,file=open("tmp.json","w"))





nodes: List[solcast.nodes.IterableNodeBase] = solcast.from_standard_output(output_json)
onenode: solcast.nodes.NodeBase = nodes[0]
fd:list= onenode.children(include_children=True,
                       filters={'nodeType': 'FunctionDefinition'})


mainContractName: str = BasicInformation.MainContract[contract_name.strip()]
# mainContractName='ProperProposal'
# 一定是只返回一个节点
# mainnode = onenode.children(include_children=True,
#                                   filters = {'nodeType': 'ContractDefinition', 'contractKind': 'contract',
#                                            'name': mainContractName})[0]
mainnode = onenode.children(include_children=True,
                                  filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract','name': mainContractName})[0]



# 获得合约地址中，所有定义的函数
funcs = onenode.children(include_children=True, filters={'nodeType':'FunctionDefinition'})

def deepVisit(rootnode, depth):
    """
       按照多叉树的思想，深度优先访问判断结点的最大深度
       @param rootnode 根节点
       @param depth 当前的继承深度
    """

    do_for_while_if_nodes_list = []
    # 这里遍历子结点的时候，只能遍历第一层子节点
    do_for_while_if_nodes_list.append(
        rootnode.children(include_children=True, depth=1, filters={'nodeType': 'DoWhileStatement'}))
    do_for_while_if_nodes_list.append(
        rootnode.children(include_children=True, depth=1, filters={'nodeType': 'ForStatement'}))
    do_for_while_if_nodes_list.append(
        rootnode.children(include_children=True, depth=1, filters={'nodeType': 'IfStatement'}))
    do_for_while_if_nodes_list.append(
        rootnode.children(include_children=True, depth=1, filters={'nodeType': 'WhileStatement'}))
    # flatten arrays of list
    do_for_while_if_nodes_list_flatten = [y for x in do_for_while_if_nodes_list for y in x]

    if len(do_for_while_if_nodes_list_flatten) == 0: # 当前节点并没有合适的判定节点, 返回上一层的最大节点
        return depth

    return max( deepVisit(child, depth+1) for child in do_for_while_if_nodes_list_flatten )


for f in funcs:
    print("FuncName: %s, Max Nesting %s "%(f,deepVisit(f, depth=0)))



# with open(contract_src_path,"r", encoding="utf-8") as f:
#     f.seek(1926)
#     print(f.read(50))





