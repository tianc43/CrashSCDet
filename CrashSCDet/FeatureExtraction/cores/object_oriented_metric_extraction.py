import solcast
import sys,os
# 获取当前文件所在目录的父目录，并将其添加到sys.path中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
from ORM.dbmodules import ObjectOrientedMetric
from tools.basic_information import BasicInformation

"""
计算面向对象 开发语言相关的特征
"""
class ObjectOrientedCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase):
        """
        @param contract_path 合约的地址
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        # 完成solc-ast的构建
        self.rootNode: solcast.nodes.NodeBase = rootNode

    def _getCountTotalFunction(self):
        """
        获取合约文件中的所有的函数的function个数，包括构造函数
        """
        return len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'FunctionDefinition'}))

    def _getCountFunctionPublic(self)->float:
        """
        获得合约文件中，所有可见性为public的函数
        """
        return len(self.rootNode.children(include_children=True,
                                      filters={'nodeType': 'FunctionDefinition', 'visibility': 'public'}))

    def _getCountFunctionPrivate(self)->float:
        """
        获得合约文件中，所有可见性为public的函数
        """
        return len(self.rootNode.children(include_children=True,
                 filters={'nodeType': 'FunctionDefinition','visibility': 'private'}))

    def _getCountFunctionInternal(self)->float:
        """
        获取合约文件中，所有可见性为internal的函数
        """
        return len(self.rootNode.children(include_children=True,
                 filters={'nodeType': 'FunctionDefinition','visibility':'internal'}))

    def _getCountFunctionExternal(self)->float:
        """
        获取合约文件中，所有可见性为external的函数
        """
        return len(self.rootNode.children(include_children=True,
                 filters={'nodeType': 'FunctionDefinition','visibility':'external'}))

    def _getCountContract(self)->float:
        """
        获取合约个数的方法
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType':'ContractDefinition', 'contractKind':'contract'}))

    def _getCountVariable(self)->float:
        """
        返回合约文件中所有的状态变量的个数
        """
        return len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'stateVariable': True}))

    def _getCountPublicVariable(self)->float:
        """
        返回合约文件中所有的可见性为public的状态变量的个数
        """
        return len(self.rootNode.children(include_children=True,
                       filters={'nodeType':'VariableDeclaration','stateVariable':True,'visibility':'public'}))


    def _getCountContractBase(self)->float:
        """
        返回主合约继承的合约的数量，就是源代码中直接继承的数量
        """
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip().lower()]
        # 一定是只返回一个节点
        # mainnode = self.rootNode.children(include_children=True,
        #                  filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract', 'name': mainContractName})[0]
        # 有可能一个合约地址中，只有一个library, e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]
        return len(mainnode.baseContracts)

    def _getCountDependence(self) -> float:
        """
        返回主合约所有的依赖数，一方面主合约继承了一些合约，另一方面这些被继承的合约也可能继承了其他的合约，所有统计主合约的所有以来
        """
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip().lower()]
        # 一定是只返回一个节点
        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
        # 有可能一个合约地址中，只有一个library, e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition','name': mainContractName})[0]
        return len(mainnode.dependencies)

    def _maxDepth(self, root, nodeID)->float:
        """
        按照多叉树的思想，访问继承树的深度, 如果结果的id是负数，表明节点不存在
        @param root 根节点
        @param nodeID 继承的树的根ID
        """

        if nodeID < 0:
            return 0
        # 得到当前节点的对象
        inherited_list = root.children(filters={"id": nodeID})[0].baseContracts
        if len(inherited_list) == 0:
            return 0
        # 继承的合约是通过referencedDeclaration域制定的id进行的
        inherited_ids = [item.baseName.referencedDeclaration for item in inherited_list]

        return 1 + max(self._maxDepth(root, child) for child in inherited_ids)

    def _getMaxInheritanceTree(self) -> float:
        """
        返回合约中，最大的继承深度
        """
        # 1 从合约的主方法入手
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip().lower()]
        # 一定是只返回一个节点
        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
        # 有可能一个合约地址中，只有一个library, e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]


        mainnodeID = mainnode.id
        return self._maxDepth(root=self.rootNode,nodeID=mainnodeID)


    def _getCountContractCoupled(self)->float:
        """
        实际计算CBO
        @reference ``Towards Analyzing the Complexity Landscape of solidity based ethereum smart contracts ``
        """
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip().lower()]

        # mainnode = self.rootNode.children(include_children=True,
        #                             filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                      'name': mainContractName})[0]
        # 有可能一个合约地址中，只有一个library, e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]

        # 1. 首先获得主合约上所有的变量声明，并且类型是用户自定义的
        allUserDefinedVars = mainnode.children(include_children=True, filters={'nodeType': 'VariableDeclaration',
                                                                               'typeName.nodeType': 'UserDefinedTypeName'})
        uniques = set()
        for item in allUserDefinedVars:
            uniques.add(item.typeName.name)

        # 2. 统计一下，主合约内部定义的结构体等自定义的结构类型
        inner_struct_defination = mainnode.children(include_children=True, filters={'nodeType': 'StructDefinition'})
        self_inner_user_defination = set()
        for node in inner_struct_defination:
            self_inner_user_defination.add(node.name)

        return len(uniques.difference(self_inner_user_defination))

    def getObjectOrientedMetric(self) -> ObjectOrientedMetric:
        """
        将所有的指标合并成一个object-oriented对象返回
        """
        metrics={
            'CountContractBase': self._getCountContract(),
            'CountDependence': self._getCountDependence(),
            'CountContractCoupled': self._getCountContractCoupled(),
            'CountContract': self._getCountContract(),
            'CountTotalFunction': self._getCountTotalFunction(),
            'CountPublicVariable': self._getCountPublicVariable(),
            'CountVariable': self._getCountVariable(),
            'CountFunctionPrivate': self._getCountFunctionPrivate(),
            'CountFunctionInternal': self._getCountFunctionInternal(),
            'CountFunctionExternal': self._getCountFunctionExternal(),
            'CountFunctionPublic': self._getCountFunctionPublic(),
            'MaxInheritanceTree': self._getMaxInheritanceTree()
        }

        return ObjectOrientedMetric(contractAddr=self.contract_addr,**metrics)
