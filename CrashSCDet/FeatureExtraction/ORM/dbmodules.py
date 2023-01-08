#!usr/bin/env python

from sqlalchemy import Column, String, Integer, Boolean, Float, SmallInteger
from sqlalchemy.types import VARCHAR
from sqlalchemy.ext.declarative import declarative_base

ModuleBase = declarative_base()


class ComplexityMetric(ModuleBase):
    """
    
    """
    __tablename__ = "ComplexityMetric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractAddr = Column(String(64), unique=True, nullable=False)

    # features
    AvgCyclomatic = Column(Float,nullable=True)
    MaxCyclomatic = Column(Float,nullable=True)
    MaxInheritanceTree = Column(Float,nullable=True)
    MaxNesting = Column(Float,nullable=True)
    SumCyclomatic = Column(Float,nullable=True)
    CountContractCoupled = Column(Float,nullable=True)


class CountMetric(ModuleBase):
    """
    
    """
    __tablename__ = "CountMetric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractAddr = Column(String(64), unique=True, nullable=False)

    # features
    # AvgLine = Column(Float,nullable=True)
    # AvgLineCode = Column(Float,nullable=True)
    # AvgLineComment = Column(Float,nullable=True)
    CountLineCode = Column(Float, nullable=True)
    CountLineCodeExe = Column(Float, nullable=True)
    CountLineComment = Column(Float, nullable=True)
    CountStmt = Column(Float, nullable=True)
    CountLineBlank = Column(Float, nullable=True)
    RatioCommentToCode = Column(Float, nullable=True)


class ObjectOrientedMetric(ModuleBase):
    """
    
    """
    __tablename__ = "ObjectOrientedMetric"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contractAddr = Column(String(64), unique=True, nullable=False)

    # features
    CountContractBase = Column(Float,nullable=True)
    CountDependence = Column(Float,nullable=True)
    CountContractCoupled = Column(Float,nullable=True)
    CountContract = Column(Float,nullable=True)
    CountTotalFunction = Column(Float,nullable=True)
    CountPublicVariable = Column(Float,nullable=True)
    CountVariable = Column(Float,nullable=True)
    CountFunctionPrivate = Column(Float,nullable=True)
    CountFunctionInternal = Column(Float,nullable=True)
    CountFunctionExternal = Column(Float,nullable=True)
    CountFunctionPublic = Column(Float,nullable=True)
    MaxInheritanceTree = Column(Float,nullable=True)


class LanguageRelatedMetric(ModuleBase):
    """
    
    """
    __tablename__ = "LanguageRelatedMetric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractAddr = Column(String(64), unique=True, nullable=False)

    # number of interface
    NOI = Column(Float,nullable=True)
    # number of library
    NOL = Column(Float,nullable=True)
    # number of storage variable
    NOSV = Column(Float,nullable=True)
    # number of mapping variables
    NOMap = Column(Float,nullable=True)
    # number of payable
    NOPay = Column(Float,nullable=True)
    # number of events
    NOE = Column(Float,nullable=True)
    # number of modifiers
    NOMod = Column(Float,nullable=True)
    # number of transfer
    NOT = Column(Float,nullable=True)
    # number of call
    NOC = Column(Float,nullable=True)
    # number of delegatecall
    NODC = Column(Float, nullable=True)
    # number of static function
    NOSF = Column(Float,nullable=True)
    # wheter use self-define fall back function
    SDFB =Column(Boolean,nullable=True)


class ProcessingState(ModuleBase):
    """
    
    """
    __tablename__ = "processingstate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    contractAddr = Column(String(256), unique=True, nullable=False)
    
    complexityMetricExtracted = Column(Boolean, default=False, nullable=False)

    
    countMetricExtracted = Column(Boolean,default=False, nullable=False)

    
    objectOrientedMetricExtracted = Column(Boolean,default=False, nullable=False)

    
    languageRelatedMetricExtracted = Column(Boolean,default=False, nullable=False)

    fullyextracted = Column(SmallInteger, default=0, nullable=False)

    solc_versions = Column(String(256), default='', nullable=False)


    def __repr__(self):
        return '%s:(ID: %s, Addr: %s, CPM:%s, CTM:%s, OOM:%s, LRM:%s, FE:%s, Vs:%s)' % (self.__class__.__name__,self.id, self.contractAddr,
                                                                                self.complexityMetricExtracted,
                                                                                 self.countMetricExtracted,
                                                                                 self.objectOrientedMetricExtracted,
                                                                                 self.languageRelatedMetricExtracted,
                                                                                 self.fullyextracted,
                                                                                 self.solc_versions)





