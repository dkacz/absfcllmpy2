# consumer.py

import csv
import random
import math

class Consumer:
      def __init__(self,ide,country,w,beta,folder,name,run,delta,\
                   cDisposableIncome,cWealth,liqPref,upsilon,rDeposit,ls,w0,wBar,upsilon2):
          self.ide=ide
          self.country=country 
          self.DLA={}
          self.A=0
          self.Afirm=0
          self.Abank=0 
          self.beta=beta
          self.w=w0
          self.Investing=0
          self.Depositing=0 
          self.LConsumptionEff=[]
          self.folder=folder
          self.name=name
          self.run=run
          self.l=0
          self.laborIncome=0 
          self.capitalDismiss=0
          self.DividendShare=0 
          self.pastL=0
          self.delta=delta
          self.ls=ls
          self.Expenditure=0
          self.Import=0
          self.Consumption=0
          self.wmin=0.0
          self.Mdeposit={}
          self.depositIncome=0 
          self.redistribution=0
          self.depositAllocated=0  
          self.wOffered=0
          self.cDisposableIncome=cDisposableIncome 
          self.cWealth=cWealth
          self.liqPref=liqPref 
          self.depositInterest=0       
          self.Deposit=0 
          self.omega=1*random.uniform(0,2*math.pi) 
          self.pastConsumptionIncome=0
          self.ConsumptionIncome=0
          self.wageDemanded=w
          self.totProfit=0 
          self.profitRate=0.0
          self.PastA=0
          self.liqPrefInitial=liqPref
          self.upsilon=upsilon
          self.rDeposit=rDeposit 
          self.wBar=wBar
          self.upsilon2=upsilon2
          self.deltaLabor=self.delta
          self.wageMax=float('inf')
          self.wageMin=0.0
          self.gPhi=0 
          self.memory=8
          self.LpastEmployment=[]
          for i in range(self.memory):
              self.LpastEmployment.append(0) 
          self.memPastEmployment=0   
          #self.LpastEmployment=[0,0,0,0,0,0,0,0,0,0]     
          #self.LpastEmployment=[0,0,0,0]  

      def ordinating(self,p,good,omega,avPrice):
          if p>0 or avPrice>0:
             q=min(abs(self.omega-omega),2*math.pi-abs(self.omega-omega))   
             d=math.sin(q/2.0)
             goodutility=((avPrice)/float(p))*(1/float((d)**self.beta)) 
          if p==0 or avPrice==0:
             goodutility=float('inf')
          if p<=0:
             print 'stop', stop
          return goodutility

      def ordinating0(self,p,good,omega,avPrice):
          if p>0 or avPrice>0:
             q=min(abs(self.omega-omega),2*math.pi-abs(self.omega-omega))   
             d=math.sin(q/2.0)
             goodutility=self.beta*(avPrice/float(p))-(1-self.beta)*d 
          if p==0 or avPrice==0:
             goodutility=float('inf')
          if p<=0:
             print 'stop', stop
          return goodutility

      def profitRateCompute(self):
          if self.PastA>0:
             self.profitRate=self.totProfit/float(self.PastA)
          if self.A<=0:
             self.profit=0.0
          self.totProfit=0 
  
      def income(self,McountryBank,McountryCentralBank):
          self.saving()  
          depositIncome=0
          self.depositIncome=self.depositInterest 
          self.y=self.laborIncome+self.depositIncome+self.DividendShare+self.capitalDismiss
          if self.depositIncome<-0.0001 or self.DividendShare<-0.0001 or self.capitalDismiss<-0.0001 or self.laborIncome<-0.0001\
             or self.innovationIncome<-0.001: 
             print 'stop', stop
          self.capitalDismiss=0
          self.DividendShare=0 
          self.depositInterest=0 
       
      def consumptionDemand(self,McountryBank,McountryCentralBank,DcountryFailureProbability):
          self.PastInvesting=self.Investing
          self.PastDepositing=self.Depositing
          if self.PastInvesting<-0.0001\
             or self.Depositing<-0.00001:
             print 'stop', stop 
          self.Depositing=self.Depositing+self.y  
          self.PastDepositing=self.Depositing 
          self.PastDepositAllocated=self.depositAllocated  
          pastTotalWealth=self.Investing+self.Depositing+self.A+self.redistribution   
          self.DisposableWealth=self.Investing+self.Depositing   
          if self.DisposableWealth<-0.001:
             print 'stop', stop  
          self.PastA=self.A   
          self.Depositing=self.Depositing+self.Investing+self.redistribution
          self.DepositToCheck=self.Depositing
          self.Investing=0       
          self.disposableIncome=0     
          self.reducingA=0
          self.disposableIncome=self.y+self.redistribution 
          self.Depositing=self.Depositing-self.y-self.redistribution
          self.wealth=self.Depositing+self.A
          if self.Depositing<-0.00000001 or self.A<-0.0000001 or self.y<-0.001:    
             print 'stop', stop  
          self.savingIncome=0 
          desiredConsumption=self.cDisposableIncome*self.disposableIncome+self.cWealth*self.Depositing  
          if  desiredConsumption<=self.disposableIncome+self.Depositing:     
              self.Consumption=desiredConsumption
              if desiredConsumption<self.disposableIncome:
                 self.savingIncome=self.disposableIncome-desiredConsumption
          if  desiredConsumption>self.disposableIncome+self.Depositing:
              self.Consumption=self.disposableIncome+self.Depositing
          self.Depositing=self.Depositing+self.disposableIncome-self.Consumption
          self.wealthAfterConsumption=self.Depositing+self.A
          if self.wealthAfterConsumption<-0.0000000001:
             print 'stop', stop
          self.profitRateCompute()  
          self.computeLiquidityPreference(DcountryFailureProbability)
          self.desiredA=max(self.A,(1-self.liqPref)*(self.A+self.Depositing))
          self.Depositing=self.Depositing-(self.desiredA-self.A)        
          if self.desiredA>-0.000001 and self.desiredA<0:
             self.desiredA=0  
          if  self.Depositing<-0.0001:
             print 'stop', stop
          self.Investing=self.desiredA-self.A  
          self.totalWealth=self.Investing+self.Depositing+self.A+self.Consumption  
          self.depositAllocation(McountryBank,McountryCentralBank)
          if self.A+self.Investing<self.desiredA-0.001 or self.A+self.Investing>self.desiredA+0.001:
             print 'stop', stop  
          if self.totalWealth<pastTotalWealth-0.001 or   self.totalWealth>pastTotalWealth+0.001:
             print 'stop', stop
          if self.A<-0.000001 or self.Investing<-0.0000001 or self.Depositing<-0.000001 or self.desiredA<-0.000001 or self.reducingA<-0.000001:
             print 'stop', stop
          
      def computeLiquidityPreference(self,DcountryFailureProbability):
          liq=self.liqPrefInitial
          if (self.profitRate*(1-DcountryFailureProbability[self.country])-self.rDeposit)>0 and self.A>0.0:
             self.liqPref=liq*math.exp(-1.0*(self.profitRate*(1-DcountryFailureProbability[self.country])-self.rDeposit))
          if (self.profitRate*(1-DcountryFailureProbability[self.country])-self.rDeposit)<=0 and self.A>0.0:
             self.liqPref=liq
          if self.A<=0:
             self.liqPref=liq
          if self.liqPref>=1.0:      
             self.liqPref=1.0
          if self.liqPref<=0.0:      
             self.liqPref=0.0  

      def depositAllocation(self,McountryBank,McountryCentralBank):
          Lbank=[] 
          for bank in self.Mdeposit:
              Lbank.append(bank)
          ideBank=Lbank[0]
          self.Deposit=self.Mdeposit[ideBank][2]
          if ideBank!=self.country:
             depositInBank=McountryBank[self.country][ideBank].Mdeposit[self.ide][2]
          if ideBank==self.country:
             depositInBank=McountryCentralBank[self.country].Mdeposit[self.ide][2] 
          if  self.DepositToCheck<self.Deposit-0.01 or  self.DepositToCheck>self.Deposit+0.01:
              print 'stop', stop
          if  depositInBank<self.Deposit-0.001 or  depositInBank>self.Deposit+0.001:
              print 'stop', stop 
          if  self.Deposit<-0.001:
              print 'stop', stop 
          newDeposit=self.Investing+self.Depositing+self.Consumption
          depositVariation=newDeposit-self.Deposit 
          self.Mdeposit[ideBank][2]=self.Mdeposit[ideBank][2]+depositVariation
          if ideBank!=self.country:
             McountryBank[self.country][ideBank].depositVariation(depositVariation,self.ide,McountryCentralBank)   
          if ideBank==self.country:
             McountryCentralBank[self.country].depositVariation(depositVariation,self.ide)  
             if len(self.Mdeposit)>1:
                print 'stop', stop      
          self.Deposit=self.Deposit+depositVariation
          if  self.Deposit<-0.0000001:
              print 'stop', stop    

      def saving(self):
          self.Depositing=self.Depositing+(self.Consumption-self.Expenditure)
          self.wealthAfterEffectiveConsumption=self.Depositing+self.A
          if self.Consumption-self.Expenditure<-0.001:
             print 'stop', stop

      def ownershipCheck(self,McountryBank):
          self.A=0
          self.Afirm=0
          self.Abank=0  
          for firm in self.DLA:
              if firm[0]=='F':
                 self.Afirm=self.Afirm+self.DLA[firm][2]
              if firm[0]=='B':
                 self.Abank=self.Abank+self.DLA[firm][2] 
                 if McountryBank[self.country][firm].Downer[self.ide][2]>self.DLA[firm][2]+0.000001 and\
                    McountryBank[self.country][firm].Downer[self.ide][2]<self.DLA[firm][2]-0.000001: 
                    print 'stop', stop
              self.A=self.A+self.DLA[firm][2]
          Lbank=[] 
          for bank in self.Mdeposit:
              Lbank.append(bank)
          ideBank=Lbank[0]
          self.Deposit=self.Mdeposit[ideBank][2]

      def laborSupply1(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL):
          self.pastWage=self.wageDemanded  
          unemploymentVariation=0 
          if McountryPastUnemployement[self.country]>0:
             unemploymentVariation=(McountryUnemployement[self.country]\
                               -McountryPastUnemployement[self.country])#/McountryPastUnemployement[self.country]
          productivityVariation=0
          if McountryPastYL[self.country]>0: 
             productivityVariation=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country]
          ratioUnemployment=0 
          if self.ls>0:
             ratioUnemployment=(self.ls-self.l)/self.ls
          if self.l<self.ls:
             d=-self.delta
          if self.l>=self.ls:
             d=self.delta
          u=McountryUnemployement[self.country]  
          self.wageDemanded=self.wageDemanded*(1-0.03*ratioUnemployment+productivityVariation-0.1*(u-0.04))
          #if self.wageDemanded>self.pastWage:
          #   a=random.uniform(0,1) 
          #    
          #   if a>self.upsilon2*math.exp(-u*self.upsilon):
          #      self.wageDemanded=self.pastWage     
          if self.wageDemanded<1:
             self.wageDemanded=1  
          if self.wageDemanded>self.pastWage*(1+0.03):
             self.wageDemanded=self.pastWage*(1+0.03) 
          if self.wageDemanded<self.pastWage*(1-0.03):
             self.wageDemanded=self.pastWage*(1-0.03)
          if self.ide=='C0n0':
             print
             print 'self.ide', self.ide
             print 'self.wageDemanded', self.wageDemanded
             print 'self.pastWage', self.pastWage
             print 'ratioUnemployment', ratioUnemployment
             print 'unemploymentVariation', unemploymentVariation
             print 'productivityVariation', productivityVariation
             print 'd', d
             print 'self.l', self.l
             print 'self.ls', self.ls 
             #print 'self.upsilon2*math.exp(-u*self.upsilon)', self.upsilon2*math.exp(-u*self.upsilon)
             #print 'a', a


      def laborSupply(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL):
          #if self.laborSupplyAlreadyRevised=='no':
             u=McountryUnemployement[self.country]
             self.wageDirection=0 
             self.pastWage=self.wageDemanded 
             g=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country]
             a=random.uniform(0,1)
             #self.upsilon=1.0 
             direction='stay'
             upsilonConsumer=self.upsilon2#0.75 
             if self.l<self.ls:# and g<=0:
                   #direction='down'    
                   if a<upsilonConsumer*math.exp(-1*(u*self.upsilon)):
                   #if a>u*self.upsilon*upsilonConsumer:
                      direction='stay'
                   else:
                      direction='down'#'stay'
             if self.l>=self.ls:
                #direction='up'
                   if a<upsilonConsumer*math.exp(-1*(u*self.upsilon)):# and self.gPhi>0:
                   #if a>u*self.upsilon*upsilonConsumer:
                      direction='up'
                   else:
                      direction='stay'#'stay'
             if direction=='up':
                Umin=self.wageDemanded
                Umax=self.wageDemanded*(1+self.deltaLabor)
                self.wP=random.uniform(Umin,Umax)
                self.wageDemanded=self.wP 
             if direction=='down':
                Umin=self.wageDemanded
                Umax=self.wageDemanded*(1-self.deltaLabor)
                self.wP=random.uniform(Umin,Umax)
                self.wageDemanded=self.wP  
             if self.wageDemanded<self.wageMin:
                self.wageDemanded=self.wageMin
             if self.wageDemanded>self.wageMax:
                self.wageDemanded=self.wageMax
             if self.ide=='C0n0':
                print
                print 'self.ide', self.ide
                print 'self.wageDemanded', self.wageDemanded
                print 'self.pastWage', self.pastWage
                print 'self.l', self.l
                print 'self.ls', self.ls
                print 'a', a  
                print 'math.exp(-u*self.upsilon)', math.exp(-u*self.upsilon)
                print a<math.exp(-u*self.upsilon) 
                print 'self.gPhi', self.gPhi  
                print 'g', g
                print 'direction', direction


      def laborSupply4(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL):
          #if self.laborSupplyAlreadyRevised=='no':
             u=McountryUnemployement[self.country]
             self.wageDirection=0 
             self.pastWage=self.wageDemanded 
             g=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country]
             a=random.uniform(0,1)
             del self.LpastEmployment[0] 
             if self.l<self.ls:# and g<=0:
                self.LpastEmployment.append(0)
             if self.l>=self.ls:# and g<=0:
                self.LpastEmployment.append(1)
             sumLpastEmployment=sum(self.LpastEmployment)
             #memory=4      
             if sumLpastEmployment==0:# and g<=0:
                direction='down'#'stay'
             #if sumLpastEmployment<self.memory:# and g<=0:
             #   direction='down'#'stay' 
             #   if a<self.upsilon2*math.exp(-u*self.upsilon):# and self.gPhi>0:
             #         direction='stay'
             #   else:
             #         direction='down'#'stay' 
             if sumLpastEmployment>0 and sumLpastEmployment<self.memory:# and g<=0:
                direction='stay'#'stay'
                #if a<self.upsilon2*math.exp(-u*self.upsilon):# and self.gPhi>0:
                #      direction='up'
                #else:
                #      direction='stay'#'stay'
             if sumLpastEmployment>=self.memory:# and g<=0:
                #direction='up'#'stay'    
                if a<self.upsilon2*math.exp(-u*self.upsilon):# and self.gPhi>0:
                      direction='up'
                else:
                      direction='stay'#'stay'    
             if direction=='up':
                Umin=self.wageDemanded
                Umax=self.wageDemanded*(1+self.deltaLabor)
                self.wP=random.uniform(Umin,Umax)
                self.wageDemanded=self.wP 
             if direction=='down':
                Umin=self.wageDemanded
                Umax=self.wageDemanded*(1-self.deltaLabor)
                self.wP=random.uniform(Umin,Umax)
                self.wageDemanded=self.wP  
             if self.wageDemanded<1.0:#self.wageMin:
                self.wageDemanded=1.0#self.wageMin
             if self.wageDemanded>self.wageMax:
                self.wageDemanded=self.wageMax
             if self.ide=='C0n0':
                print
                print 'self.ide', self.ide
                print 'self.wageDemanded', self.wageDemanded
                print 'self.pastWage', self.pastWage
                print 'self.l', self.l
                print 'self.ls', self.ls
                print 'a', a  
                print 'self.upsilon2*math.exp(-u*self.upsilon)', self.upsilon2*math.exp(-u*self.upsilon)
                print a<self.upsilon2*math.exp(-u*self.upsilon) 
                print 'self.gPhi', self.gPhi  
                print 'g', g
                print 'direction', direction
                print 'self.LpastEmployment', self.LpastEmployment 
             
      def laborSupply5(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL):
          #if self.laborSupplyAlreadyRevised=='no':
             u=McountryUnemployement[self.country]
             self.wageDirection=0 
             self.pastWage=self.wageDemanded 
             g=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country]
             a=random.uniform(0,1)
             b=random.uniform(0,1)
             #del self.LpastEmployment[0] 
             self.memPastEmployment=0.8*self.memPastEmployment+0.2*self.l/float(self.ls)   
             #if self.l<self.ls:# and g<=0:
             #   self.LpastEmployment.append(0)
             #if self.l>=self.ls:# and g<=0:
             #   self.LpastEmployment.append(1)
             #sumLpastEmployment=sum(self.LpastEmployment)
             #memory=4    
             if self.memPastEmployment<0.7:
                direction='down' 
             #if b>self.memPastEmployment and self.memPastEmployment>=0.2:# and g<=0:
             #   direction='stay'#'stay'
             #if sumLpastEmployment<self.memory:# and g<=0:
             #   direction='down'#'stay' 
             #if sumLpastEmployment>0 and sumLpastEmployment<self.memory:# and g<=0:
             #   direction='stay'#'stay'
                #if a<self.upsilon2*math.exp(-u*self.upsilon):# and self.gPhi>0:
                #      direction='up'
                #else:
                #      direction='stay'#'stay'
             #if b<=self.memPastEmployment and self.memPastEmployment>=0.2:# and g<=0:
             if self.memPastEmployment>=0.7:
                #direction='up'#'stay'    
                if a<self.upsilon2*math.exp(-u*self.upsilon):# and self.gPhi>0:
                      direction='up'
                else:
                      direction='stay'#'stay'    
             if direction=='up':
                Umin=self.wageDemanded
                Umax=self.wageDemanded*(1+self.deltaLabor)
                self.wP=random.uniform(Umin,Umax)
                self.wageDemanded=self.wP 
             if direction=='down':
                Umin=self.wageDemanded
                Umax=self.wageDemanded*(1-self.deltaLabor)
                self.wP=random.uniform(Umin,Umax)
                self.wageDemanded=self.wP  
             if self.wageDemanded<1.0:#self.wageMin:
                self.wageDemanded=1.0#self.wageMin
             if self.wageDemanded>self.wageMax:
                self.wageDemanded=self.wageMax
             if self.ide=='C0n0':
                print
                print 'self.ide', self.ide
                print 'self.wageDemanded', self.wageDemanded
                print 'self.pastWage', self.pastWage
                print 'self.l', self.l
                print 'self.ls', self.ls
                print 'a', a  
                print 'self.upsilon2*math.exp(-u*self.upsilon)', self.upsilon2*math.exp(-u*self.upsilon)
                print a<self.upsilon2*math.exp(-u*self.upsilon) 
                print 'self.gPhi', self.gPhi  
                print 'g', g
                print 'direction', direction
                #print 'self.LpastEmployment', self.LpastEmployment 
                print 'self.memPastEmployment', self.memPastEmployment
                print 'b', b     
        
      def write(self,t):
         nameWrite=self.folder+'/'+self.name+'Consumer.csv'
         c=open(nameWrite,'a')  
         C=[self.run, self.ide,t,self.country,self.omega,self.l, self.A,self.y,self.Consumption,self.Investing,self.Expenditure]  
         writer = csv.writer(c)
         writer.writerow(C)
         c.close()

      def orderBankDeposit(self):
          self.LbankDeposit=[]
          for bank in self.Mdeposit:
              self.LbankDeposit.append(bank)

      def paying(self,payment,McountryBank,McountryCentralBank):
          LbankDeposit=[]
          for bank in self.Mdeposit:
              LbankDeposit.append(bank)
          random.shuffle(LbankDeposit)
          for bank in LbankDeposit:
                 volumeDeposit=self.Mdeposit[bank][2]
                 reduction=payment
                 if bank!=self.country: 
                    volumeCheck=McountryBank[self.country][bank].Mdeposit[self.ide][2]
                 if bank==self.country: 
                    volumeCheck=McountryCentralBank[self.country].Mdeposit[self.ide][2]
                 if volumeDeposit<volumeCheck-0.00001 or volumeDeposit>volumeCheck+0.00001:
                    print 'stop', stop
                 self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction
                 if bank!=self.country:
                    McountryBank[self.country][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank)
                 if bank==self.country:
                    McountryCentralBank[self.country].depositWithdrawal(reduction,self.ide)
   
      def receiving(self,payment,McountryBank,McountryCentralBank):
          LbankDeposit=[]
          for bank in self.Mdeposit:
              LbankDeposit.append(bank)   
          random.shuffle(LbankDeposit)
          ideBank=LbankDeposit[0]
          volumeDeposit=self.Mdeposit[ideBank][2]  
          if ideBank!=self.country:
             volumeCheck=McountryBank[self.country][ideBank].Mdeposit[self.ide][2]
          if ideBank==self.country:
             volumeCheck=McountryCentralBank[self.country].Mdeposit[self.ide][2]  
          if volumeDeposit<volumeCheck-0.00001 or volumeDeposit>volumeCheck+0.00001:     
             print 'stop', stop
          self.Mdeposit[ideBank][2]=self.Mdeposit[ideBank][2]+payment
          if ideBank!=self.country:
             McountryBank[self.country][ideBank].depositInjection(payment,self.ide,McountryCentralBank)
          if ideBank==self.country:
             McountryCentralBank[self.country].depositInjection(payment,self.ide) 
             if len(LbankDeposit)>1:
                print 'stop', stop
                  
     
