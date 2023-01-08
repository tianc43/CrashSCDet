from typing import *
import solcast
from dbmodules import LanguageRelatedMetric

"""
"""
class LanguageRelatedCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase):
        """
        @param contract_path 
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        # -
        self.rootNode: solcast.nodes.NodeBase = rootNode

    def _getNOE(self)->float:
        """
        
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'EventDefinition'}))

    def _getNOMod(self)->float:
        """
        
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ModifierDefinition'}))

    def _getNOMap(self)->float:
        """
        
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'Mapping'}))

    def _getNOT(self)->float:
        """
        
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionCall', 'expression.memberName': 'transfer'}))

    def _getNOC(self)->float:
        """
         
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionCall', 'expression.memberName': 'call'}))

    def _getNODC(self)->float:
        """
         
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionCall', 'expression.memberName': 'delegatecall'}))

    def _getNOI(self)->float:
        """
        
        """
        return  len(self.rootNode.children(include_children=True,
                                           filters={'nodeType': 'ContractDefinition', 'contractKind': 'interface'}))

    def _getNOL(self)->float:
        """
        
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'ContractDefinition', 'contractKind': 'library'}))

    def _getNOPay(self)->float:
        """
        
        """
        return len(self.rootNode.children(include_children=True,
                                          filters={'nodeType': 'FunctionDefinition', 'payable': True}))

    def _getNOSV(self)->float:
      

        # 1 
        stateNum = len(self.rootNode.children(include_children=True,
                                              filters={'nodeType': "VariableDeclaration", 'stateVariable': True}))

        # 2. 
        snum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType':'VariableDeclaration','storageLocation':'storage'},
                         exclude_filter={'stateVariable': True}))

        # 3. 
        strunum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'storageLocation': 'default',
                                  'typeName.nodeType': 'UserDefinedTypeName'},
                         exclude_filter={'stateVariable': True}))

        # 4. 
        arrnum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'storageLocation': 'default',
                                  'typeName.nodeType': 'ArrayTypeName'},
                         exclude_filter={'stateVariable': True}))

        # 5. 
        mapnum = len(self.rootNode.children(include_children=True,
                         filters={'nodeType': 'VariableDeclaration', 'storageLocation': 'default',
                                  'typeName.nodeType': 'Mapping'},
                         exclude_filter={'stateVariable': True}))
        return stateNum + snum + strunum + arrnum + mapnum

    def _getSDFB(self)-> bool:
       
      
        fd: list = self.rootNode.children(include_children=True,
                                    filters={'nodeType': 'FunctionDefinition'}, exclude_filter={'isConstructor': True})
        #  
        callback = [one for one in fd if one.name == ""]

        return True if len(callback) else False

    def _getNOSF(self)->float:
      

        purenum = len(self.rootNode.children(include_children=True,
                                            filters={'nodeType': 'FunctionDefinition', 'stateMutability': 'pure'}))
        # view  constant  view
        viewenum = len(self.rootNode.children(include_children=True,
                                             filters={'nodeType': 'FunctionDefinition', 'stateMutability': 'view'}))

        return purenum + viewenum

    def getLanguageRelatedMetric(self)->LanguageRelatedMetric:
        """
        
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
