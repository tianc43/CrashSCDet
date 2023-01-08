import os,time,sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir, "ORM"))

from ORM import dbmodules, db
from sqlalchemy.orm import query, scoped_session
from Labeling.EtherscanAPI import EtherscanAPI
from Common.mylogger import logger
from sqlalchemy.sql import text



class LabelSmarContract:
    def __init__(self, dirpath):
        self.rootpath = dirpath

    def initDBofContract(self, session:scoped_session, submitInteral, sleepSec=1):


       
        if session.query(dbmodules.Processing).first():
            logger.warning("wrong")
            return

        for root, dirs, files in os.walk(self.rootpath):
         
            interval:int = 0
            templist = []
            templist_2 = []
            for file in files:
                if file.endswith("txt"):
                    templist.append(dbmodules.Processing(contractAddr=os.path.splitext(file)[0],isprocessed=False))
                    templist_2.append(dbmodules.SmartContract(contractAddr=os.path.splitext(file)[0],label='none'))
                    interval = interval +1
                    if interval % submitInteral ==0: #
                        session.add_all(templist)
                        session.add_all(templist_2)

                        templist = [] #
                        templist_2 = []
                        session.commit() # 
                        session.flush()
                        time.sleep(sleepSec) # 
                        print("sumbit: %d times" %((interval-1) // submitInteral +1))

            if templist:
                session.add_all(templist)
                session.add_all(templist_2)
                session.commit()
                session.flush()
                print("sumbit: %d times" %((interval-1) // submitInteral +1))

    def labelBatchSmartContract(self,session: scoped_session, min_id: int, max_id: int,batchSize:int = 500):
  
        processinglist = session.query(dbmodules.Processing)\
                                            .filter(dbmodules.Processing.id.between(min_id,max_id))\
                                            .filter(dbmodules.Processing.isprocessed == False)\
                                            .limit(batchSize)
        if not processinglist:
            logger.warning("All Smart Contracts Have Been Addressed!")

        #
        SCid: int = 1
        for processing in processinglist:
            print(": %d / %d"%(SCid,batchSize))
            print(processing)
            logger.info("Current Contract:{contract}".format(contract=processing.contractAddr))
            status = self.pullAllTransactionBySmartContract(processing.contractAddr,session=session)
            SCid = SCid + 1


    def pullAllTransactionBySmartContract(self, scAddress,session:scoped_session)->bool:
        
       
        api = EtherscanAPI()
     
        existError: bool = False
        batchSize = 100
        try:
            txList =api.getAllTransactionForContractAddress(scAddress)
            logger.info("TxList for: {address}, length: {length} ".format(address=scAddress,length=len(txList)))
            batchList = []
            errorNumber: int = 0
            # testIndex = 0
            for item in txList:
                # print("testindex :%d" % testIndex)
                # testIndex =testIndex +1
               
                if item['isError'] == "0":
                    continue

                errDescp = ''
                # time.sleep(0.2)
                existError = True
                errDescp = api.getTransactionStatus(item['hash'])['errDescription']

              
                if not item['to'] and item['contractAddress']:
                    item['to'] = item['contractAddress']

               
                batchList.append(
                    dbmodules.ErrorTransactionListForSC(blockNumber=item['blockNumber'],
                                               timeStamp=item['timeStamp'],
                                               hash=item['hash'],
                                               nonce=item['nonce'],
                                               blockHash=item['blockHash'],
                                               transactionIndex=item['transactionIndex'],
                                               fromAddr=item['from'],
                                               toAddr=item['to'],
                                               value=item['value'],
                                               gas=item['gas'],
                                               gasPrice=item['gasPrice'],
                                               isError=item['isError'],
                                               errDescription=errDescp,
                                               txreceipt_status=item['txreceipt_status'],
                                               contractAddress=item['contractAddress'],
                                               comulativeGasUsed=item['cumulativeGasUsed'],
                                               gasUsed=item['gasUsed'],
                                               confirmations=item['confirmations'])
                )

                errorNumber = errorNumber + 1

                if errorNumber % batchSize == 0:  # 
                    # session.add_all(batchList)
                    session.bulk_save_objects(batchList)
                    batchList = []  # 
                    session.commit()  # 
                    session.flush()
                    time.sleep(0.25)  # 
                    logger.info(" |__ TxList for: %s, %d times, at most %d txs/submit."%(scAddress, (errorNumber-1) // batchSize + 1, batchSize))

            # 
            if batchList:
                # session.add_all(batchList)
                session.bulk_save_objects(batchList)
                session.commit()
                session.flush()
                # time.sleep(0.5)
                logger.info(" |__ TxList for: %s, %d times, at most %d txs/submit."%(scAddress, (errorNumber-1) // batchSize + 1, batchSize))
            logger.info(" |__ TxList for: %s, total error transactions: %d." % ( scAddress, errorNumber))

        except Exception as e:
            # 
            logger.error("Contract Address:{address}, Transaction Hash:{txhash}, Error Message:{message}".format(
                address=scAddress,
                txhash=item['hash'],
                message=e
            ))
            return False

        else:
            # 
            session.query(dbmodules.Processing)\
                .filter(dbmodules.Processing.contractAddr == scAddress)\
                .update({"isprocessed":True})
            session.query(dbmodules.SmartContract)\
                    .filter(dbmodules.SmartContract.contractAddr == scAddress)\
                    .update({"label": "1" if existError else '0',
                             "txTotalCount": len(txList),
                             "txErrorTotalCount": errorNumber
                             })
            session.commit()
            session.flush()
            # time.sleep(0.)

            logger.success("Request all txlist of Contract Address:{address} successfully!"
                        .format(address=scAddress))
            return True

    
    def pullAllTransactionBySmartContract_raw(self, scAddress,session:scoped_session)->bool:
       
        
        api = EtherscanAPI()
        
        existError: bool = False

        try:
            txList =api.getAllTransactionForContractAddress(scAddress)
            logger.info("TxList for: {address}, length: {length} ".format(address=scAddress,length=len(txList)))
            errorNumber: int = 0
            # testIndex = 0
            batchSize = 100
            for item in txList:
               
                if item['isError'] == "0":
                    continue

                errDescp = ''
                existError = True
                errDescp = api.getTransactionStatus(item['hash'])['errDescription']

           
                if not item['to'] and item['contractAddress']:
                    item['to'] = item['contractAddress']

                item['fromAddr'] = item['from']
                item['toAddr'] = item['to']
                item["errDescription"] = errDescp
                item['comulativeGasUsed']=item['cumulativeGasUsed']

            

                sql = text("INSERT INTO errTxList (blockNumber,timeStamp,hash,nonce,blockHash,transactionIndex,fromAddr,toAddr,value,gas,gasPrice,isError,errDescription,txreceipt_status,contractAddress,comulativeGasUsed,gasUsed,confirmations)"
                " VALUES (:blockNumber,:timeStamp,:hash,:nonce,:blockHash,:transactionIndex,:fromAddr,:toAddr,:value,:gas,:gasPrice,:isError,:errDescription,:txreceipt_status,:contractAddress,:comulativeGasUsed,:gasUsed,:confirmations)"
                           )
              
                sess.execute(sql, params=item)

                errorNumber = errorNumber + 1

                if errorNumber % batchSize == 0:  # 
                    session.flush()
                    session.commit()  # 
                    time.sleep(0.25)  # 
                    logger.info(" |__ TxList for: %s, %d times, at most %d txs/submit."%(scAddress, (errorNumber-1) // batchSize + 1, batchSize))

            logger.info(" |__ TxList for: %s, total error transactions: %d." % ( scAddress, errorNumber))

        except Exception as e:
           
            logger.error("Contract Address:{address}, Transaction Hash:{txhash}, Error Message:{message}".format(
                address=scAddress,
                txhash=item['hash'],
                message=e
            ))
            return False

        else:
            # 
            session.query(dbmodules.Processing)\
                .filter(dbmodules.Processing.contractAddr == scAddress)\
                .update({"isprocessed":True})
            session.query(dbmodules.SmartContract)\
                    .filter(dbmodules.SmartContract.contractAddr == scAddress)\
                    .update({"label": "1" if existError else '0',
                             "txTotalCount": len(txList),
                             "txErrorTotalCount": errorNumber
                             })
            session.commit()
            session.flush()
            # time.sleep(0.)

            logger.success("Request all txlist of Contract Address:{address} successfully!"
                        .format(address=scAddress))
            return True


if __name__ == '__main__':
    path = "path_to_data"
    lsc = LabelSmarContract(path)
    sess = db.DBOperator().getScopedSession()
    # init 
    # lsc.initDBofContract(session=sess, submitInteral=200)
    #
    #  
    lsc.labelBatchSmartContract(session=sess,min_id=0, max_id=30000, batchSize=5000)
    logger.info("Batch Finished!")

    print("ok")