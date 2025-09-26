# consumer.py

import csv
import random
from  policy import * 

class Etat:
      def __init__(self,country,taxRate,delta,G,rBonds,\
                   maxPublicDeficit,xiBonds,taxRatioMin,taxRatioMax,gMin,gMax):
          self.country=country   
          self.taxRate=taxRate
          self.taxCollectedConsumer=0
          self.taxCollectedFirm=0
          self.taxCollectedBank=0        
          self.delta=delta
          self.G=G 
          self.initialG=G
          self.LiquidityEtat=0
          self.rBonds=rBonds
          self.Bonds=0.0
          self.Salvatage=0
          self.endTransitionTime=1
          self.maxPublicDeficit=maxPublicDeficit
          self.startingTime=0 
          self.xiBonds=xiBonds 
          self.taxCollectedBank=0
          self.taxCollectedFirm=0
          self.interestExpenditure=0
          self.addingSurplus=0 
          self.adjust='no' 
          self.pastBonds=0
          self.bondsAllocated=0  
          self.bondsCB=0
          self.desiredG=self.G
          self.taxCollectedImponibleBank=0
          self.taxCollectedImponibleFirm=0
          self.taxCollectedImponibleConsumer=0
          self.taxCollectedImponible=0
          self.followingTaxRate=self.taxRate 
          self.surplusEtat=0 
          self.inheritedLiquidity=0 
          self.pastTaxCollected=0.0 
          self.taxRatioMin=taxRatioMin
          self.taxRatioMax=taxRatioMax
          self.gMin=gMin
          self.gMax=gMax
          self.labPolicy='no'   
          self.whichPolicy='nn'

      def taxationConsumer(self,McountryConsumer,McountryBank,McountryCentralBank):
          self.taxCollectedConsumer=0
          self.taxCollectedImponibleConsumer=0
          for consumer in McountryConsumer[self.country]:
              McountryConsumer[self.country][consumer].taxes=0 
              if McountryConsumer[self.country][consumer].y>0.0: 
                 taxable=McountryConsumer[self.country][consumer].y
                 self.taxCollectedImponibleConsumer=self.taxCollectedImponibleConsumer+taxable
                 taxVolume=self.taxRate*taxable 
                 self.taxCollectedConsumer=self.taxCollectedConsumer+self.taxRate*taxable
                 McountryConsumer[self.country][consumer].taxes=self.taxRate*taxable
                 McountryConsumer[self.country][consumer].y=McountryConsumer[self.country][consumer].y-self.taxRate*taxable
                 McountryConsumer[self.country][consumer].paying(taxVolume,McountryBank,McountryCentralBank)
                 self.LiquidityEtat=self.LiquidityEtat+taxVolume
                 McountryCentralBank[self.country].DepositEtatCentralBank=McountryCentralBank[self.country].DepositEtatCentralBank+taxVolume                
                 if taxVolume<-0.000001:
                    print 'stop', stop 
                 if McountryConsumer[self.country][consumer].y<-0.00001:
                    print 'stop', stop  
         
      def taxationFirm(self,McountryFirm,McountryBank,McountryCentralBank):
          self.taxCollectedFirm=0  
          self.taxCollectedImponibleFirm=0
          for firm in McountryFirm[self.country]:
              if McountryFirm[self.country][firm].profit>0.0000000001 and McountryFirm[self.country][firm].closing=='no': 
                 self.taxCollectedFirm=self.taxCollectedFirm+self.taxRate*McountryFirm[self.country][firm].profit
                 McountryFirm[self.country][firm].netProfit=(1-self.taxRate)*McountryFirm[self.country][firm].profit
                 pastA=McountryFirm[self.country][firm].A 
                 McountryFirm[self.country][firm].A=McountryFirm[self.country][firm].A-self.taxRate*McountryFirm[self.country][firm].profit
                 taxVolume=self.taxRate*McountryFirm[self.country][firm].profit
                 McountryFirm[self.country][firm].paying(taxVolume,McountryBank,McountryCentralBank) 
                 newA=McountryFirm[self.country][firm].A
                 self.taxCollectedImponibleFirm=self.taxCollectedImponibleFirm+McountryFirm[self.country][firm].profit
                 self.LiquidityEtat=self.LiquidityEtat+taxVolume
                 McountryCentralBank[self.country].DepositEtatCentralBank=McountryCentralBank[self.country].DepositEtatCentralBank+taxVolume  

      def taxationBank(self,McountryBank,McountryCentralBank):
          self.taxCollectedBank=0  
          self.taxCollectedImponibleBank=0
          for bank in McountryBank[self.country]:
              if McountryBank[self.country][bank].profit>0.0000000001 and McountryBank[self.country][bank].closing=='no': 
                 self.taxCollectedBank=self.taxCollectedBank+self.taxRate*McountryBank[self.country][bank].profit
                 McountryBank[self.country][bank].netProfit=(1-self.taxRate)*McountryBank[self.country][bank].profit
                 McountryBank[self.country][bank].A=McountryBank[self.country][bank].A-self.taxRate*McountryBank[self.country][bank].profit
                 reduction=self.taxRate*McountryBank[self.country][bank].profit    
                 taxVolume=reduction      
                 McountryBank[self.country][bank].reserveWithdrawal(reduction,McountryCentralBank) 
                 self.LiquidityEtat=self.LiquidityEtat+taxVolume
                 self.taxCollectedImponibleBank=self.taxCollectedImponibleBank+McountryBank[self.country][bank].profit
                 McountryCentralBank[self.country].DepositEtatCentralBank=McountryCentralBank[self.country].DepositEtatCentralBank+taxVolume 

      def expectingTaxation(self,McountryConsumer,McountryCentralBank,McountryUnemployement):
          self.bondsRepayments=self.Bonds        
          rBonds=self.rBonds
          McountryCentralBank[self.country].Bonds=0
          self.Bonds=0
          self.profitCB=0 
          self.pastInterestExpenditure=self.interestExpenditure
          self.interestExpenditure=0
          McountryCentralBank[self.country].pastProfitPos=0   
          if  McountryCentralBank[self.country].profit>0:
              self.profitCB=McountryCentralBank[self.country].profit
              McountryCentralBank[self.country].pastProfitPos=McountryCentralBank[self.country].profit        
          self.expectedTaxCollected=0
          for consumer in McountryConsumer[self.country]:
              self.expectedTaxCollected=self.expectedTaxCollected+McountryConsumer[self.country][consumer].y*self.taxRate
          self.expectedTaxCollected=self.expectedTaxCollected+self.profitCB+self.taxCollectedFirm+self.taxCollectedBank
          
      def effectiveTaxation(self):
          self.taxCollected=self.taxCollectedFirm+self.taxCollectedConsumer+self.taxCollectedBank+self.profitCB
          self.taxCollectedImponible=self.taxCollectedImponibleBank+self.taxCollectedImponibleFirm+self.taxCollectedImponibleConsumer
          self.publicDeficit=self.realG+self.pastInterestExpenditure-self.taxCollected+self.Salvatage 
          self.taxRate=self.followingTaxRate 
          if self.taxCollected>self.expectedTaxCollected+0.001 or self.taxCollected<self.expectedTaxCollected-0.001:
             print 'stop', stop

      def governmentPlannedExpenditure(self,McountryConsumer,McountryFirm,McountryCentralBank,\
                                McountryAvPrice,McountryY,t,DcountryAverageWage,policyKind,\
                               DTBC,McountryUnemployement,DglobalPhi):
          if self.startingTime<self.endTransitionTime:
             self.realG=1.0*McountryAvPrice[self.country]*DglobalPhi[self.country]*self.initialG
             self.G=1.0*McountryAvPrice[self.country]*DglobalPhi[self.country]*self.initialG    
          if self.startingTime>=self.endTransitionTime: 
             self.pastNominalY=McountryY[self.country]
             self.pastAvWage=DcountryAverageWage[self.country]                   
             desiredG=min(McountryAvPrice[self.country]*DglobalPhi[self.country]*self.initialG,self.gMax*McountryY[self.country])
             desiredG=max(desiredG,self.gMin*McountryY[self.country])  
             self.desiredG=desiredG 
             self.pastTaxCollected=self.taxCollected 
             if self.adjust=='no' and  McountryY[self.country]>0:
                expectedDeficit=self.publicDeficit/McountryY[self.country]
                maxPublicDeficit=self.maxPublicDeficit
                if desiredG<=self.G and expectedDeficit>=maxPublicDeficit:
                   self.realG=self.G*(1-random.uniform(0,self.delta))
                   self.followingTaxRate=self.taxRate*(1+random.uniform(0,self.delta))
                if desiredG>self.G and expectedDeficit>=maxPublicDeficit:
                   self.realG=self.G
                   self.followingTaxRate=self.taxRate*(1+random.uniform(0,self.delta))
                if desiredG<=self.G and expectedDeficit<maxPublicDeficit:
                   self.realG=self.G*(1-random.uniform(0,self.delta))
                   self.followingTaxRate=self.taxRate*(1-random.uniform(0,self.delta))   
                if desiredG>self.G and expectedDeficit<maxPublicDeficit:
                   self.realG=self.G*(1+random.uniform(0,self.delta))              
                   self.followingTaxRate=self.taxRate
             if self.followingTaxRate>=self.taxRatioMax:
                self.followingTaxRate=self.taxRatioMax
             if self.followingTaxRate<=self.taxRatioMin:
                self.followingTaxRate=self.taxRatioMin         
             self.G=self.realG  
          if self.realG<self.initialG:
             self.realG=self.initialG    
             self.G=self.initialG
          if self.realG<0:
             self.realG=0    
          self.startingTime=self.startingTime+1 
          self.expenditure=self.realG+self.bondsRepayments
          McountryCentralBank[self.country].profit=0
          publicDeficit=self.realG+self.pastInterestExpenditure-self.expectedTaxCollected+self.Salvatage
          self.inheritedLiquidity=self.LiquidityEtat
          if self.LiquidityEtat>self.surplusEtat+self.taxCollectedFirm+self.taxCollectedBank+0.001 or\
             self.LiquidityEtat<self.surplusEtat+self.taxCollectedFirm+self.taxCollectedBank-0.001:
             print 'stop', stop   
          deficitSecondary=self.bondsRepayments+self.realG-self.surplusEtat-self.expectedTaxCollected+self.profitCB 
          self.deficitSecondaryExpected=deficitSecondary
          if deficitSecondary>0:
             self.bondsSupply=deficitSecondary 
             self.surplusEtat=0 
          if deficitSecondary<=0:     
             self.bondsSupply=0
             self.surplusEtat=-1*deficitSecondary 
          if  McountryY[self.country]>0:
              self.leverage=self.bondsSupply/float(McountryY[self.country])
          if  McountryY[self.country]==0:
              self.leverage=0.0#float('inf')      
          self.Consumption=self.realG
          self.rBonds=McountryCentralBank[self.country].rDiscount
          if McountryY[self.country]>0.01:  
             self.rBonds=self.xiBonds*(self.bondsSupply/float(McountryY[self.country]))+McountryCentralBank[self.country].rDiscount           
          if self.LiquidityEtat<-0.0001:
             print 'stop', stop
    
      def bondsToCentralBank(self,McountryCentralBank):  
          if self.bondsSupply>self.bondsAllocated:     
             self.bondsCB=self.bondsSupply-self.bondsAllocated
             McountryCentralBank[self.country].Bonds=self.bondsCB
             McountryCentralBank[self.country].DepositEtatCentralBank=McountryCentralBank[self.country].DepositEtatCentralBank+self.bondsCB
             self.LiquidityEtat=self.LiquidityEtat+self.bondsCB#McountryCentralBank[self.country].basicMoney
          self.Bonds=self.bondsSupply
          self.pastBonds=self.Bonds
          self.LiquidityEtat=self.LiquidityEtat-self.bondsRepayments # paying back previous debt
          McountryCentralBank[self.country].DepositEtatCentralBank=McountryCentralBank[self.country].DepositEtatCentralBank-self.bondsRepayments 
         
      def redistributionConsumer(self,McountryConsumer,McountryBank,McountryCentralBank,McountryAvPrice,t):
             self.effectiveTaxation() 
             #if self.LiquidityEtat<-0.01 or self.LiquidityEtat+self.expenditure<self.realG-0.00001:
             #   print 'stop', stop      
             self.Redistribution=0#self.LiquidityEtat               
             redistributionConsumer=(self.realG)/float(len(McountryConsumer[self.country]))
             for consumer in McountryConsumer[self.country]:  
                 McountryConsumer[self.country][consumer].redistribution=redistributionConsumer           
                 self.Redistribution=self.Redistribution+McountryConsumer[self.country][consumer].redistribution
                 payment=McountryConsumer[self.country][consumer].redistribution
                 McountryConsumer[self.country][consumer].receiving(payment,McountryBank,McountryCentralBank)            
             self.LiquidityEtat=self.LiquidityEtat-self.Redistribution
             McountryCentralBank[self.country].DepositEtatCentralBank=McountryCentralBank[self.country].DepositEtatCentralBank-self.Redistribution
              #if self.LiquidityEtat<-0.01:
              #  print 'stop', stop   
              
      def coveringDeposit(self,ammount,McountryCentralBank):
          McountryCentralBank[self.country].Bonds=McountryCentralBank[self.country].Bonds+ammount
          self.Bonds=self.Bonds+ammount 
          self.coveredDeposit=self.coveredDeposit+ammount   

     

                             
      


           
              
      
               
