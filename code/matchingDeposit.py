#matchingcredit.py
import random

class MatchingDeposit:
      def __init__(self,Lcountry):
         self.DinCentralBank={} 
         for country in Lcountry:
             self.DinCentralBank[country]='zero'

      def creatingAccount(self,McountryConsumer,McountryFirm,McountryBank,McountryCentralBank):
          for country in McountryConsumer:
              Lbank=[]
              for bank in McountryBank[country]:
                  Lbank.append(bank)
              if len(McountryBank[country])>0 and self.DinCentralBank[country]=='no':    
                 for consumer in McountryConsumer[country]:
                     if len(McountryConsumer[country][consumer].Mdeposit)==0: 
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideConsumer=consumer
                        interestRate=McountryBank[country][ideBank].rDeposit 
                        deposit=0  
                        McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country]   
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit 
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit            
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                     elif (country in McountryConsumer[country][consumer].Mdeposit)==True: 
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideConsumer=consumer
                        interestRate=McountryBank[country][ideBank].rDeposit 
                        deposit=McountryConsumer[country][consumer].Mdeposit[country][2]
                        del McountryConsumer[country][consumer].Mdeposit[country]
                        del McountryCentralBank[country].Mdeposit[ideConsumer]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                        McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country] 
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit 
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit                
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                 for firm in McountryFirm[country]:
                     if len(McountryFirm[country][firm].Mdeposit)==0: 
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideFirm=firm
                        interestRate=McountryBank[country][ideBank].rDeposit 
                        deposit=McountryFirm[country][firm].A 
                        McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]   
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit 
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit               
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]
                     elif (country in McountryFirm[country][firm].Mdeposit)==True:
                          if  len(McountryFirm[country][firm].Mdeposit)==1:
                              random.shuffle(Lbank)
                              ideBank=Lbank[0]
                              ideFirm=firm
                              interestRate=McountryBank[country][ideBank].rDeposit 
                              deposit=McountryFirm[country][firm].Mdeposit[country][2]
                              del McountryCentralBank[country].Mdeposit[ideFirm]
                              del McountryFirm[country][firm].Mdeposit[country]
                              McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                              McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]  
                              McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                              McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit  
                              McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit                 
                              McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]  
                          else:    
                              for bank in self.LbankDeposit:
                                  if bank!=country:
                                     ideBank=bank
                                     ideFirm=firm
                                     interestRate=McountryBank[country][ideBank].rDeposit 
                                     deposit=McountryFirm[country][firm].Mdeposit[country][2]
                                     del McountryCentralBank[country].Mdeposit[ideFirm]
                                     del McountryFirm[country][firm].Mdeposit[country]
                                     McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                                     McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]  
                                     McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                                     McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit 
                                     McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit                     
                                     McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country] 
                     McountryFirm[country][firm].orderBankDeposit(McountryBank)
              if len(McountryBank[country])>0 and self.DinCentralBank[country]=='yes': 
                 for consumer in McountryConsumer[country]:
                     if (country in McountryConsumer[country][consumer].Mdeposit)==True:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideConsumer=consumer
                        interestRate=McountryBank[country][ideBank].rDeposit 
                        deposit=McountryConsumer[country][consumer].Mdeposit[country][2]
                        if deposit<McountryCentralBank[country].Mdeposit[ideConsumer][2]-0.00001 or\
                           deposit>McountryCentralBank[country].Mdeposit[ideConsumer][2]+0.00001:
                           print 'stop', stop          
                        del McountryConsumer[country][consumer].Mdeposit[country]
                        del McountryCentralBank[country].Mdeposit[ideConsumer]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                        McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country] 
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit                 
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                        McountryConsumer[country][ideConsumer].orderBankDeposit()
                 for firm in McountryFirm[country]:                   
                     if (country in McountryFirm[country][firm].Mdeposit)==True: 
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideFirm=firm
                        interestRate=McountryBank[country][ideBank].rDeposit 
                        deposit=McountryFirm[country][firm].Mdeposit[country][2]
                        if deposit<McountryCentralBank[country].Mdeposit[ideFirm][2]-0.00001 or\
                           deposit>McountryCentralBank[country].Mdeposit[ideFirm][2]+0.00001:
                           print 'stop', stop
                        del McountryCentralBank[country].Mdeposit[ideFirm]
                        del McountryFirm[country][firm].Mdeposit[country]
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit-deposit
                        McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]  
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit                   
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]   
                        if interestRate<-0.00001:
                           print 'stop', stop   
                     else:
                        random.shuffle(Lbank)
                        ideBank=Lbank[0]
                        ideFirm=firm
                        interestRate=McountryBank[country][ideBank].rDeposit 
                        deposit=McountryFirm[country][firm].A
                        McountryBank[country][ideBank].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]  
                        McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                        McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit 
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+deposit                
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country]                                             
                     McountryFirm[country][firm].orderBankDeposit(McountryBank)
              if len(McountryBank[country])==0:
                 self.DinCentralBank[country]='yes'     
                 for consumer in McountryConsumer[country]:
                     if len(McountryConsumer[country][consumer].Mdeposit)==0:
                        ideBank=country
                        ideConsumer=consumer
                        interestRate=McountryCentralBank[country].rDeposit 
                        deposit=0                  
                        McountryCentralBank[country].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country] 
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit+deposit             
                        McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country] 
                        McountryConsumer[country][ideConsumer].orderBankDeposit()
                 for firm in McountryFirm[country]:
                     if len(McountryFirm[country][firm].Mdeposit)==0:
                        ideBank=country 
                        ideFirm=firm
                        interestRate=McountryCentralBank[country].rDeposit
                        deposit=McountryFirm[country][firm].A 
                        McountryCentralBank[country].Mdeposit[ideFirm]=[ideFirm,ideBank,deposit,interestRate,country]                 
                        McountryFirm[country][ideFirm].Mdeposit[ideBank]=[ideFirm,ideBank,deposit,interestRate,country] 
                        McountryCentralBank[country].Deposit=McountryCentralBank[country].Deposit+deposit
                     McountryFirm[country][firm].orderBankDeposit(McountryBank)

      def allocatingConsumerDeposit(self,McountryConsumer,McountryBank):
          self.MdepositSupply={}
          self.MdepositDemand={}     
          for country in McountryBank:            
              if len(McountryBank[country])>1 and self.DinCentralBank[country]=='no':                                
                 self.extractingDeposit(McountryConsumer,McountryBank,country)
                 self.matchDeposit(McountryConsumer,McountryBank,country) 
                 if self.createdReserves>self.delatedReserves+0.00001 or self.createdReserves<self.delatedReserves-0.00001:
                    print 'stop', stop       
              if len(McountryBank[country])>0:
                 self.DinCentralBank[country]='no'      

      def extractingDeposit(self,McountryConsumer,McountryBank,country):
              self.delatedReserves=0 
              self.MdepositDemand[country]=[]
              self.MdepositSupply[country]=[] 
              for consumer in McountryConsumer[country]:
                  if len(McountryConsumer[country][consumer].Mdeposit)>1:
                     print 'stop', stop
                  for ideBank in McountryConsumer[country][consumer].Mdeposit: 
                      deposit=McountryConsumer[country][consumer].Mdeposit[ideBank][2]               
                  del McountryBank[country][ideBank].Mdeposit[consumer]
                  McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit-deposit
                  McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves-deposit 
                  self.delatedReserves=self.delatedReserves+deposit  
                  McountryConsumer[country][consumer].Mdeposit 
                  McountryConsumer[country][consumer].Mdeposit={}
                  McountryConsumer[country][consumer].depositAllocated=0
                  depositSupply=[McountryConsumer[country][consumer].ide,deposit]
                  McountryConsumer[country][consumer].Depositing
                  self.MdepositSupply[country].append(depositSupply)
              for bank in McountryBank[country]: 
                  depositDemand=[McountryBank[country][bank].ide,McountryBank[country][bank].rDeposit]
                  self.MdepositDemand[country].append(depositDemand) 

      def matchDeposit(self,McountryConsumer,McountryBank,country):
              self.createdReserves=0
              for depositSupply in self.MdepositSupply[country]: 
                  random.shuffle(self.MdepositDemand[country]) 
                  depositDemand=self.MdepositDemand[country][0]
                  ideConsumer=depositSupply[0] 
                  deposit=depositSupply[1]
                  ideBank=depositDemand[0]
                  interestRate=depositDemand[1]
                  McountryConsumer[country][ideConsumer].Mdeposit[ideBank]=[ideConsumer,ideBank,deposit,interestRate,country]
                  McountryBank[country][ideBank].Mdeposit[ideConsumer]=[ideConsumer,ideBank,deposit,interestRate,country] 
                  McountryBank[country][ideBank].Deposit=McountryBank[country][ideBank].Deposit+deposit
                  McountryBank[country][ideBank].Reserves=McountryBank[country][ideBank].Reserves+deposit 
                  self.createdReserves=self.createdReserves+deposit 
                   
                  
                  
                      
      
                              
                             
       

