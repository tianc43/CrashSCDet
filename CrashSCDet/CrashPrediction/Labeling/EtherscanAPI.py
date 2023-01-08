import requests
from Common import allConfigures
import os,time


class EtherscanAPI:

    def __init__(self):

        self.api_key = allConfigures.Allconfiguration.configures_json['api_key']


    def getAllTransactionForContractAddress(self,smartContractAddr)->list:
       
        # url = "https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=asc&apikey={api_key}"
        url = "http://api-cn.etherscan.com/api?module=account&action=txlist&address={scAddr}&sort=asc&apikey={api_key}"
        r = requests.get(url.format(scAddr=smartContractAddr, api_key=self.api_key))

        txlists: list = []
        # ok
        assert r.status_code == 200

        txlists: list = r.json()['result']
            
        return txlists


    def getTransactionStatus(self,txHash)->dict:
        """
        :param txHash: hash
        :return: dict{'isError':str, 'errDescription':str}
        """
        url = "https://api-cn.etherscan.com/api?module=transaction&action=getstatus&txhash={txhash}&apikey={api_key}"

        rs = requests.get(url.format(txhash=txHash, api_key=self.api_key))
        assert rs.status_code == 200
        result: dict = rs.json()['result']

        return result


if __name__ == '__main__':
    # path = "path_to_data"
    # for root,dirs,file in os.walk(path):
    #     for dirname in dirs:
    #         print(dirname)

    
    print(len(EtherscanAPI().getAllTransactionForContractAddress("0x0000000000013949f288172bd7e36837bddc7211")))



