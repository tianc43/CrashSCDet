import solcast
from dbmodules import ObjectOrientedMetric
from tools.basic_information import BasicInformation

"""
 
"""
class ObjectOrientedCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase):
        """
        @param contract_path 
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path

        self.rootNode: solcast.nodes.NodeBase = rootNode

    def _getCountTotalFunction(self):
    
        return len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'FunctionDefinition'}))

    def _getCountFunctionPublic(self)->float:
   
        return len(self.rootNode.children(include_children=True,
                                      filters={'nodeType': 'FunctionDefinition', 'visibility': 'public'}))

    def _getCountFunctionPrivate(self)->float:
   
        return len(self.rootNode.children(include_children=True,
                 filters={'nodeType': 'FunctionDefinition','visibility': 'private'}))

    def _getCountFunctionInternal(self)->float:
   
        return len(self.rootNode.children(include_children=True,
                 filters={'nodeType': 'FunctionDefinition','visibility':'internal'}))

    def _getCountFunctionExternal(self)->float:
      
        return len(self.rootNode.children(include_children=True,
                 filters={'nodeType': 'FunctionDefinition','visibility':'external'}))

    def _getCountContract(self)->float:
      
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType':'ContractDefinition', 'contractKind':'contract'}))

    def _getCountVariable(self)->float:
     
        return len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'stateVariable': True}))

    def _getCountPublicVariable(self)->float:
    
        return len(self.rootNode.children(include_children=True,
                       filters={'nodeType':'VariableDeclaration','stateVariable':True,'visibility':'public'}))


    def _getCountContractBase(self)->float:
   
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]
        # 
        # mainnode = self.rootNode.children(include_children=True,
        #                  filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract', 'name': mainContractName})[0]
        # , e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'name': mainContractName})[0]
        return len(mainnode.baseContracts)

    def _getCountDependence(self) -> float:
     
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]
        # 
        # mainnode = self.rootNode.children(include_children=True,
        #                                   filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                            'name': mainContractName})[0]
        # , e.g., 0x005f68eafb2ac24201e8651a1f3d6c79f50c5ec3
        mainnode = self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition','name': mainContractName})[0]
        return len(mainnode.dependencies)

    def _maxDepth(self, root, nodeID)->float:
        """
        , 
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
        return self._maxDepth(root=self.rootNode,nodeID=mainnodeID)


    def _getCountContractCoupled(self)->float:
        """
        
        @reference ``Towards Analyzing the Complexity Landscape of solidity based ethereum smart contracts ``
        """
        mainContractName: str = BasicInformation.MainContract[self.contract_addr.strip()]

        # mainnode = self.rootNode.children(include_children=True,
        #                             filters={'nodeType': 'ContractDefinition', 'contractKind': 'contract',
        #                                      'name': mainContractName})[0]
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

    def getObjectOrientedMetric(self) -> ObjectOrientedMetric:
       
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
