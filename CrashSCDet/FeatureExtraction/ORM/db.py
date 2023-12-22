import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__),os.path.pardir,"common"))

from common.allConfigures import Allconfiguration
import sqlalchemy
from sqlalchemy.orm import session, sessionmaker,scoped_session
from .dbmodules import *
from sqlalchemy.pool import QueuePool
# import pandas as pd



class DBOperator:
    def __init__(self):
        self.username = Allconfiguration.configures_json['username']
        self.password = Allconfiguration.configures_json['password']
        self.host = Allconfiguration.configures_json['host']
        self.database = Allconfiguration.configures_json['database']
        self.poolsize = Allconfiguration.configures_json['poolsize']
        engine = self.__create_engine()
        self.session_factory: sessionmaker = sessionmaker(bind=engine, autocommit=False)
        # thread safety(each thread only has a unique session)
        self.scoppedSession: scoped_session = scoped_session(self.session_factory)
        # test session


    def __create_engine(self):
        # ref to {https://www.cnblogs.com/jackadam/p/8727409.html}
        dburl = "mysql+mysqlconnector://{username}:{password}@{host}/{database}".format(username=self.username,password=self.password,host=self.host,database=self.database)
        # pool_size = 10  # 连接池的大小，0表示连接数无限制
        # pool_recycle = -1  # 连接池回收连接的时间，如果设置为-1，表示没有no timeout, 注意，mysql会自动断开超过8小时的连接，所以sqlalchemy沿用被mysql断开的连接会抛出MySQL has gone away
        # max_overflow = -1  # 连接池中允许‘溢出’的连接个数，如果设置为-1，表示连接池中可以创建任意数量的连接
        # pool_timeout = 30  # 在连接池获取一个空闲连接等待的时间
        # echo = False  # 如果设置True, Engine将会记录所有的日志，日志默认会输出到sys.stdout
        # pool_pre_ping = True

        engine = sqlalchemy.create_engine(dburl, pool_size=self.poolsize,
                                          max_overflow=10,
                                          pool_timeout=30,
                                          pool_pre_ping=True,
                                          poolclass=QueuePool)
        # create all related tables
        ModuleBase.metadata.create_all(engine)
        return engine

    def getNewSession(self):
        """
        return a new session when called
        :return:
        """
        return self.session_factory()

    def getScopedSession(self)->scoped_session:
        """
        return a thread-safety session, which means one thread has only one session
        :return:
        """
        return self.scoppedSession()



    # def executor_rawsql(self,sql:str)->pd.DataFrame:
    #     """
    #     pull data from a table using specific sql string
    #     :param sql:
    #     :return:
    #     """
    #     try:
    #         df= pd.read_sql(str)
    #     except Exception as ex:
    #         print("execute sql error")
    #
    #     return df




if __name__ == '__main__':
    session = DBOperator().getScopedSession()
    result = session.query(ProcessingState).all()
    if result:
        print("obtain results")
        print(result)
    else:
        print("empty")
