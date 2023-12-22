

class BasicInformation:
    MainContract = dict()
    with open(r"/home/debian/CrashSCDet/CrashSCDet/FeatureExtraction/tools/ContractMainFile.csv", "r") as f:
        for line in f.readlines():
            MainContract[line.split(",")[0].strip()] = line.split(",")[1].strip()