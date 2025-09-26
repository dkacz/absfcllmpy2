# centralbank.py
from decimal import * 

class CentralBank:
      def __init__(self,country,rDiscount,rDeposit):
          self.country=country 
          self.DepositEtatCentralBank=0
          self.Bonds=0
          self.Reserves=0
          self.loanDiscount=0
          self.LiquidityCentralBank=0      
          self.rDiscount=rDiscount
          self.Mdeposit={} 
          self.Deposit=0
          self.Reserves=0  
          self.profit=0
          self.rDeposit=0.0#rDeposit 
          self.depositInterest=0
          self.pastProfitPos=0
          self.interestLoanDiscount=0 
          self.LoanCentralBankUnion=0
          self.DepositCentralBankUnion=0
          self.DepositUnion=0
          self.CreditTaxCentralBankUnion=0
          self.DebtTaxCentralBankUnion=0
          self.moneyInflow=0
          self.moneyOutflow=0 
          self.pastMoneyInflow=0
          self.pastMoneyOutflow=0
          self.bondRepeymentInflow=0
          self.pastBondRepeymentInflow=0
          self.bondRepeymentOutflow=0
          self.pastBondRepeymentOutflow=0 
          self.diffInflowOutflow=0 
          self.pastDiffInflowOutflow=0
          self.pastDiffBondRepeymentInflowOutflow=0  
          self.diffBondRepeymentInflowOutflow=0

      def checkNetWorth(self):
          Liabilities=self.Reserves+self.DepositEtatCentralBank+self.Deposit+self.profit+self.LoanCentralBankUnion-self.DepositUnion+self.CreditTaxCentralBankUnion
          Assets=self.Bonds+self.loanDiscount+self.LiquidityCentralBank+self.DepositCentralBankUnion+self.profit+self.DebtTaxCentralBankUnion
          if (Liabilities-Assets)/float(Liabilities+Assets)>0.0001 or (Liabilities-Assets)/float(Liabilities+Assets)<-0.0001 or self.Reserves<-0.001:  
             print 'stop', stop
          if self.Deposit<-0.001:
             print 'stop', stop  
          checkDeposit=0   
          for agent in self.Mdeposit:
              checkDeposit=checkDeposit+self.Mdeposit[agent][2]  
          if  self.Deposit<checkDeposit-0.001 or self.Deposit>checkDeposit+0.001:
              print 'stop', stop 
     
      def depositInjection(self,injection,ideAgent):
          self.Mdeposit[ideAgent][2]=self.Mdeposit[ideAgent][2]+injection
          self.Deposit=self.Deposit+injection 
          if self.Deposit<-0.000001:
             print 'stop', stop
 
      def depositWithdrawal(self,reduction,ideAgent):
          self.Mdeposit[ideAgent][2]=self.Mdeposit[ideAgent][2]-reduction
          self.Deposit=self.Deposit-reduction
          if self.Deposit<-0.000001:
             print 'stop', stop 

      def depositVariation(self,variation,ideAgent):
          if variation>=0: 
             self.depositInjection(variation,ideAgent)
          else:
             reduction=-1*variation
             self.depositWithdrawal(reduction,ideAgent)

      def payDepositInterest(self,McountryConsumer,McountryFirm):
          for agent in self.Mdeposit:
              if agent[0]=='C':
                 volume=self.Mdeposit[agent][2]   
                 interest=self.Mdeposit[agent][3]
                 service=volume*interest
                 self.Mdeposit[agent][2]=self.Mdeposit[agent][2]+service
                 self.Deposit=self.Deposit+service
                 McountryConsumer[self.country][agent].Mdeposit[self.country][2]=\
                   McountryConsumer[self.country][agent].Mdeposit[self.country][2]+service
                 McountryConsumer[self.country][agent].depositInterest=\
                   McountryConsumer[self.country][agent].depositInterest+service
              if agent[0]=='F' and McountryFirm[self.country][agent].closing=='yes':
                 print 'stop', stop 
    
      def balancing(self,McountryConsumer,McountryFirm,McountryEtat,CentralBankUnion,DTBC):         
          self.profit=self.interestLoanDiscount-self.depositInterest
          McountryEtat[self.country].Bonds=McountryEtat[self.country].Bonds-self.profit
          self.Bonds=self.Bonds-self.profit 
          Liabilities=self.Reserves+self.DepositEtatCentralBank+self.Deposit+self.profit+self.LoanCentralBankUnion-self.DepositUnion+self.CreditTaxCentralBankUnion
          Assets=self.Bonds+self.loanDiscount+self.LiquidityCentralBank+self.DepositCentralBankUnion+self.profit+self.DebtTaxCentralBankUnion    
          TB=DTBC[self.country] 
          changingLoanCentralBankUnion=0 
          changingDepositCentralBankUnion=0
          self.pastDiffInflowOutflow=self.diffInflowOutflow
          self.diffInflowOutflow=self.moneyInflow-self.moneyOutflow 
          self.pastDiffBondRepeymentInflowOutflow=self.diffBondRepeymentInflowOutflow  
          self.diffBondRepeymentInflowOutflow=self.bondRepeymentInflow-self.bondRepeymentOutflow 
          TB=TB+self.diffInflowOutflow+self.diffBondRepeymentInflowOutflow
          self.pastMoneyInflow=self.moneyInflow
          self.pastMoneyOutflow=self.moneyOutflow
          self.moneyInflow=0
          self.moneyOutflow=0 
          self.pastBondRepeymentInflow=self.bondRepeymentInflow
          self.pastBondRepeymentOutflow=self.bondRepeymentOutflow
          self.bondRepeymentInflow=0
          self.bondRepeymentOutflow=0
          if TB>=0:
             if self.LoanCentralBankUnion>=TB:
                changingLoanCentralBankUnion=-TB
             if self.LoanCentralBankUnion<TB:
                changingLoanCentralBankUnion=-self.LoanCentralBankUnion 
                changingDepositCentralBankUnion=TB-self.LoanCentralBankUnion
          if TB<0:
             if self.DepositCentralBankUnion>=abs(TB):
                changingDepositCentralBankUnion=TB
             if self.DepositCentralBankUnion<abs(TB):
                changingDepositCentralBankUnion=-self.DepositCentralBankUnion
                changingLoanCentralBankUnion=abs(TB)-self.DepositCentralBankUnion
          self.LoanCentralBankUnion=self.LoanCentralBankUnion+changingLoanCentralBankUnion
          self.DepositCentralBankUnion=self.DepositCentralBankUnion+changingDepositCentralBankUnion
          CentralBankUnion.LoanCentralBankUnion=CentralBankUnion.LoanCentralBankUnion+changingLoanCentralBankUnion
          CentralBankUnion.DepositCentralBankUnion=CentralBankUnion.DepositCentralBankUnion+changingDepositCentralBankUnion
          changingCreditTaxCentralBankUnion=0 
          changingDebtTaxCentralBankUnion=0 
          self.CreditTaxCentralBankUnion=self.CreditTaxCentralBankUnion+changingCreditTaxCentralBankUnion
          self.DebtTaxCentralBankUnion=self.DebtTaxCentralBankUnion+changingDebtTaxCentralBankUnion
          CentralBankUnion.CreditTaxCentralBankUnion=CentralBankUnion.CreditTaxCentralBankUnion+changingCreditTaxCentralBankUnion
          CentralBankUnion.DebtTaxCentralBankUnion=CentralBankUnion.DebtTaxCentralBankUnion+changingDebtTaxCentralBankUnion  
          self.interestLoanDiscount=0  
          self.checkNetWorth()

      def checkReserves(self,McountryBank):
          ReservesBank=0
          for bank in McountryBank[self.country]:
              ReservesBank=ReservesBank+McountryBank[self.country][bank].Reserves
          if ReservesBank>self.Reserves+0.01 or ReservesBank<self.Reserves-0.01:
             if len(McountryBank[self.country])>0: 
                print 'stop', stop   

           
 

      
