from pycaret.classification import *
import pandas as pd
import numpy

numpy.random.seed(seed=2)  # 如果使用相同的seed( )值，则每次生成的随即数都相同

raw_data = pd.read_csv(r"./results.csv")
raw_data = raw_data.drop(["id", "contractAddr"], axis=1)

# 分层抽样字典定义 组名：数据个数
typicalNDict = {1: 5000, 0: 5000}


# label_0 = 12571
# label_1 = 7429

# 函数定义
def typicalsamling(group, typicalNDict):
    name = group.name
    n = typicalNDict[name]
    return group.sample(n=n)


# 返回值：抽样后的数据框
# print(type(raw_data))
# print(raw_data.head())
# pydata = raw_data.groupby('label')
pydata = raw_data.groupby('label').apply(typicalsamling, typicalNDict)
print(type(pydata))



# pydata.drop(["id","contractAddr"],inplace=True, axis=1)
print(pydata.shape)
print(pydata.columns)
print(pydata.tail())
print(pydata.groups)
pydata.to_csv('tmp2.csv')
pydata.reset_index(inplace=True)

# cpms = ['label', 'AvgCyclomatic','MaxCyclomatic','MaxInheritanceTree','MaxNesting','SumCyclomatic','CountContractCoupled']
# ctms = ['label', 'CountLineCode', 'CountLineCodeExe', 'CountLineComment', 'CountStmt', 'CountLineBlank', 'RatioCommentToCode']
# ooms = ['label', 'CountContractBase', 'CountDependence', 'CountContract', 'CountTotalFunction', 'CountPublicVariable', 'CountVariable',
#        'CountFunctionPrivate', 'CountFunctionInternal',  'CountFunctionExternal', 'CountFunctionPublic']
# lrm = ['label', 'NOI', 'NOL', 'NOSV', 'NOMap', 'NOPay', 'NOE', 'NOMod', 'NOT', 'NOC', 'NODC', 'NOSF', 'SDFB']


experiment_name = setup(data=pydata,
                        target='label',
                        html=False,
                        train_size=0.7, #没有验证集合
                        # feature_selection=True,
                        session_id=1122,
                        fix_imbalance=False,
                        numeric_features=['SDFB']

                        )

compare_models(include=["knn","lr","nb","rf"], round=3,sort='F1')
# # # print(best_model)

# rf = create_model("rf")
# #emrf= ensemble_model(rf)
# tuned_emrf = tune_model(rf,n_iter=100,optimize='F1')
# predict_model(tuned_emrf)

# # tune_model(rf)


