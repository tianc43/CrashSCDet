from typing import *
import solcast
from dbmodules import LanguageRelatedMetric

"""
计算solidity 开发语言相关的特征
"""
class LanguageRelatedCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase):
        """
        @param contract_path 合约的地址
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        # 完成solc-ast的构建
        self.rootNode: solcast.nodes.NodeBase = rootNode

    def _getNOE(self)->float:
        """
        计算event的数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'EventDefinition'}))

    def _getNOMod(self)->float:
        """
        计算modifier的数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ModifierDefinition'}))

    def _getNOMap(self)->float:
        """
        计算mapping的数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'Mapping'}))

    def _getNOT(self)->float:
        """
        计算调用transfer函数的数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionCall', 'expression.memberName': 'transfer'}))

    def _getNOC(self)->float:
        """
        计算调用call 函数的数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionCall', 'expression.memberName': 'call'}))

    def _getNODC(self)->float:
        """
        计算调用delegatecall 函数的数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionCall', 'expression.memberName': 'delegatecall'}))

    def _getNOI(self)->float:
        """
        计算合约文件中，总共定义的interface数量
        """
        return  len(self.rootNode.children(include_children=True,
                                           filters={'nodeType': 'ContractDefinition', 'contractKind': 'interface'}))

    def _getNOL(self)->float:
        """
        计算合约文件中，总共定义的library数量
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'contractKind': 'library'}))

    def _getNOPay(self)->float:
        """
        合约文件中，支持payable的合约
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionDefinition', 'payable': True}))

    def _getNOSV(self)->float:
        """
        合约文件中，所有storage 类型的变量, 1) contract中的stateVariable=True的都是storage类型的； 2） stateVariable = False变量中， mapping array 或者struct 这三种类型的也是storage
        """

        # 1. 状态变量强制是storage 类型
        stateNum = len(self.rootNode.children(include_children=True,
                                              filters={'nodeType': "VariableDeclaration", 'stateVariable': True}))

        # 2. 变量中，明确指定为storage类型的
        snum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType':'VariableDeclaration','storageLocation':'storage'},
                         exclude_filter={'stateVariable': True}))

        # 3. 结构体变量也是storage类型
        strunum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'storageLocation': 'default',
                                  'typeName.nodeType': 'UserDefinedTypeName'},
                         exclude_filter={'stateVariable': True}))

        # 4. 数组变量类型
        arrnum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'storageLocation': 'default',
                                  'typeName.nodeType': 'ArrayTypeName'},
                         exclude_filter={'stateVariable': True}))

        # 5. mapping类型的变量
        mapnum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'storageLocation': 'default',
                                  'typeName.nodeType': 'Mapping'},
                         exclude_filter={'stateVariable': True}))
        return stateNum + snum + strunum + arrnum + mapnum

    def _getSDFB(self)-> bool:
        """
        判断合约是否使用了自定义的call back函数
        """
        # constructor 函数和callback函数的名称都是空串，所以，需要排除先排除constructor函数
        fd: list = self.rootNode.children(include_children=True,
                                    filters={'nodeType': 'FunctionDefinition'}, exclude_filter={'isConstructor': True})
        # 然后从所有剩下的函数中，过滤函数名称是空的函数，该函数就是自定义的call back函数
        callback = [one for one in fd if one.name == ""]

        return True if len(callback) else False

    def _getNOSF(self)->float:
        """
        统计合约文件中，不会发生数据修改的函数的数量,即
        """

        purenum = len(self.rootNode.children(include_children=True,
                                            filters={'nodeType': 'FunctionDefinition', 'stateMutability': 'pure'}))
        # view 和 constant 都被标记成 view
        viewenum = len(self.rootNode.children(include_children=True,
                                             filters={'nodeType': 'FunctionDefinition', 'stateMutability': 'view'}))

        return purenum + viewenum

    def getLanguageRelatedMetric(self)->LanguageRelatedMetric:
        """
        将所有的指标合并成一个对象返回
        """
        metrics = {
            'NOI': self._getNOI(),
            'NOL': self._getNOL(),
            'NOSV': self._getNOSV(),
            'NOMap': self._getNOMap(),
            'NOPay': self._getNOPay(),
            'NOE': self._getNOE(),
            'NOMod': self._getNOMod(),
            'NOT': self._getNOT(),
            'NOC': self._getNOC(),
            'NODC': self._getNODC(),
            'NOSF': self._getNOSF(),
            'SDFB': self._getSDFB()
        }

        return LanguageRelatedMetric(contractAddr=self.contract_addr, **metrics)
