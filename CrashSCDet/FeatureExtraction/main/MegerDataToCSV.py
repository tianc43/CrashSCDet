import pandas as pd
import pymysql


"""
将抽取特征的数据库与标记合约的数据库中的结果进行合并
"""
class MergerData:

    # 抽取特征的数据库
    featureConnStrs: dict = {
        "host":"localhost",
        "user":"root",
        "password":"1234",
        "database":"crashfeatureextraction"
    }

    # 标记合约是否含有缺陷的数据库
    labelConnStrs: dict ={
        "host": "localhost",
        "user": "root",
        "password": "1234",
        "database": "crashprediction"
    }

    def _getdbconn(self)->dict:
        #  用DBAPI构建数据库链接engine
        # 返回两个数据库的连接
        feature_con = pymysql.connect(host=self.featureConnStrs['host'], user=self.featureConnStrs['user'],  password=self.featureConnStrs['password'],
                                      database=self.featureConnStrs['database'])
        label_con = pymysql.connect(host=self.labelConnStrs['host'], user= self.labelConnStrs['user'], password= self.labelConnStrs['password'],
                                    database = self.labelConnStrs['database'])
        return {'feature_con':feature_con, 'label_con':label_con}

    def get_all_related_tables(self,target_size= 60000):
        """
        从两个数据库中获得相应的数据表中的数据
        :TODO  当前通过明确指定的相应的数据来进行筛选数据，后期可以考虑通过传参自动化完成
        """
        # 首先需要根据两个数据库中，计算出被正确抽取特征，同时也被正确的标记crash列表的合约集合
        # 然后从符合的合约记录中，将所有相关的特征和相关的标签进行合并

        # target_size = 10000
        # 1. 所有的合约都已经被成功标记了，但是有部分合约还不能被成功编译，以此，仅以编译成功的合约作为参考的合约
        con: dict = self._getdbconn()
        # 不考虑没有transaction 的合约
        contract_state = pd.read_sql("select `contractAddr` from smartcontract where txTotalCount>0 limit %s"%(target_size), con=con['label_con'])
        # 不考虑没有标记成功的合约
        feature_processing_state = pd.read_sql("select `contractAddr` from processingstate where fullyextracted=1 limit %s "%(target_size), con=con['feature_con'])
        print(contract_state.shape)
        print(feature_processing_state.shape)

        mergered = pd.merge(feature_processing_state, contract_state, how="inner", left_on="contractAddr", right_on="contractAddr")
        # 选取适合的数据量
        targeted = mergered[0:target_size][['contractAddr']]

        # 2. 根据符合条件的合约地址，从表中抽取对应的合约标签和对应的指标特征
        # 2.1 抽取标签
        labels = pd.read_sql("select `contractAddr`, `label` from smartcontract", con=con['label_con'])
        labels_merged = pd.merge(left=targeted,right=labels,how="inner",on="contractAddr")

        # 2.2 抽取各个类别的指标 Complexity metrics； CountMetric ; ObjectOrientedMetric; LanguageRelatedMetric
        cpm_features = pd.read_sql("select * from complexitymetric", con=con['feature_con']).drop("id",axis=1)
        ctm_features = pd.read_sql("select * from countmetric", con=con['feature_con']).drop("id",axis=1)
        # 去掉重复的特征
        oom_features = pd.read_sql("select * from objectorientedmetric", con=con['feature_con']).drop(["id","CountContractCoupled","MaxInheritanceTree"],axis=1)
        lrm_features = pd.read_sql("select * from languagerelatedmetric", con=con['feature_con']).drop("id",axis=1)

        #合并所有结果
        results = pd.merge(labels_merged, cpm_features, how="inner", on="contractAddr")
        results = pd.merge(results, ctm_features,how="inner", on="contractAddr")
        results = pd.merge(results, oom_features, how="inner", on="contractAddr")
        results = pd.merge(results, lrm_features, how="inner", on="contractAddr")

        print(results.shape)
        print(results.columns)

        print(results[results['label'] == '1'].shape)
        print(results[results['label'] == '0'].shape)

        # 将结果存到csv文件中
        results.to_csv("results-all-remove-zero-transaction.csv",index_label="id")


        con['label_con'].close()
        con['feature_con'].close()


if __name__ == '__main__':
    instance = MergerData()
    # 所有标记过，并且抽取过指标的合约
    # [注意]： 这里需要移除 没有tx的合约
    instance.get_all_related_tables(target_size=60000)
