import json
import solcx
import solcast
import time, os, sys

# 获取当前文件所在目录的父目录，并将其添加到sys.path中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from typing import List
from sqlalchemy.orm import *
from sqlalchemy import *
from sqlalchemy.orm import query, scoped_session, session
from orm.dbmodules import *
from orm.db import *
from common.mylogger import logger

from cores.count_metric_extraction import CountMetricCalculator
from cores.language_related_extraction import LanguageRelatedCalculator
from cores.object_oriented_metric_extraction import ObjectOrientedCalculator
from cores.complexity_metric_extraction import ComplexityCalculator


class Extracting:

    def __init__(self, contract_src_path_skeleton:str, contract_root_path:str):
        """
        :param contract_src_path_skeleton 
        :param allow_paths 
        :param contract_root_path 
        """
        self.solc_input_json_str_skeleton = """{
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
        }"""
        self.contract_src_path_skeleton = contract_src_path_skeleton
        # self.allow_paths = "H:\\Shared\\Smart_Contract_Source_Code"
        self.allow_paths = contract_root_path
        self.contract_root_path = contract_root_path


    def _setMostSuitableVersion(self, versions: str):
        print("_setMostSuitableVersion:"+versions)
        solcx.set_solc_version_pragma(versions)
        # # 
        # assert str
        # # 
        # lst = versions.split("")
        # print(lst)
        # if len(lst) == 1:
            
        #     solcx.set_solc_version_pragma(lst[0])
        # else:
            
        #     tempset = set()
        #     for vv in lst:
        #         tempset.add(solcx.set_solc_version_pragma(vv))
        #     # 
        #     # TODO: 
        #     mostSuitableVersion = max(tempset)
        #     solcx.set_solc_version_pragma(mostSuitableVersion.__str__())


    def _getRootNode(self, contractAddr: str, versionString: str)->solcast.nodes.NodeBase:
    

        solc_input_json_str = self.solc_input_json_str_skeleton%(contractAddr, self.contract_src_path_skeleton%(contractAddr) )
        input_json = json.loads(solc_input_json_str)

        # TODO: calculate the most suitable complier version
        self._setMostSuitableVersion(versionString)

        output_json = solcx.compile_standard(input_json, allow_paths=self.allow_paths)
        # print(self.allow_paths)
        nodes: List[solcast.nodes.IterableNodeBase] = solcast.from_standard_output(output_json)
        return nodes[0]

   
    def _tryParse(self,input_json, soc_version)->dict:

        state:bool = True
        try:
            solcx.set_solc_version_pragma(soc_version)
            output_json = solcx.compile_standard(input_json, allow_paths=self.allow_paths)
        except Exception as e:
            state = False
        return {'state':state, 'output_json':output_json}

    def _initProcessingStateTable(self, dbsession: session, submitInteral: int=100):
        if dbsession.query(ProcessingState).first():
            logger.warning("error")
            return

        for root, dirs, files in os.walk(self.allow_paths):
            
            interval:int = 0
            templist = []
            for file in files:
                if file.endswith("txt") or file.endswith("sol"):
                    sol_version_set:set = self._getSolidityVersions(file)
                    templist.append(ProcessingState(contractAddr=os.path.splitext(file)[0],
                                                    fullyextracted= 0 if len(sol_version_set) else -1,
                                                    solc_versions=";".join(sol_version_set)))
                    interval = interval +1
                    if interval % submitInteral ==0: #
                        dbsession.add_all(templist)
                        templist = [] #
                        dbsession.flush()
                        dbsession.commit() # 
                        print("sumbit: %d times" %((interval-1) // submitInteral +1))

            if templist:
                dbsession.add_all(templist)
                dbsession.flush()
                dbsession.commit()
                print("sumbit: %d times" %((interval-1) // submitInteral +1))
    def _getSolidityVersions(self, file_path):
        pragma_line = ""

        try:
            with open(os.path.join(contract_root_path,file_path), 'r') as file:
                for line in file:
                    # 去除行首和行尾的空白字符
                    line = line.strip()
                    if line.startswith("pragma solidity"):
                        pragma_line = line
                        break  # 找到第一个符合条件的行就停止循环

        except FileNotFoundError:
            print(f"文件 '{file_path}' 未找到。")

        return set([pragma_line])
    def _extractComplexityMetric(self, dbsession: session, contractAddress:str, rootNode: solcast.nodes.NodeBase) -> bool:
        
        try:

            cpmResult: ComplexityMetric = ComplexityCalculator(contract_addr=contractAddress,
                                                           contract_path=os.path.join(self.contract_root_path,
                                                                                     contractAddress + "." +
                                                                                     self.contract_src_path_skeleton.split(
                                                                                         ".")[1]),
                                                          rootNode=rootNode).getComplexityMetric()
        except Exception as e:
            logger.error(
                "|_____Extracting ComplexityMetric for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress,
                                                                                               emsg=e))
            return False
        else:
            #
            dbsession.add(cpmResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def _extractCountMetric(self, dbsession: session, contractAddress:str, rootNode: solcast.nodes.NodeBase)-> bool:
        
        try:

            cmResult: CountMetric = CountMetricCalculator(contract_addr=contractAddress,
                                             contract_path= os.path.join(self.contract_root_path, contractAddress+"."+self.contract_src_path_skeleton.split(".")[1]),
                                             rootNode=rootNode).getCountMetrics()
        except Exception as e:
            logger.error(
                "|_____Extracting CountMetric for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress, emsg=e))
            return False
        else:
            # 
            dbsession.add(cmResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def _extractObjectOrientedMetric(self, dbsession: session, contractAddress:str, rootNode: solcast.nodes.NodeBase)-> bool:
        
        try:

            oomResult: ObjectOrientedMetric = ObjectOrientedCalculator(contract_addr=contractAddress,
                                             contract_path= os.path.join(self.contract_root_path, contractAddress+"."+self.contract_src_path_skeleton.split(".")[1]),
                                             rootNode=rootNode).getObjectOrientedMetric()
        except Exception as e:
            logger.error(
                "|_____Extracting ObjectOrientedMetrics for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress, emsg=e))
            return False
        else:
            # 
            dbsession.add(oomResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def _extractLanguageRelatedMetric(self, dbsession: session, contractAddress, rootNode: solcast.nodes.NodeBase)-> bool:
        
        try:

            lrmResult: LanguageRelatedMetric = LanguageRelatedCalculator(contract_addr=contractAddress,
                                                          contract_path=os.path.join(self.contract_root_path,
                                                                                     contractAddress + "." +
                                                                                     self.contract_src_path_skeleton.split(
                                                                                         ".")[1]),
                                                          rootNode=rootNode).getLanguageRelatedMetric()
        except Exception as e:
            logger.error(
                "|___Extracting LanguageRelatedMetric for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress,
                                                                                               emsg=e))
            return False
        else:
            #
            dbsession.add(lrmResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def extractBatchContractFeature(self, dbsession: session, min_id: int = 0, max_id: int = 60000, batchSize: int = 500):
        
        processinglist:List[ProcessingState] = dbsession.query(ProcessingState)\
                                            .filter(ProcessingState.id.between(min_id,max_id))\
                                            .filter(ProcessingState.fullyextracted == 0)\
                                            .limit(batchSize)
        if not processinglist:
            logger.warning("All Smart Contracts Have Been Successfully Feature-Extracted")

        # 
        SCid: int = 1
        for processing in processinglist:
            # time.sleep(0.2)
            contractAddr = processing.contractAddr
            logger.info("Extracting Features for Contract:{contract}".format(contract=contractAddr))

            # 
            cpmState=processing.complexityMetricExtracted
            ctmState=processing.countMetricExtracted
            oomState=processing.objectOrientedMetricExtracted
            lrmState=processing.languageRelatedMetricExtracted

            allState = all([cpmState, ctmState, oomState, lrmState])
            rootNode: solcast.nodes.NodeBase = self._getRootNode(contractAddr=contractAddr,
                                                                 versionString=processing.solc_versions)
            print(processing)
            try:



                if not processing.complexityMetricExtracted:
                    cpmState:bool = self._extractComplexityMetric(dbsession, contractAddr,rootNode=rootNode)

                    if cpmState:
                        logger.info("|___Extracting ComplexityMetric for Contract:{contract} Successfully.".format(
                            contract=contractAddr))
                    else:
                        logger.error("|___Extracting ComplexityMetric for Contract:{contract} Failed!.".format(
                            contract=contractAddr))
                    assert cpmState == True

                if not processing.countMetricExtracted:
                    ctmState:bool = self._extractCountMetric(dbsession, contractAddress=contractAddr, rootNode=rootNode)
                    if ctmState:
                        logger.info("|___Extracting CountMetric Features for Contract:{contract} Successfully.".format(contract=contractAddr))
                    else:
                        logger.error("|___Extracting CountMetric Features for Contract:{contract} Failed!.".format(
                            contract=contractAddr))
                    assert ctmState==True

                if not processing.objectOrientedMetricExtracted:
                    oomState:bool = self._extractObjectOrientedMetric(dbsession, contractAddress=contractAddr, rootNode=rootNode)
                    if oomState:
                        logger.info("|___Extracting ObjectOrientedMetric Features for Contract:{contract} Successfully.".format(
                            contract=contractAddr))
                    else:
                        logger.error("|___Extracting ObjectOrientedMetric Features for Contract:{contract} Failed!.".format(
                            contract=contractAddr))
                    assert oomState == True

                if not processing.languageRelatedMetricExtracted:
                    lrmState:bool = self._extractLanguageRelatedMetric(dbsession, contractAddress=contractAddr, rootNode=rootNode)
                    if lrmState:
                        logger.info("|___Extracting LanguageRelatedMetric Features for Contract:{contract} Successfully.".format(
                            contract=contractAddr))
                    else:
                        logger.error("|___Extracting LanguageRelatedMetric Features for Contract:{contract} Failed!.".format(
                            contract=contractAddr))
                    assert lrmState == True

            except Exception as e:
                logger.error("|___Extracting Features for Contract:{contract} ERROR: {emsg}".format(contract=contractAddr,emsg=e))
                
                break
            else:
                allState = all([cpmState,  ctmState, oomState, lrmState])
                if allState:
                    logger.success("Extracting Features for Contract:{contract} Full SUCCESSFULLY!".format(contract=contractAddr))
                else:
                    logger.warning("Extracting Features for Contract:{contract} PARTIAL SUCCESSFULLY!".format(contract=contractAddr))
            finally:
                processing.fullyextracted=allState
                processing.complexityMetricExtracted=cpmState
                processing.countMetricExtracted=ctmState
                processing.objectOrientedMetricExtracted=oomState
                processing.languageRelatedMetricExtracted=lrmState
                dbsession.commit()
                dbsession.flush()
                logger.success("Update Information on ProcessingState Table for  Contract:{contract} successfully!".format(contract=contractAddr))
                SCid = SCid+1


if __name__ == '__main__':


    dbsession: session = DBOperator().getNewSession()
    # contract_src_path_skeleton= "D:\\\contractsrcs\\\%s.sol"
    # contract_root_path = r"D:\\contractsrcs"

    contract_src_path_skeleton = r"/home/debian/CrashSCDet/DATA/test-solidity/%s.sol"
    contract_root_path = r"/home/debian/CrashSCDet/DATA/test-solidity"

    instance = Extracting(contract_src_path_skeleton, contract_root_path=contract_root_path)
    instance._initProcessingStateTable(dbsession)
    instance.extractBatchContractFeature(dbsession, min_id=0, max_id=60000, batchSize=300)

    dbsession.close()


    print("Feature Extraction Finish!")