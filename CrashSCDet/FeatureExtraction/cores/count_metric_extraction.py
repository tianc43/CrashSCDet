from typing import *
import solcast
from dbmodules import CountMetric


"""
计算数量相关的指标方法
"""
class CountMetricCalculator:

    def __init__(self, contract_addr: str, contract_path: str, rootNode: solcast.nodes.NodeBase ):
        """
        @param contract_path 合约的地址
        """
        self.contract_addr = contract_addr
        self.contract_path = contract_path
        # 完成solc-ast的构建
        self.rootNode: solcast.nodes.NodeBase = rootNode

    def _statisLines(self):
        """
        统计代码行相关的行数 CountLineCode    CountLineComment   CountLineCodeExe
        """
        with open(self.contract_path, "r", encoding="utf-8") as f:
            # TODO: 移除每个文件的前几行, 这些内容似乎是后续添加的，所以跟源文件没有任何关系，直接将其删除
            lines: List(str) = f.readlines()[4:]
            total_lines: float = len(lines)
            blank_lines: float = 0
            comment_lines: float = 0
            execution_lines: float = 0

            multilineState: bool = False
            # 计算空行
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

                    # 找到可执行的代码行
                    elif line.strip().startswith("//"):
                        comment_lines = comment_lines + 1
                    else:
                        execution_lines = execution_lines + 1
                        if "//" in line.strip():
                            comment_lines = comment_lines + 1

        return {'CountLineCode': total_lines, 'CountLineBlank': blank_lines, 'CountLineComment': comment_lines, 'CountLineCodeExe': execution_lines}

    def _getCountStmt(self):
        """
        直接通过solcast 遍历子节点中，基本属性baseNodeType 为Statement 的节点，然后统计启数量
        """
        return len(self.rootNode.children(include_children=True, filters={'baseNodeType': 'Statement'}))


    def getCountMetrics(self)->CountMetric:
        """
        将所有的指标打包成一个对象返回
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