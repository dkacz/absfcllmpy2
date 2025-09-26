# initialize.py
import random
from firm import Firm
from consumer import Consumer
from bank import Bank
from etat import Etat
import itertools
from centralBank import CentralBank

class Initialize:
      def __init__(self,ncountry,nconsumer,A,phi,beta,folder,name,run,delta,\
                   taxRatio,\
                   rDiscount,G,\
                   cDisposableIncome,cWealth,liqPref,rDeposit,rBonds,upsilon,\
                   maxPublicDeficit,xiBonds,ls,taxRatioMin,taxRatioMax,gMin,gMax,\
                   w0,wBar,upsilon2):
          self.ncountry=ncountry
          self.nconsumer=nconsumer
          self.A=A 
          self.phi=phi
          self.beta=beta
          self.folder=folder
          self.name=name
          self.run=run
          self.delta=delta
          self.taxRatio=taxRatio
          self.Lcountry=[]
          self.rDiscount=rDiscount
          self.G=G
          self.cDisposableIncome=cDisposableIncome
          self.cWealth=cWealth
          self.liqPref=liqPref 
          self.rDeposit=rDeposit
          self.rBonds=rBonds  
          self.upsilon=upsilon
          self.maxPublicDeficit=maxPublicDeficit 
          self.xiBonds=xiBonds
          self.breaking='no'
          self.ls=ls
          self.taxRatioMin=taxRatioMin
          self.taxRatioMax=taxRatioMax
          self.gMin=gMin
          self.gMax=gMax 
          self.w0=w0
          self.wBar=wBar 
          self.upsilon2=upsilon2
          for i in range(self.ncountry):  
              country=i 
              self.Lcountry.append(country)

      def createConsumer(self):
          self.McountryConsumer={}
          for country in self.Lcountry:
              self.McountryConsumer[country]={}
              for i in range(self.nconsumer):
                  consumeride='C'+str(country)+'n'+str(i)
                  w=1.0 
                  consumer=Consumer(consumeride,country,w,self.beta,self.folder,self.name,
                                    self.run,self.delta,\
                                    self.cDisposableIncome,self.cWealth,self.liqPref,\
                                    self.upsilon,self.rDeposit,self.ls,self.w0,self.wBar,self.upsilon2)
                  consumer.income
                  self.McountryConsumer[country][consumeride]=consumer

      def createBasic(self):
          self.McountryFirm={}
          self.McountryBank={}
          self.McountryFirmMaxNumber={}
          self.McountryBankMaxNumber={}   
          for country in self.Lcountry:
              self.McountryFirm[country]={}
              self.McountryBank[country]={}
              self.McountryFirmMaxNumber[country]=0
              self.McountryBankMaxNumber[country]=0      

      def createEtat(self):
          self.McountryEtat={}
          for country in self.Lcountry:
              sumW=0
              for consumer in self.McountryConsumer[country]:
                  sumW=sumW+self.McountryConsumer[country][consumer].w    
              w=sumW/float(len(self.McountryConsumer[country]))
              e=Etat(country,self.taxRatio,\
                    self.delta,self.G,self.rBonds,\
                     self.maxPublicDeficit,self.xiBonds,\
                   self.taxRatioMin,self.taxRatioMax,self.gMin,self.gMax)
              self.McountryEtat[country]=e

      def createCentralBank(self):
          self.McountryCentralBank={} 
          for country in self.Lcountry:
              bc=CentralBank(country,self.rDiscount,self.rDeposit)
              self.McountryCentralBank[country]=bc

      def debtExplotionStop(self,McountryY,DcumulativeDTBC,t):
           for country in self.Lcountry:
               if McountryY[country]>0:
                  if self.McountryEtat[country].Bonds/McountryY[country]>10.0 and t>100:
                     print
                     print
                     print 
                     print 'DEBT EXPLOTION        DEBT EXPLOTION           DEBT EXPLOTION             DEBT EXPLOTION           DEBT EXPLOTION'
                     print
                     print 'debt/GDP',  self.McountryEtat[country].Bonds/McountryY[country] 
                     print 'stop', stop

      def debtExplotionBreak(self,McountryY,t):
           self.breaking='no' 
           for country in self.Lcountry:
               if McountryY[country]>0:
                  if self.McountryEtat[country].Bonds/McountryY[country]>8.0 and t>400:
                     print
                     print
                     print 
                     print 'DEBT EXPLOTION        DEBT EXPLOTION           DEBT EXPLOTION             DEBT EXPLOTION           DEBT EXPLOTION'
                     print
                     print 'debt/GDP',  self.McountryEtat[country].Bonds/McountryY[country] 
                     self.breaking='yes'
           
               
     
