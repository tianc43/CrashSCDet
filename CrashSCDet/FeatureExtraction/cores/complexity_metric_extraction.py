import solcast, re
from dbmodules import ComplexityMetric
from tools.basic_information import BasicInformation

"""

"""
class ComplexityCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase):
        """
        @param contract_path 
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        # 
        self.rootNode: solcast.nodes.NodeBase = rootNode
        # 
        self.andPattern = re.compile("\(.*\&\&.*\)\s*{")
        self.orPattern = re.compile("\(.*\|\|.*\)\s*{")
        self.conditionPattern = re.compile("\(.*\?.*\:.*\)\s*{")
        self.cycomationinfos = self._getCyclomaticInformation()

    def _extractFuncSrc(self, srcPosition) -> str:
        """
        
        """
        with open(self.contract_path, "r", encoding="utf-8") as f:
            (start, length, _) = [int(pos) for pos in srcPosition.split(":")]
            f.seek(start)
            outs = f.read(length)
        return outs

    def _calculateAndOrCondition(self, srcPosition: str) -> str:
        """
       
        """
        srcContent = self._extractFuncSrc(srcPosition)
        andNum: int = len(self.andPattern.findall(srcContent))
        orNum: int = len(self.orPattern.findall(srcContent))
        conditionNum: int = len(self.conditionPattern.findall(srcContent))

        return andNum + orNum + conditionNum

    def _calculateDecisionStatents(self, func) -> int:
        """
      
        @param func: solcast.nodes.FunctionDefinition 
        """
        dowhilenums = len(func.children(include_children=True, filters={'nodeType': 'DoWhileStatement'}))
        fornums = len(func.children(include_children=True, filters={'nodeType': 'ForStatement'}))
        ifnums = len(func.children(include_children=True, filters={'nodeType': 'IfStatement'}))
        whilenums = len(func.children(include_children=True, filters={'nodeType': 'WhileStatement'}))

        return dowhilenums + fornums + ifnums + whilenums

    def _getCyclomaticInformation(self)-> dict:
        
        # 
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
       
        @param root 
        @param nodeID 
        """

        if nodeID < 0:
            return 0
        # 
        inherited_list = root.children(filters={"id": nodeID})[0].baseContracts
        if len(inherited_list) == 0:
            return 0
        # 
        inherited_ids = [item.baseName.referencedDeclaration for item in inherited_list]

        return 1 + max(self._maxDepth(root, child) for child in inherited_ids)

    def _getMaxInheritanceTree(self) -> float:
        """
        
        """
        # 1 
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]
        # 
        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
        # , e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]
        mainnodeID = mainnode.id
        return self._maxDepth(root=self.rootNode, nodeID=mainnodeID)

    def _getCountContractCoupled(self) -> float:
        """
        
        @reference ``Towards Analyzing the Complexity Landscape of solidity based ethereum smart contracts ``
        """
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]

        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
        # , e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]

        # 1. 
        allUserDefinedVars = mainnode.children(include_children=True, filters={'nodeType': 'VariableDeclaration',
                                                                               'typeName.nodeType': 'UserDefinedTypeName'})
        uniques = set()
        for item in allUserDefinedVars:
            uniques.add(item.typeName.name)

        # 2. 
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
           
           @param rootnode 
           @param depth 
        """

        do_for_while_if_nodes_list = []
        # 
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

        if len(do_for_while_if_nodes_list_flatten) == 0:  # 
            return depth

        return max(self._deepVisit(child, depth + 1) for child in do_for_while_if_nodes_list_flatten)

    def _getMaxNesting(self) -> float:
        # 
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



