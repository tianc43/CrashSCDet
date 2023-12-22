import solcast, re
from dbmodules import ComplexityMetric
from tools.basic_information import BasicInformation

"""
计算复杂度相关的特征
"""
class ComplexityCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase):
        """
        @param contract_path 合约的地址
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        # 完成solc-ast的构建
        self.rootNode: solcast.nodes.NodeBase = rootNode
        # 找到条件判断中的&&操作符号
        self.andPattern = re.compile("\(.*\&\&.*\)\s*{")
        self.orPattern = re.compile("\(.*\|\|.*\)\s*{")
        self.conditionPattern = re.compile("\(.*\?.*\:.*\)\s*{")
        self.cycomationinfos = self._getCyclomaticInformation()

    def _extractFuncSrc(self, srcPosition) -> str:
        """
        根据AST中，获取函数的源代码位置信息，从源文件中得到其中的函数的源代码
        """
        with open(self.contract_path, "r", encoding="utf-8") as f:
            (start, length, _) = [int(pos) for pos in srcPosition.split(":")]
            f.seek(start)
            outs = f.read(length)
        return outs

    def _calculateAndOrCondition(self, srcPosition: str) -> str:
        """
        从函数的源代码中，提取&&, || 和?:运算符的个数
        """
        srcContent = self._extractFuncSrc(srcPosition)
        andNum: int = len(self.andPattern.findall(srcContent))
        orNum: int = len(self.orPattern.findall(srcContent))
        conditionNum: int = len(self.conditionPattern.findall(srcContent))

        return andNum + orNum + conditionNum

    def _calculateDecisionStatents(self, func) -> int:
        """
        获取"DoWhileStatement", "ForStatement", "IfStatement", "WhileStatement" 语句的个数
        @param func: solcast.nodes.FunctionDefinition Function结点
        """
        dowhilenums = len(func.children(include_children=True, filters={'nodeType': 'DoWhileStatement'}))
        fornums = len(func.children(include_children=True, filters={'nodeType': 'ForStatement'}))
        ifnums = len(func.children(include_children=True, filters={'nodeType': 'IfStatement'}))
        whilenums = len(func.children(include_children=True, filters={'nodeType': 'WhileStatement'}))

        return dowhilenums + fornums + ifnums + whilenums

    def _getCyclomaticInformation(self)-> dict:
        """
        圈复杂度按照如下方法进行计算  http://kaelzhang81.github.io/2017/06/18/%E8%AF%A6%E8%A7%A3%E5%9C%88%E5%A4%8D%E6%9D%82%E5%BA%A6/
        https://blog.csdn.net/The_Reader/article/details/83113207 Solidity中支持的控制语句 if else , for , while,do while,三目运算符。
        不支持switch语句

        圈复杂度的计算最直观的方法，根据``判定条件``的数量，即圈复杂度实际上就是等于判定节点的数量再加上1，也即控制流图的区域数，
        对应的计算公式为： V(G) = P + 1
        其中P为判定节点数，判定节点举例：
          1. if语句 2. while语句 3.for语句 4.case语句 [solidity 不支持] 5.catch语句 [solidity 不支持],
          6. and和or布尔操作 7.对应solidity 中&& 和|| 运算符 8. ?:三元运算符

        在实际计算中，需要分两步走
        step1: 从AST中，直接获取  "DoWhileStatement", "ForStatement", "IfStatement", "WhileStatement", 这四类判定数量的个数
        step2: 从源代码文件中，获取 &&，|| 和三元运算符的操作个数
        """
        # 获得合约地址中，所有定义的函数
        funcs = self.rootNode.children(include_children=True, filters={'nodeType': 'FunctionDefinition'})
        infos = {}
        for func in funcs:
            srcPosition = func.src
            part1 = self._calculateDecisionStatents(func)
            part2 = self._calculateAndOrCondition(srcPosition)
            infos[func.name] = part1 + part2 + 1
        return infos

    def _maxDepth(self, root, nodeID) -> float:
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
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]
        # 一定是只返回一个节点
        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
        # 有可能一个合约地址中，只有一个library, e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]
        mainnodeID = mainnode.id
        return self._maxDepth(root=self.rootNode, nodeID=mainnodeID)

    def _getCountContractCoupled(self) -> float:
        """
        实际计算CBO
        @reference ``Towards Analyzing the Complexity Landscape of solidity based ethereum smart contracts ``
        """
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]

        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
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

    def _getAvgCyclomatic(self) -> float:
        sumNum = sum(self.cycomationinfos.values())
        funNum = len(self.cycomationinfos)
        if sumNum == funNum == 0:
            return 0
        else:
            return float(sumNum) / float(funNum)

    def _getMaxCyclomatic(self) -> float:
        if len(self.cycomationinfos)==0:
            return 0
        else:
            return max(self.cycomationinfos.values())

    def _getSumCyclomatic(self) -> float:
        return sum(self.cycomationinfos.values())


    def _deepVisit(self, rootnode, depth)->float:
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

        if len(do_for_while_if_nodes_list_flatten) == 0:  # 当前节点并没有合适的判定节点, 返回上一层的最大节点
            return depth

        return max(self._deepVisit(child, depth + 1) for child in do_for_while_if_nodes_list_flatten)

    def _getMaxNesting(self) -> float:
        # 获得合约地址中，所有定义的函数
        funcs = self.rootNode.children(include_children=True, filters={'nodeType': 'FunctionDefinition'})
        nesting_list = []
        for f in funcs:
            nesting_list.append(self._deepVisit(f,depth=0))
        if not nesting_list:
            return 0
        else:
            return max(nesting_list)


    def getComplexityMetric(self):
        """
        将所有的指标合并成一个对象返回
        """
        metrics ={
             "AvgCyclomatic": self._getAvgCyclomatic(),
             "MaxCyclomatic": self._getMaxCyclomatic(),
             "MaxInheritanceTree": self._getMaxInheritanceTree(),
             "MaxNesting": self._getMaxNesting(),
             "SumCyclomatic": self._getSumCyclomatic(),
             "CountContractCoupled": self._getCountContractCoupled()
         }
        return ComplexityMetric(contractAddr=self.contract_addr, **metrics)



