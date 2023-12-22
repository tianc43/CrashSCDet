import pandas as pd

# 1. 载入数据
data = pd.read_csv("path_to_file.csv")

from pycaret.datasets import get_data
data = get_data('juice')

# 2. 导入模型模块

from pycaret.classification import *
from pycaret.regression import *
from pycaret.clustering import *

# anomaly deection
from pycaret.anomaly import *
# natural language processing
from pycaret.nlp import *
# association rule mining
from pycaret.arules import *

# 函数介绍
