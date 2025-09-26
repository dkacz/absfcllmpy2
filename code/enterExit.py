2#enterExit.py

import random
from firm import Firm
from bank import Bank

class enterExit:
      def __init__(self,Lcountry,McountryFirmMaxNumber,\
                   folder,name,run,\
                   delta,initialA,McountryBankMaxNumber,probBank,minReserve,\
                   rDiscount,xi,dividendRate,iota,rDeposit,\
                   upsilon,gamma,deltaInnovation,mu1,\
                   propTradable,Fcost,ni,minMarkUp,iotaE,theta,sigma,upsilon2,jobDuration):
          self.Lcountry=Lcountry
          self.McountryFirmMaxNumber=McountryFirmMaxNumber
          self.folder=folder
          self.name=name
          self.run=run
          self.ni=ni
          self.upsilon=upsilon 
          self.delta=delta
          self.initialA=initialA
          self.initialPhi=1.0
          self.initialWage=1.0
          self.initialPrice=1.0
          self.DminBankSizePast={}
          self.DmaxBankSizePast={}
          self.bound=10 
          self.upsilon2=upsilon2 
          for country in Lcountry:
              self.DminBankSizePast[country]=4*self.initialA
              self.DmaxBankSizePast[country]=4*self.initialA
          self.McountryBankMaxNumber=McountryBankMaxNumber
          self.probBank=probBank 
          self.minReserve=minReserve
          self.rDeposit=rDeposit
          self.xi=xi 
          self.dividendRate=dividendRate
          self.initialProbBank=self.probBank
          self.iota=iota 
          self.rDiscount=rDiscount
          self.gamma=gamma
          self.deltaInnovation=deltaInnovation
          self.mu1=mu1
          self.propTradable=propTradable 
          self.DcountryFirmEnter={}
          self.Fcost=Fcost
          self.minMarkUp=minMarkUp 
          self.iotaE=iotaE 
          self.theta=theta
          self.sigma=sigma
          self.DcountryFirmEnterTradable={}
          for country in self.Lcountry:
              self.DcountryFirmEnter[country]=0
              self.DcountryFirmEnterTradable[country]=0
          self.DcountryFirmExit={}
          self.DcountryFirmExitTradable={}  
          for country in self.Lcountry:
              self.DcountryFirmExit[country]=0
              self.DcountryFirmExitTradable[country]=0
          self.DcountryBankEnter={}
          for country in self.Lcountry:
              self.DcountryBankEnter[country]=0
          self.DcountryBankExit={}
          for country in self.Lcountry:
              self.DcountryBankExit[country]=0
          self.DcountryAverageWage={} 
          for country in self.Lcountry:
              self.DcountryAverageWage[country]=1.0  
          self.DcountryFirmGone={} 
          self.DcountryBankGone={} 
          self.DcountryForeignBankLosses={}  
          self.DcountryEnterValue={}
          self.DcountryUpsilon={}
          self.DcountryJobDuration={}  
          self.DcountryIotaRelPhi={}
          for country in self.Lcountry:
              self.DcountryFirmGone[country]={}
              self.DcountryBankGone[country]={}
              self.DcountryForeignBankLosses[country]=0  
              self.DcountryEnterValue[country]=0
              self.DcountryUpsilon[country]=self.upsilon
              self.DcountryJobDuration[country]=jobDuration
              self.DcountryIotaRelPhi[country]=self.iota 
          
      def minMaxAgents(self,McountryFirm,McountryBank,country,McountryAvPrice):
          LbankSize=[]
          for bank in McountryBank[country]:
              LbankSize.append(McountryBank[country][bank].A)
          if len(LbankSize)>0:
             self.minBankSize=min(LbankSize)
             self.maxBankSize=max(LbankSize)
             self.medianBankSize=LbankSize[int(len(LbankSize)/2.0)]
          if len(LbankSize)==0:
             if McountryAvPrice[country]>0:
                self.minBankSize=self.DminBankSizePast[country]
                self.maxBankSize=self.DmaxBankSizePast[country]
                self.medianBankSize=self.initialA*McountryAvPrice[country]
             if McountryAvPrice[country]<=0:
                self.minBankSize=self.initialA
                self.maxBankSize=self.initialA 
                self.medianBankSize=self.initialA   
          self.minBankSizePast=self.DminBankSizePast[country] 
          self.maxBankSizePast=self.DmaxBankSizePast[country]          
          self.DminBankSizePast[country]=self.minBankSize 
          self.DmaxBankSizePast[country]=self.maxBankSize          
          LfirmSizeNotTradable=[]
          LfirmPhiNotTradable=[] 
          LfirmPriceNotTradable=[]
          LfirmWageNotTradable=[]
          LfirmExNotTradable=[]
          sumW=0
          sumL=0
          sumQ=0 
          sumQNotTradable=0
          sumQTradable=0 
          for firm in McountryFirm[country]:
              sumW=sumW+McountryFirm[country][firm].w
              sumL=sumL+McountryFirm[country][firm].l
              sumQ=sumQ+McountryFirm[country][firm].xSold#Lsold[2]
              if McountryFirm[country][firm].tradable=='no':
                 LfirmSizeNotTradable.append(McountryFirm[country][firm].A)
                 LfirmExNotTradable.append(McountryFirm[country][firm].mind.xE)
                 LfirmPhiNotTradable.append(McountryFirm[country][firm].phi) 
                 LfirmPriceNotTradable.append(McountryFirm[country][firm].price)#Lselling[0]) 
                 LfirmWageNotTradable.append(McountryFirm[country][firm].w)  
                 sumQNotTradable=sumQNotTradable+McountryFirm[country][firm].xSold#Lsold[2]
          self.averageWage=1.0       
          if sumL>0:
             self.averageWage=sumW/float(sumL)       
          if len(LfirmSizeNotTradable)>0:
             self.minFirmSizeNotTradable=min(LfirmSizeNotTradable)
             self.maxFirmSizeNotTradable=max(LfirmSizeNotTradable)
             self.minFirmExNotTradable=min(LfirmExNotTradable)
             self.maxFirmExNotTradable=max(LfirmExNotTradable)
             self.medianFirmExNotTradable=LfirmExNotTradable[int(len(LfirmExNotTradable)/2.0)] 
             self.medianFirmSizeNotTradable=LfirmSizeNotTradable[int(len(LfirmSizeNotTradable)/2.0)]
             self.minFirmPhiNotTradable=min(LfirmPhiNotTradable)
             self.maxFirmPhiNotTradable=max(LfirmPhiNotTradable)
             self.medianFirmPhiNotTradable=LfirmPhiNotTradable[int(len(LfirmPhiNotTradable)/2.0)]
             self.minFirmPriceNotTradable=min(LfirmPriceNotTradable)
             self.maxFirmPriceNotTradable=max(LfirmPriceNotTradable)
             self.medianFirmPriceNotTradable=LfirmPriceNotTradable[int(len(LfirmPriceNotTradable)/2.0)]  
             self.meanFirmPriceNotTradable=sum(LfirmPriceNotTradable)/len(LfirmPriceNotTradable)          
             self.minFirmWageNotTradable=min(LfirmWageNotTradable)
             self.maxFirmWageNotTradable=max(LfirmWageNotTradable) 
             self.medianFirmWageNotTradable=LfirmWageNotTradable[int(len(LfirmWageNotTradable)/2.0)]
          if len(LfirmSizeNotTradable)==0:
             self.minFirmSizeNotTradable=self.initialA
             self.maxFirmSizeNotTradable=self.initialA
             self.minFirmExNotTradable=self.initialA
             self.maxFirmExNotTradable=self.initialA  
             self.medianFirmExNotTradable=self.initialA
             self.medianFirmSizeNotTradable=self.initialA
             self.minFirmPhiNotTradable=self.initialPhi
             self.maxFirmPhiNotTradable=self.initialPhi
             self.medianFirmPhiNotTradable=self.initialPhi
             self.minFirmPriceNotTradable=self.initialPrice
             self.maxFirmPriceNotTradable=self.initialPrice
             self.meanFirmPriceNotTradable=self.initialPrice
             self.medianFirmPriceNotTradable=self.initialPrice
             self.minFirmWageNotTradable=self.initialWage
             self.maxFirmWageNotTradable=self.initialWage
             self.medianFirmWageNotTradable=self.initialWage
          LfirmSizeTradable=[]
          LfirmExTradable=[] 
          LfirmPhiTradable=[] 
          LfirmPriceTradable=[]
          LfirmWageTradable=[]          
          for firm in McountryFirm[country]:
              if McountryFirm[country][firm].tradable=='yes':
                 LfirmSizeTradable.append(McountryFirm[country][firm].A)
                 LfirmExTradable.append(McountryFirm[country][firm].mind.xE)
                 LfirmPhiTradable.append(McountryFirm[country][firm].phi) 
                 LfirmPriceTradable.append(McountryFirm[country][firm].price)#Lselling[0]) 
                 LfirmWageTradable.append(McountryFirm[country][firm].w)
                 sumQTradable=sumQTradable+McountryFirm[country][firm].xSold#Lsold[2]
          if len(LfirmSizeTradable)>0:
             self.minFirmSizeTradable=min(LfirmSizeTradable)
             self.maxFirmSizeTradable=max(LfirmSizeTradable)
             self.minFirmExTradable=min(LfirmExTradable)
             self.maxFirmExTradable=max(LfirmExTradable)
             self.medianFirmExTradable=LfirmExTradable[int(len(LfirmExTradable)/2.0)]
             self.medianFirmSizeTradable=LfirmSizeTradable[int(len(LfirmSizeTradable)/2.0)]
             self.minFirmPhiTradable=min(LfirmPhiTradable)
             self.maxFirmPhiTradable=max(LfirmPhiTradable) 
             self.medianFirmPhiTradable=LfirmPhiTradable[int(len(LfirmPhiTradable)/2.0)]
             self.minFirmPriceTradable=min(LfirmPriceTradable)
             self.maxFirmPriceTradable=max(LfirmPriceTradable)
             self.medianFirmPriceTradable=LfirmPriceTradable[int(len(LfirmPriceTradable)/2.0)]
             self.meanFirmPriceTradable=sum(LfirmPriceTradable)/len(LfirmPriceTradable)
             self.minFirmWageTradable=min(LfirmWageTradable)
             self.maxFirmWageTradable=max(LfirmWageTradable) 
             self.medianFirmWageTradable=LfirmWageTradable[int(len(LfirmWageTradable)/2.0)]
          if len(LfirmSizeTradable)==0:
             self.minFirmSizeTradable=self.initialA
             self.maxFirmSizeTradable=self.initialA
             self.minFirmExTradable=self.initialA
             self.maxFirmExTradable=self.initialA
             self.medianFirmExTradable=self.initialA
             self.medianFirmSizeTradable=self.initialA
             self.minFirmPhiTradable=self.initialPhi
             self.maxFirmPhiTradable=self.initialPhi
             self.medianFirmPhiTradable=self.initialPhi
             self.minFirmPriceTradable=self.initialPrice
             self.maxFirmPriceTradable=self.initialPrice
             self.medianFirmPriceTradable=self.initialPrice
             self.meanFirmPriceTradable=self.initialPrice 
             self.minFirmWageTradable=self.initialWage
             self.maxFirmWageTradable=self.initialWage 
             self.medianFirmWageTradable=self.initialWage      
          self.avQ=0
          self.avQNotTradable=0  
          self.avQTradable=0 
          if len(McountryFirm[country])>0:
             self.avQ=sumQ/float(len(McountryFirm[country]))
          if len(LfirmSizeTradable)>0:
             self.avQTradable=sumQTradable/float(len(LfirmSizeTradable))
          if len(LfirmSizeNotTradable)>0:
             self.avQNotTradable=sumQNotTradable/float(len(LfirmSizeNotTradable))

      def whichSize(self,kind):
          if kind=='firmNotTradable':
             price=self.whichPrice('firmNotTradable')
             phi=self.whichPhi('firmNotTradable')
             wage=self.whichWage('firmNotTradable') 
             size=max(self.initialA,wage,random.uniform(self.minFirmSizeNotTradable,self.maxFirmSizeNotTradable))
             eX=self.whichEx('firmNotTradable',phi,price,wage) 
             Lkind=[kind,size,phi,price,wage,eX]  
          if kind=='firmTradable':
             price=self.whichPrice('firmTradable')
             phi=self.whichPhi('firmTradable')
             wage=self.whichWage('firmTradable') 
             size=max(self.initialA,wage,random.uniform(self.minFirmSizeTradable,self.maxFirmSizeTradable))
             eX=self.whichEx('firmTradable',phi,price,wage) 
             Lkind=[kind,size,phi,price,wage,eX] 
          if kind=='bank':
             size=random.uniform(self.minBankSizePast,self.maxBankSizePast)   
             sizeMin=max(self.sigma*self.medianFirmSizeNotTradable,4*self.medianFirmSizeTradable,self.minBankSizePast) 
             size=random.uniform(sizeMin,self.maxBankSizePast)
             Lkind=[kind,size] 
          return Lkind             
                 
      def whichPhi(self,kind):
          if kind=='firmNotTradable':
             phi=random.uniform(self.minFirmPhiNotTradable,self.maxFirmPhiNotTradable)
          if kind=='firmTradable':
             phi=random.uniform(self.minFirmPhiTradable,self.maxFirmPhiTradable)
          return phi
          
      def whichPrice(self,kind):
          if kind=='firmNotTradable':
             price=random.uniform(self.minFirmPriceNotTradable,self.maxFirmPriceNotTradable)
          if kind=='firmTradable':
             price=random.uniform(self.minFirmPriceTradable,self.maxFirmPriceTradable)
          return price
          
      def whichWage(self,kind):
          if kind=='firmNotTradable':
             wage=random.uniform(self.minFirmWageNotTradable,self.maxFirmWageNotTradable)
          if kind=='firmTradable':
             wage=random.uniform(self.minFirmWageTradable,self.maxFirmWageTradable)
          return wage   

      def whichEx(self,kind,phi,p,wage):
          if kind=='firmNotTradable': 
             xE=random.uniform(self.minFirmExNotTradable,self.maxFirmExNotTradable)
          if kind=='firmTradable':
             xE=random.uniform(self.minFirmExTradable,self.maxFirmExTradable)
          return xE   

      def whichAgentEnter6(self,country,McountryFirm,McountryBank):
          nBank=len(McountryBank[country])
          newAgent='no'
          ABank=0
          for bank in McountryBank[country]:
              ABank=ABank+McountryBank[country][bank].A
          AFirm=0
          for firm in McountryFirm[country]:
              AFirm=AFirm+McountryFirm[country][firm].A    
          nFirm=len(McountryFirm[country])
          nBank=len(McountryBank[country])
          if nFirm>0:
             ratioBankFirm=ABank/float(AFirm)
             rationBankFirmNumber=nBank/float(nFirm)
          if nFirm==0:
             ratioBankFirm=1   
             rationBankFirmNumber=1  
          if ratioBankFirm<self.initialProbBank or rationBankFirmNumber<self.initialProbBank:
             #if country==0: 
             newAgent='bank'
          if ratioBankFirm>=self.initialProbBank and  rationBankFirmNumber>=self.initialProbBank:
          #if  rationBankFirmNumber<self.initialProbBank:
          #   #if country==0: 
          #   newAgent='bank'
          #if  rationBankFirmNumber>=self.initialProbBank:
             a=random.uniform(0,1)
             if a<self.propTradable:
                newAgent='firmTradable'
             else:
                newAgent='firmNotTradable'  
          return newAgent   
       

      def enter(self,McountryConsumer,McountryFirm,time,McountryBank,McountryCentralBank,McountryAvPrice,McountryEtat):
          enteringfirm=0
          enteringbank=0
          for country in McountryConsumer: 
              self.DcountryEnterValue[country]=0  
              totalInvesting=0 
              LconsumerInvesting=[]
              LconsumerAsset=[]
              self.DcountryFirmEnter[country]=0
              self.DcountryFirmEnterTradable[country]=0 
              self.DcountryBankEnter[country]=0
              enteringfirmC=0
              pos=0  
              sumL=0
              sumW=0
              for consumer in McountryConsumer[country]:
                  sumL=sumL+McountryConsumer[country][consumer].l
                  sumW=sumW+McountryConsumer[country][consumer].wOffered
              avWage=1.0
              if sumL>0:
                 avWage=sumW/float(sumL)   
              lenPartecipation=self.bound
              for consumer in McountryConsumer[country]:
                  if McountryConsumer[country][consumer].Investing>McountryConsumer[country][consumer].wBar*avWage\
                     and len(McountryConsumer[country][consumer].DLA)<=lenPartecipation:
                     totalInvesting=totalInvesting+McountryConsumer[country][consumer].Investing
                     LconsumerInvesting.append([McountryConsumer[country][consumer].ide,McountryConsumer[country][consumer].Investing,0,0,pos])                    
                  pos=pos+1   
              self.minMaxAgents(McountryFirm,McountryBank,country,McountryAvPrice)
              newAgentKind=self.whichAgentEnter6(country,McountryFirm,McountryBank)
              Lkind=self.whichSize(newAgentKind)
              newAgentSize=Lkind[1]
              random.shuffle(LconsumerInvesting)   
              i=0
              li=len(LconsumerInvesting)
              sumInv=0
              basicJ=0   
              self.DidEnterANewAgent='no'
              wmin=0
              while i<li:
                    if self.DidEnterANewAgent=='yes':
                       self.DidEnterANewAgent='no'
                       newAgentKind=self.whichAgentEnter6(country,McountryFirm,McountryBank)
                       Lkind=self.whichSize(newAgentKind)
                       newAgentSize=Lkind[1]
                       if sumInv>0.001:
                          print 'stop', stop    
                    sumInv=sumInv+LconsumerInvesting[i][1]							    
                    if sumInv>=newAgentSize:
                       if newAgentKind=='firmNotTradable' or newAgentKind=='firmTradable':
                          if newAgentKind=='firmNotTradable':
                             newfirmA=Lkind[1] 
                             number=self.McountryFirmMaxNumber[country]
                             self.McountryFirmMaxNumber[country]=number+1
                             firmide='F'+str(country)+'n'+str(number)  
                             phi=Lkind[2] 
                             price=Lkind[3]
                             w=Lkind[4]#
                             eX=Lkind[5] 
                             upsilon=self.DcountryUpsilon[country]
                             jobDuration=self.DcountryJobDuration[country]
                             newfirm=Firm(firmide,country,newfirmA,phi,\
                                    self.Lcountry,w,\
                                    self.folder,self.name,self.run,self.delta,\
                                    self.dividendRate,self.xi,self.iota,\
                                    upsilon,self.gamma,self.deltaInnovation,\
                                    price,self.Fcost,\
                                    self.ni,self.minMarkUp,eX,self.theta,self.upsilon2,jobDuration)
                             self.DcountryEnterValue[country]=self.DcountryEnterValue[country]+newfirmA
                             newfirm.tradable='no'
                             newfirm.time=time   
                             newfirm.whichPolicy=McountryEtat[country].whichPolicy
                          if newAgentKind=='firmTradable': 
                             newfirmA=Lkind[1]
                             number=self.McountryFirmMaxNumber[country]
                             self.McountryFirmMaxNumber[country]=number+1
                             firmide='F'+str(country)+'n'+str(number)     
                             phi=Lkind[2] 
                             price=Lkind[3]
                             w=Lkind[4]  
                             eX=Lkind[5]  
                             upsilon=self.DcountryUpsilon[country]
                             jobDuration=self.DcountryJobDuration[country]
                             newfirm=Firm(firmide,country,newfirmA,phi,\
                                    self.Lcountry,w,\
                                    self.folder,self.name,self.run,self.delta,\
                                    self.dividendRate,self.xi,self.iota,\
                                    upsilon,self.gamma,self.deltaInnovation,\
                                    price,self.Fcost,\
                                    self.ni,self.minMarkUp,eX,self.theta,self.upsilon2,jobDuration)
                             self.DcountryEnterValue[country]=self.DcountryEnterValue[country]+newfirmA 
                             self.DcountryFirmEnterTradable[country]=self.DcountryFirmEnterTradable[country]+1  
                             newfirm.tradable='yes'  
                             newfirm.time=time
                             newfirm.whichPolicy=McountryEtat[country].whichPolicy
                          j=basicJ
                          lj=i
                          while j<lj:
                                consumeride=LconsumerInvesting[j][0]
                                consumerShare=LconsumerInvesting[j][1]
                                ratioA=consumerShare/float(newAgentSize)
                                LconsumerInvesting[j][1]=0
                                LconsumerInvesting[j][2]=LconsumerInvesting[j][2]+consumerShare
                                pos=LconsumerInvesting[j][4] 
                                McountryConsumer[country][consumeride].Investing=0
                                McountryConsumer[country][consumeride].DLA[newfirm.ide]=[consumeride,newfirm.ide,consumerShare,pos,ratioA]
                                McountryConsumer[country][consumeride].paying(consumerShare,McountryBank,McountryCentralBank) 
                                LconsumerAsset.append([consumeride,newfirm.ide,consumerShare])
                                newfirm.Downer[consumeride]=McountryConsumer[country][consumeride].DLA[newfirm.ide]
                                newfirm.ListOwners.append(consumeride)  
                                j=j+1
                          # last consumer
                          lastShare=LconsumerInvesting[i][1]-(sumInv-newAgentSize)
                          consumeride=LconsumerInvesting[i][0]
                          consumerShare=lastShare
                          LconsumerInvesting[i][1]=LconsumerInvesting[i][1]-consumerShare
                          LconsumerInvesting[i][2]=LconsumerInvesting[i][2]+consumerShare
                          pos=LconsumerInvesting[i][4] 
                          McountryConsumer[country][consumeride].Investing=LconsumerInvesting[i][1]#0
                          ratioA=consumerShare/float(newAgentSize) 
                          McountryConsumer[country][consumeride].DLA[newfirm.ide]=[consumeride,newfirm.ide,consumerShare,pos,ratioA]
                          McountryConsumer[country][consumeride].paying(consumerShare,McountryBank,McountryCentralBank)
                          LconsumerAsset.append([consumeride,newfirm.ide,consumerShare])
                          newfirm.Downer[consumeride]=McountryConsumer[country][consumeride].DLA[newfirm.ide]
                          newfirm.ListOwners.append(consumeride)
                          newfirmide=newfirm.ide
                          McountryFirm[country][newfirmide]=newfirm
                          enteringfirm=enteringfirm+1
                          enteringfirmC=enteringfirmC+1
                          self.DcountryFirmEnter[country]=self.DcountryFirmEnter[country]+1
                          basicJ=i
                          sumInv=0
                          self.DidEnterANewAgent='yes'
                       if newAgentKind=='bank': 
                          newbankA=newAgentSize
                          number=self.McountryBankMaxNumber[country]
                          self.McountryBankMaxNumber[country]=number+1
                          bankide='B'+str(country)+'n'+str(number)
                          iotaRelPhi=self.DcountryIotaRelPhi[country]
                          newbank=Bank(bankide,country,newbankA,self.Lcountry,self.Fcost,self.folder,self.name,\
                                    self.run,self.delta,self.minReserve,self.rDiscount,self.xi,\
                                    self.dividendRate,self.iota,self.rDeposit,self.mu1,self.iotaE,iotaRelPhi)
                          self.DcountryEnterValue[country]=self.DcountryEnterValue[country]+newbankA
                          j=basicJ
                          lj=i
                          while j<lj:
                                consumeride=LconsumerInvesting[j][0]
                                consumerShare=LconsumerInvesting[j][1]
                                LconsumerInvesting[j][1]=0
                                LconsumerInvesting[j][2]=LconsumerInvesting[j][2]+consumerShare
                                pos=LconsumerInvesting[j][4] 
                                McountryConsumer[country][consumeride].Investing=0
                                ratioA=consumerShare/float(newAgentSize)
                                McountryConsumer[country][consumeride].DLA[newbank.ide]=[consumeride,newbank.ide,consumerShare,pos,ratioA]
                                McountryConsumer[country][consumeride].paying(consumerShare,McountryBank,McountryCentralBank)
                                LconsumerAsset.append([consumeride,newbank.ide,consumerShare])
                                newbank.Downer[consumeride]=McountryConsumer[country][consumeride].DLA[newbank.ide]
                                newbank.ListOwners.append(consumeride)
                                j=j+1
                          # last consumer
                          lastShare=LconsumerInvesting[i][1]-(sumInv-newAgentSize)
                          consumeride=LconsumerInvesting[i][0]
                          consumerShare=lastShare
                          LconsumerInvesting[i][1]=LconsumerInvesting[i][1]-consumerShare
                          LconsumerInvesting[i][2]=LconsumerInvesting[i][2]+consumerShare
                          pos=LconsumerInvesting[i][4] 
                          McountryConsumer[country][consumeride].Investing=LconsumerInvesting[i][1]
                          ratioA=consumerShare/float(newAgentSize) 
                          McountryConsumer[country][consumeride].DLA[newbank.ide]=[consumeride,newbank.ide,consumerShare,pos,ratioA]
                          McountryConsumer[country][consumeride].paying(consumerShare,McountryBank,McountryCentralBank)
                          LconsumerAsset.append([consumeride,newbank.ide,consumerShare])
                          newbank.Downer[consumeride]=McountryConsumer[country][consumeride].DLA[newbank.ide]
                          newbank.ListOwners.append(consumeride)
                          newbank.Reserves=newbank.A
                          McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves+newbank.Reserves
                          McountryBank[country][newbank.ide]=newbank
                          enteringbank=enteringbank+1
                          self.DcountryBankEnter[country]=self.DcountryBankEnter[country]+1
                          basicJ=i
                          sumInv=0
                          self.DidEnterANewAgent='yes' 
                    else:
                        i=i+1
             
 
      def exitFirm(self,McountryFirm,McountryBank,McountryCentralBank):
          exitingfirm=0
          self.DfirmExit={}          
          for country in McountryBank:
              self.DcountryForeignBankLosses[country]=0
          for country in McountryFirm: 
              self.DcountryFirmGone[country]={} 
              self.DcountryFirmExit[country]=0
              self.DcountryFirmExitTradable[country]=0 
              LfirmExit=[] 
              self.DfirmExit[country]=[]
              for firm in  McountryFirm[country]:
                  if McountryFirm[country][firm].closing=='yes': 
                     LfirmExit.append(firm)
                     self.DfirmExit[country].append(firm)
              exitingfirm=0 
              sumDiff=0
              for firm in LfirmExit:
                  if McountryFirm[country][firm].loanReceived>0.0:  
                     rap=McountryFirm[country][firm].loanReimboursed/float(McountryFirm[country][firm].loanReceived) 
                     diff=McountryFirm[country][firm].loanReimboursed-McountryFirm[country][firm].loanReceived
                     sumDiff=sumDiff+diff
                     totalLosses=0
                     for bank in McountryFirm[country][firm].Mloan: 
                         ideBank=bank    
                         reimboursements=0                        
                         countryBank=McountryFirm[country][firm].Mloan[bank][4]                    
                         if McountryBank[countryBank][ideBank].ide==ideBank:
                            reimbourse=rap*McountryFirm[country][firm].Mloan[ideBank][2] 
                            reimboursements=reimboursements+reimbourse
                            losses=McountryFirm[country][firm].Mloan[ideBank][2]*McountryFirm[country][firm].Mloan[ideBank][3]\
                                   +McountryFirm[country][firm].Mloan[ideBank][2]-reimbourse
                            if countryBank!=country:
                               self.DcountryForeignBankLosses[countryBank]=self.DcountryForeignBankLosses[countryBank]+losses
                               self.DcountryForeignBankLosses[country]=self.DcountryForeignBankLosses[country]-losses
                            if reimbourse<McountryFirm[country][firm].Mloan[ideBank][2]:
                               missLoan=McountryFirm[country][firm].Mloan[ideBank][2]-reimbourse 
                               bankIde=McountryFirm[country][firm].Mloan[ideBank][1]  
                               McountryFirm[country][firm].repayingLoan(bankIde,reimbourse,reimbourse,McountryBank,McountryCentralBank,countryBank)
                               McountryBank[countryBank][ideBank].Loan=McountryBank[countryBank][ideBank].Loan-missLoan
                            if reimbourse>=McountryFirm[country][firm].Mloan[ideBank][2]:
                               ideBank=bank
                               loanValue=McountryFirm[country][firm].Mloan[ideBank][2]
                               service=reimbourse-McountryFirm[country][firm].Mloan[ideBank][2]   
                               loanVolume=loanValue+service
                               McountryFirm[country][firm].repayingLoan(ideBank,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank) 
                            if losses<-0.001: 
                               print 'stop', stop
                            totalLosses=totalLosses+losses                            
                            McountryBank[countryBank][ideBank].losses=McountryBank[countryBank][ideBank].losses+losses   
                  for bank in McountryFirm[country][firm].Mdeposit:
                      countryBank=McountryFirm[country][firm].Mdeposit[bank][4]
                      if bank!=country:
                         del  McountryBank[countryBank][bank].Mdeposit[firm]  
                      if bank==country:
                         del  McountryCentralBank[countryBank].Mdeposit[firm]      
                  self.DcountryFirmGone[country][firm]=McountryFirm[country][firm]
                  if McountryFirm[country][firm].tradable=='yes':
                     self.DcountryFirmExitTradable[country]=self.DcountryFirmExitTradable[country]+1
                  del McountryFirm[country][firm]
                  exitingfirm=exitingfirm+1
                  self.DcountryFirmExit[country]=self.DcountryFirmExit[country]+1
                  

      def exitBank(self,McountryConsumer,McountryFirm,McountryBank,McountryCentralBank,McountryEtat):
          exitingbank=0
          self.DpastBondExit={}
          DbankLiving={}
          for country in McountryBank:
              self.DcountryBankGone[country]={}  
              DbankLiving[country]=[]
              for bank in McountryBank[country]:
                  if McountryBank[country][bank].closing=='no':
                     DbankLiving[country].append(McountryBank[country][bank].ide) 
              if len(DbankLiving[country])==0:
                 DbankLiving[country].append(country)    
          for country in McountryBank:
              LbankExit=[]
              LbankLiving=[]
              self.DcountryBankExit[country]=0
              self.DpastBondExit[country]=0 
              McountryEtat[country].coveredDeposit=0 
              for bank in McountryBank[country]:
                  if McountryBank[country][bank].closing=='yes':
                     LbankExit.append(McountryBank[country][bank].ide) 
                  else:
                     LbankLiving.append(McountryBank[country][bank].ide) 
              if len(LbankLiving)==0:
                 LbankLiving.append(country)
              McountryEtat[country].Salvatage=0                    
              for bank in LbankExit: 
                        loss=McountryBank[country][bank].loss 
                        serviceLoanCentralBank=McountryBank[country][bank].loanDiscount*(1+McountryCentralBank[country].rDiscount) 
                        McountryCentralBank[country].loanDiscount=McountryCentralBank[country].loanDiscount-McountryBank[country][bank].loanDiscount
                        McountryCentralBank[country].Bonds=McountryCentralBank[country].Bonds+serviceLoanCentralBank
                        McountryCentralBank[country].interestLoanDiscount=McountryCentralBank[country].interestLoanDiscount+\
                                                   McountryBank[country][bank].loanDiscount*McountryCentralBank[country].rDiscount
                        McountryEtat[country].Bonds=McountryEtat[country].Bonds+serviceLoanCentralBank
                        McountryEtat[country].Salvatage=McountryEtat[country].Salvatage+loss
                        salvatage=McountryBank[country][bank].loanDiscount 
                        McountryBank[country][bank].loanDiscount=0   
                        self.DpastBondExit[country]=self.DpastBondExit[country]+McountryBank[country][bank].pastBonds\
                                          +McountryBank[country][bank].pastBonds*McountryEtat[country].rBonds
                        McountryBank[country][bank].governmentCover=0  
                        sumDepositBack=0
                        sumInterestPayment=0
                        sumVolume=0
                        for agent in McountryBank[country][bank].Mdeposit: 
                            ideAgent=agent
                            volume=McountryBank[country][bank].Mdeposit[ideAgent][2]
                            countryAgent=McountryBank[country][bank].Mdeposit[ideAgent][4]
                            interest=McountryBank[country][bank].Mdeposit[ideAgent][3]                             
                            if ideAgent[0]=='C':
                               volumeCheck=McountryConsumer[countryAgent][ideAgent].Mdeposit[bank][2]
                               if volume<volumeCheck-0.0000001 or volume>volumeCheck+0.0000001:
                                  print 'stop', stop
                               del McountryConsumer[countryAgent][ideAgent].Mdeposit[bank]
                               sumVolume=sumVolume+volume 
                            if ideAgent[0]=='F':
                               interest=0
                               volumeCheck=McountryFirm[countryAgent][ideAgent].Mdeposit[bank][2]
                               if volume<volumeCheck-0.0000001 or volume>volumeCheck+0.0000001:
                                  print 'stop', stop
                               del McountryFirm[countryAgent][ideAgent].Mdeposit[bank]
                            depositBack=volume*interest+volume
                            sumDepositBack=sumDepositBack+depositBack  
                            interestPayment=volume*interest
                            sumInterestPayment=sumInterestPayment+interestPayment 
                            McountryBank[country][bank].exitWithdrawal(depositBack,McountryEtat,McountryCentralBank) 
                            salvatage=salvatage+McountryBank[country][bank].governmentCover
                            random.shuffle(DbankLiving[countryAgent])
                            newbankIde=DbankLiving[countryAgent][0]                           
                            if newbankIde!=countryAgent:
                               if (ideAgent in McountryBank[countryAgent][newbankIde].Mdeposit)==True:   
                                  McountryBank[countryAgent][newbankIde].Mdeposit[ideAgent][2]=\
                                           McountryBank[countryAgent][newbankIde].Mdeposit[ideAgent][2]+depositBack
                                  McountryBank[countryAgent][newbankIde].Deposit=McountryBank[countryAgent][newbankIde].Deposit+depositBack
                                  McountryBank[countryAgent][newbankIde].Reserves=McountryBank[countryAgent][newbankIde].Reserves+depositBack
                                  McountryCentralBank[countryAgent].Reserves=McountryCentralBank[countryAgent].Reserves+depositBack    
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                            McountryConsumer[countryAgent][ideAgent][2].Mdeposit[newbankIde][2]+depositBack
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment 
                                  if ideAgent[0]=='F':
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                       McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]+depositBack 
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment 
                               if (ideAgent in McountryBank[countryAgent][newbankIde].Mdeposit)==False: 
                                  interest=McountryBank[countryAgent][newbankIde].rDeposit
                                  McountryBank[countryAgent][newbankIde].Mdeposit[ideAgent]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                  McountryBank[countryAgent][newbankIde].Deposit=McountryBank[countryAgent][newbankIde].Deposit+depositBack
                                  McountryBank[countryAgent][newbankIde].Reserves=McountryBank[countryAgent][newbankIde].Reserves+depositBack 
                                  McountryCentralBank[countryAgent].Reserves=McountryCentralBank[countryAgent].Reserves+depositBack 
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment
                                  if ideAgent[0]=='F':
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde]=[ideAgent,newbankIde,depositBack,interest,countryAgent]  
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment     
                            if newbankIde==countryAgent:
                               if (ideAgent in McountryCentralBank[countryAgent].Mdeposit)==True: 
                                  McountryCentralBank[countryAgent].Mdeposit[ideAgent][2]=\
                                   McountryCentralBank[countryAgent].Mdeposit[ideAgent][2]+depositBack
                                  McountryCentralBank[countryAgent].Deposit=McountryCentralBank[countryAgent].Deposit+depositBack 
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                           McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde][2]+depositBack
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment
                                  if ideAgent[0]=='F':
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]=\
                                        McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde][2]+depositBack 
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment
                               if (ideAgent in McountryCentralBank[countryAgent].Mdeposit)==False: 
                                  interest=McountryCentralBank[countryAgent].rDeposit 
                                  McountryCentralBank[countryAgent].Mdeposit[ideAgent]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                  McountryCentralBank[countryAgent].Deposit=McountryCentralBank[countryAgent].Deposit+depositBack 
                                  if ideAgent[0]=='C':
                                     McountryConsumer[countryAgent][ideAgent].Mdeposit[newbankIde]=[ideAgent,newbankIde,depositBack,interest,countryAgent]
                                     McountryConsumer[countryAgent][ideAgent].depositInterest=\
                                            McountryConsumer[countryAgent][ideAgent].depositInterest+interestPayment
                                  if ideAgent[0]=='F':                      
                                     McountryFirm[countryAgent][ideAgent].Mdeposit[newbankIde]\
                                                 =[ideAgent,newbankIde,depositBack,interest,countryAgent]                     
                                     McountryFirm[countryAgent][ideAgent].depositInterest=\
                                            McountryFirm[countryAgent][ideAgent].depositInterest+interestPayment
                        withdrawalDifference=sumDepositBack-McountryBank[country][bank].totalDeposit
                        McountryCentralBank[country].Reserves=McountryCentralBank[country].Reserves-McountryBank[country][bank].Reserves
                        McountryCentralBank[country].Bonds=McountryCentralBank[country].Bonds-McountryBank[country][bank].Reserves
                        McountryEtat[country].Bonds=McountryEtat[country].Bonds-McountryBank[country][bank].Reserves
                        intDifference=sumInterestPayment-McountryBank[country][bank].potentialExitConsumer 
                        McountryEtat[country].Salvatage=McountryEtat[country].Salvatage+intDifference
                        McountryBank[country][bank].Reserves=0
                        self.DcountryBankGone[country][bank]=McountryBank[country][bank]
                        del McountryBank[country][bank]
                        exitingbank=exitingbank+1 
                        self.DcountryBankExit[country]=self.DcountryBankExit[country]+1

