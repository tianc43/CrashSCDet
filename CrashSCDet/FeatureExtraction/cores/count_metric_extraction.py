from typing import *
import solcast
from dbmodules import CountMetric


"""

"""
class CountMetricCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase ):
        """
        @param contract_path 
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        #
        self.rootNode: solcast.nodes.NodeBase = rootNode

    def _statisLines(self):
        """
         CountLineCode    CountLineComment   CountLineCodeExe
        """
        with open(self.contract_path, "r", encoding="utf-8") as f:
            # TODO: 
            lines: List(str) = f.readlines()[4:]
            total_lines: float = len(lines)
            blank_lines: float = 0
            comment_lines: float = 0
            execution_lines: float = 0

            multilineState: bool = False
            # 
            for line in lines:
                if line.strip() == "":
                    blank_lines = blank_lines + 1
                    continue;

                if multilineState:
                    comment_lines = comment_lines + 1
                    if line.strip().endswith("*/"):
                        multilineState = False
                else:
                    if line.strip().startswith("/*"):
                        multilineState = True
                        comment_lines = comment_lines + 1
                        if line.strip().endswith("*/"):
                            multilineState = False

                    # 
                    elif line.strip().startswith("//"):
                        comment_lines = comment_lines + 1
                    else:
                        execution_lines = execution_lines + 1
                        if "//" in line.strip():
                            comment_lines = comment_lines + 1

        return {'CountLineCode': total_lines, 'CountLineBlank': blank_lines, 'CountLineComment': comment_lines, 'CountLineCodeExe': execution_lines}

    def _getCountStmt(self):
        """
       
        """
        return len(self.rootNode.children(include_children=True, filters={'baseNodeType': 'Statement'}))


    def getCountMetrics(self)->CountMetric:
        """
        
        """
        statistic = self._statisLines()
        countStmt = self._getCountStmt()

        return CountMetric(contractAddr=self.contract_addr,
                           CountLineCode=statistic['CountLineCode'],
                           CountLineCodeExe=statistic['CountLineCodeExe'],
                           CountLineComment=statistic['CountLineComment'],
                           CountStmt=countStmt,
                           CountLineBlank=statistic['CountLineBlank'],
                           RatioCommentToCode= statistic['CountLineComment'] / statistic['CountLineCode'])