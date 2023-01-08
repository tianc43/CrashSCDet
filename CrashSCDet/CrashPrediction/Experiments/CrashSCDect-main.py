
from imblearn.base import SamplerMixin
import pandas as pd
import numpy as np
from imblearn.over_sampling import RandomOverSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, cross_validate
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

np.random.seed(seed=1122)  #

pydata = pd.read_csv("path_to_data")
#
to_deleted_features = ["id","contractAddr"]
pydata.drop(to_deleted_features,inplace=True, axis=1)
print(pydata.shape)



file = open("CrashSCDect_perforance_results.csv","w")
file.write("classifier,f1,auc\n")

def store_results(method_name:str, f1_resuts, auc_results):
        print("%s performance: f1:%s auc:%s" % (method_name,np.mean(f1_resuts), np.mean(auc_results)))
        for i in range(len(f1_resuts)):
                file.write(method_name+","+str(f1_resuts[i])+","+str(auc_results[i])+"\n")


folds =0
for folds in range(10):
        print("Folds: %s"%(folds))

        # 
        sampled = RandomOverSampler(random_state=folds)
        X_sampled,Y_sampled = sampled.fit_resample(pydata.drop(['label'], axis=1), pydata['label'])

        print(X_sampled.shape)
        print(Y_sampled.shape)
        strKFold = StratifiedKFold(n_splits=10, shuffle=True, random_state=folds)
        scoring = ['roc_auc', 'f1']



        rf = RandomForestClassifier()
        results_rf = cross_validate(
                rf,
                X=X_sampled,
                y=Y_sampled,
                cv=strKFold,
                scoring=scoring,
                return_train_score=False)
        # print(results.keys())
        print( "CrashSCDect performance: f1:%s auc:%s"%( np.mean(results_rf['test_f1']), np.mean(results_rf['test_roc_auc']) ))
        store_results("CrashSCDect", results_rf['test_f1'],results_rf['test_roc_auc'])

  

file.close()
print("finished.")

