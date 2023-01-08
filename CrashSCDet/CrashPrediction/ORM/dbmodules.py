#!usr/bin/env python

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.types import VARCHAR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

ModuleBase = declarative_base()


class TransactionListForSC(ModuleBase):
    """
    
    """
    __tablename__ = "txList"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 
    blockNumber = Column(Integer)
    timeStamp = Column(String(128))
    hash = Column(String(512))
    nonce = Column(Integer)
    blockHash = Column(String(256))
    transactionIndex = Column(Integer)
    fromAddr = Column(String(256))
    # ,
    #toAddr = Column(String(256), ForeignKey("smartcontract.contractAddr"))
    toAddr = Column(String(256))
    value = Column(String(256))
    gas = Column(String(256))
    gasPrice = Column(String(256))
    isError = Column(Integer)
    # isError = 
    errDescription = Column(String(512), default='', nullable=True)

    txreceipt_status = Column(String(128))
   # input 
    # input = Column(String(512))
    # 
    contractAddress = Column(String(256),default='',nullable=True)
    comulativeGasUsed = Column(String(256))
    gasUsed = Column(String(256))
    confirmations = Column(Integer)


class ErrorTransactionListForSC(ModuleBase):
    """
    
    """
    __tablename__ = "errTxList"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 
    blockNumber = Column(Integer)
    timeStamp = Column(String(128))
    hash = Column(String(512))
    nonce = Column(Integer)
    blockHash = Column(String(256))
    transactionIndex = Column(Integer)
    fromAddr = Column(String(256))
    # ,
    #toAddr = Column(String(256), ForeignKey("smartcontract.contractAddr"))
    toAddr = Column(String(256))
    value = Column(String(256))
    gas = Column(String(256))
    gasPrice = Column(String(256))
    isError = Column(Integer)
    #  = 
    errDescription = Column(String(512), default='', nullable=True)

    txreceipt_status = Column(String(128))
   # input 
    # input = Column(String(512))
    # 
    contractAddress = Column(String(256),default='',nullable=True)
    comulativeGasUsed = Column(String(256))
    gasUsed = Column(String(256))
    confirmations = Column(Integer)


class SmartContract(ModuleBase):
    """
    
    """
    __tablename__ = "smartcontract"
    # 
    contractAddr = Column(String(256),primary_key=True)

    label =Column(String(256),default='none', nullable=False)
    # a set of features to be defined

  
    txTotalCount = Column(Integer,default=0)


    txErrorTotalCount = Column(Integer,default=0)

    # err_types
    label_reverted = Column(String(64),nullable=True)
    label_outofgas = Column(String(64), nullable=True)
    label_badjumpdestination = Column(String(64), nullable=True)
    label_badinstruction = Column(String(64), nullable=True)
    label_outofstack = Column(String(64), nullable=True)


    #
    #txlist = relationship("TransactionListForSC")



class Processing(ModuleBase):
    """
    
    """
    __tablename__ = "processing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 
    contractAddr = Column(String(256), unique=True, nullable=False)
    #  
    isprocessed = Column(Boolean)

    def __repr__(self):
        return '%s:(ID: %s, Addr: %s)' % (self.__class__.__name__,self.id, self.contractAddr)

