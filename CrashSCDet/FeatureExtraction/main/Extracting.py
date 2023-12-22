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
from ORM.dbmodules import *
from ORM.db import *
from Common.mylogger import logger

from cores.count_metric_extraction import CountMetricCalculator
from cores.language_related_extraction import LanguageRelatedCalculator
from cores.object_oriented_metric_extraction import ObjectOrientedCalculator
from cores.complexity_metric_extraction import ComplexityCalculator


class Extracting:

    def __init__(self, contract_src_path_skeleton:str, contract_root_path:str):
        """
        :param contract_src_path_skeleton 存放合约文件的路径模板
        :param allow_paths 允许编译时候访问的文件夹
        :param contract_root_path 合约存放的根目录
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
        self.allow_paths = "H:\\Shared\\Smart_Contract_Source_Code"
        self.allow_paths = contract_root_path
        self.contract_root_path = contract_root_path


    def _setMostSuitableVersion(self, versions: str):
        """
        根据合约文件中提供的版本信息，选择最合适的编译器
        """
        # 确保传入的不是空串
        assert str
        # 将数据库中的数据分割出来
        # lst = versions.split(";")
        lst = [versions]
        # print(lst)
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


    def _getRootNode(self, contractAddr: str, versionString: str)->solcast.nodes.NodeBase:
        """
        通过solc 和 astcast 工具，对解析后的AST进行操作
        :param contractAddr 合约地址
        """

        solc_input_json_str = self.solc_input_json_str_skeleton%(contractAddr, self.contract_src_path_skeleton%(contractAddr) )
        input_json = json.loads(solc_input_json_str)

        # TODO: calculate the most suitable complier version
        self._setMostSuitableVersion(versionString)

        output_json = solcx.compile_standard(input_json, allow_paths=self.allow_paths)
        # print(self.allow_paths)
        nodes: List[solcast.nodes.IterableNodeBase] = solcast.from_standard_output(output_json)
        return nodes[0]

    # def _getRootNode(self, contractAddr: str, versionString: str) -> solcast.nodes.NodeBase:
    #     """
    #     通过solc 和 astcast 工具，对解析后的AST进行操作
    #     :param contractAddr 合约地址
    #     """
    #
    #     solc_input_json_str = self.solc_input_json_str_skeleton % (
    #     contractAddr, self.contract_src_path_skeleton % (contractAddr))
    #     input_json = json.loads(solc_input_json_str)
    #
    #     # TODO: calculate the most suitable complier version
    #     try:
    #         self._setMostSuitableVersion(versionString)
    #         output_json = solcx.compile_standard(input_json, allow_paths=self.allow_paths)
    #     except Exception:
    #         versions = solcx.get_installed_solc_versions()
    #         logger.info("正在尝试不同的编译器：")
    #         for vers in versions[::-1]:
    #             logger.info("|__正在尝试编译器：%s。"%vers)
    #             outs = self._tryParse(input_json, soc_version=vers)
    #             if outs['state']: # 找到合适的编码器了
    #                 logger.info("|__成功找到编译器：%s。" % vers)
    #                 output_json = outs['output_json']
    #                 nodes: List[solcast.nodes.IterableNodeBase] = solcast.from_standard_output(output_json)
    #                 break
    #     else:
    #         # print(self.allow_paths)
    #         nodes: List[solcast.nodes.IterableNodeBase] = solcast.from_standard_output(output_json)
    #
    #     return nodes[0]

    def _tryParse(self,input_json, soc_version)->dict:
        """
        通过solc 和 astcast 工具，对解析后的AST进行操作
        :param contractAddr 合约地址
        """
        state:bool = True
        try:
            # 正确的情况
            solcx.set_solc_version_pragma(soc_version)
            output_json = solcx.compile_standard(input_json, allow_paths=self.allow_paths)
        except Exception as e:
            state = False
        return {'state':state, 'output_json':output_json}

    def _initProcessingStateTable(self, dbsession: session, submitInteral: int=100):
        """
        该方法只执行一次，从文件夹中提取合约地址，然后将其存储到数据库中
        :parameter session 链接数据库的session
        :parameter submitInteral 批量插入数据时，间隔多少条数据提交一次
        :parameter sleepSec 每一批次提交之后暂停多少秒
        :return:
        """
        # 如果已经存在数据了，就直接退出，人工检查
        if dbsession.query(ProcessingState).first():
            logger.warning("表格中已经存在数据，请人工检查是否需要重新初始化")
            return

        for root, dirs, files in os.walk(self.allow_paths):
            # 直接遍历合约文件，从文件名中提取合约地址,
            interval:int = 0
            templist = []
            for file in files:
                if file.endswith("txt") or file.endswith("sol"):
                    sol_version_set:set = self._getSolidityVersions(file)
                    templist.append(ProcessingState(contractAddr=os.path.splitext(file)[0],
                                                    fullyextracted= 0 if len(sol_version_set) else -1,
                                                    solc_versions=";".join(sol_version_set)))
                    interval = interval +1
                    if interval % submitInteral ==0: #达到提交次数
                        dbsession.add_all(templist)
                        templist = [] #清空提交的数据
                        dbsession.flush()
                        dbsession.commit() # 提交
                        print("sumbit: %d times" %((interval-1) // submitInteral +1))

            if templist:
                dbsession.add_all(templist)
                dbsession.flush()
                dbsession.commit()
                print("sumbit: %d times" %((interval-1) // submitInteral +1))

    def _extractComplexityMetric(self, dbsession: session, contractAddress:str, rootNode: solcast.nodes.NodeBase) -> bool:
        """
        抽取复杂度相关的特征指标
        :param session
        :param contractAddress 当前正在处理的合约地址
        :param rootNode solc ast 构建后的根节点
        :return: 返回当前抽取是否正确
        """
        try:

            calculator = ComplexityCalculator(contract_addr=contractAddress,
                                                           contract_path=os.path.join(self.contract_root_path,
                                                                                     contractAddress + "." +
                                                                                     self.contract_src_path_skeleton.split(
                                                                                         ".")[1]),
                                                          rootNode=rootNode)
            cpmResult: ComplexityMetric = calculator.getComplexityMetric()
        except Exception as e:
            logger.error(
                "|_____Extracting ComplexityMetric for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress,
                                                                                               emsg=e))
            return False
        else:
            # 抽取正确, 添加指标数据
            dbsession.add(cpmResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def _extractCountMetric(self, dbsession: session, contractAddress:str, rootNode: solcast.nodes.NodeBase)-> bool:
        """
        抽取数量相关的特征指标
        :param session
        :param contractAddress 当前正在处理的合约地址
        :param rootNode solc ast 构建后的根节点
        :return: 返回当前抽取是否正确
        """
        try:

            cmResult: CountMetric = CountMetricCalculator(contract_addr=contractAddress,
                                             contract_path= os.path.join(self.contract_root_path, contractAddress+"."+self.contract_src_path_skeleton.split(".")[1]),
                                             rootNode=rootNode).getCountMetrics()
        except Exception as e:
            logger.error(
                "|_____Extracting CountMetric for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress, emsg=e))
            return False
        else:
            # 抽取正确, 添加指标数据
            dbsession.add(cmResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def _extractObjectOrientedMetric(self, dbsession: session, contractAddress:str, rootNode: solcast.nodes.NodeBase)-> bool:
        """
        抽取面向对象相关的特征指标
        :param session
        :param contractAddress 当前正在处理的合约地址
        :param rootNode solc ast 构建后的根节点
        :return: 返回当前抽取是否正确
        """
        try:

            oomResult: ObjectOrientedMetric = ObjectOrientedCalculator(contract_addr=contractAddress,
                                             contract_path= os.path.join(self.contract_root_path, contractAddress+"."+self.contract_src_path_skeleton.split(".")[1]),
                                             rootNode=rootNode).getObjectOrientedMetric()
        except Exception as e:
            logger.error(
                "|_____Extracting ObjectOrientedMetrics for Contract:{contract} ERROR: {emsg}".format(contract=contractAddress, emsg=e))
            return False
        else:
            # 抽取正确, 添加指标数据
            dbsession.add(oomResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def _extractLanguageRelatedMetric(self, dbsession: session, contractAddress, rootNode: solcast.nodes.NodeBase)-> bool:
        """
        抽取开发语言相关的特征
        :param session
        :param contractAddress 当前正在处理的合约地址
        :param rootNode solc ast 构建后的根节点
        :return: 返回当前抽取是否正确
        """
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
            # 抽取正确, 添加指标数据
            dbsession.add(lrmResult)
            dbsession.commit()
            dbsession.flush()
            return True

    def extractBatchContractFeature(self, dbsession: session, min_id: int = 0, max_id: int = 60000, batchSize: int = 500):
        """
        该方法从processingstate 数据表中，读取所有未抽取过特征的数据，进行各个维度的特征抽取
        :parameter dbsession 数据库连接的session
        :parameter batchSize 每一次处理多少个合约
        :parameter min_id 处理的id最小值，包含该值
        :parameter max_id 处理的id最大值，不包含该值
        :return:
        """
        processinglist:List[ProcessingState] = dbsession.query(ProcessingState)\
                                            .filter(ProcessingState.id.between(min_id,max_id))\
                                            .filter(ProcessingState.fullyextracted == 0)\
                                            .limit(batchSize)
        if not processinglist:
            logger.warning("All Smart Contracts Have Been Successfully Feature-Extracted")

        # 循环处理每一个合约地址
        SCid: int = 1
        for processing in processinglist:
            # time.sleep(0.2)
            print("当前抽取特征的批次完成进度: %d / %d"%(SCid,batchSize))
            contractAddr = processing.contractAddr
            logger.info("Extracting Features for Contract:{contract}".format(contract=contractAddr))

            # 初始化
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
                # 遇到出错，暂时先停止
                break
            else:
                allState = all([cpmState,  ctmState, oomState, lrmState])
                # 正确执行的话，那么就去更新数据库，当然上述的四类指标在执行时候，可能有的存在错误
                if allState:
                    logger.success("Extracting Features for Contract:{contract} Full SUCCESSFULLY!".format(contract=contractAddr))
                else:
                    logger.warning("Extracting Features for Contract:{contract} PARTIAL SUCCESSFULLY!".format(contract=contractAddr))
            finally:
                # 更新数据库
                # 由于ORM的原因，直接更新对象即可
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

    contract_src_path_skeleton = "/home/debian/CrashSCDet/DATA/test-solidity/%s.sol"
    contract_root_path = r"/home/debian/CrashSCDet/DATA/test-solidity"

    instance = Extracting(contract_src_path_skeleton, contract_root_path=contract_root_path)
    # 该方法只调用一次
    # instance._initProcessingStateTable(dbsession)
    instance.extractBatchContractFeature(dbsession, min_id=0, max_id=60000, batchSize=300)

    dbsession.close()


    print("Feature Extraction Finish!")