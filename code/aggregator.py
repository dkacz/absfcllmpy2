# aggegaror.py

import csv

class Aggregator:
      def __init__(self,Lcountry,name,folder,timeCollectingStart,LtimeCollecting,printAgent):
          self.Lcountry=Lcountry
          ncountry=len(Lcountry)
          self.name=name
          self.folder=folder
          self.timeCollectingStart=timeCollectingStart
          self.LtimeCollecting=LtimeCollecting
          self.firstCountry='no'  
          self.printAgent=printAgent
          self.PastDismiss=0
          self.McountryUnemployement={}
          self.McountryPastUnemployement={}
          self.McountryGrowth={}  
          self.wmin=0
          for country in Lcountry:
              self.McountryUnemployement[country]=0
              self.McountryPastUnemployement[country]=0
              self.McountryGrowth[country]=0 
          self.McountryInflation={}
          for country in Lcountry:
              self.McountryInflation[country]=0
          self.McountryAvPrice={}
          self.McountryAvPriceTradable={}
          self.McountryAvPriceNotTradable={}
          self.McountryYL={}#Y/L aggregate labor productivity
          self.McountryPastYL={}
          for country in Lcountry:
              self.McountryAvPrice[country]=1.0
              self.McountryAvPriceTradable[country]=1.0
              self.McountryAvPriceNotTradable[country]=1.0
              self.McountryYL[country]=1.0
              self.McountryPastYL[country]=1.0
          self.DcumulativeDTBC={} 
          self.DcumulativeTBC={} 
          for country in Lcountry: 
              self.DcumulativeDTBC[country]=0
              self.DcumulativeTBC[country]=0
          self.McountryY={}
          self.McountryYReal={}
          self.McountryDebtY={}
          self.McountryCumCA={} 
          for country in Lcountry:
              self.McountryY[country]=1.0
              self.McountryYReal[country]=1.0 
              self.McountryDebtY[country]=0.0
              self.McountryCumCA[country]=0 
          self.DcountryMinWage={}
          self.DcountryAvWage={}
          self.DcountryTradeBalance={}   
          self.DcountryFailureProbability={}  
          self.DcountryGPhi={}         
          for country in Lcountry:
              self.DcountryMinWage[country]=0.0
              self.DcountryAvWage[country]=1.0
              self.DcountryTradeBalance[country]=0   
              self.DcountryFailureProbability[country]=0
              self.DcountryGPhi[country]=0
          self.DpastDismissedA={}
          self.DdismissedA={}
          self.DpastServiceFirm={}
          self.DserviceFirm={} 
          self.DpastPotentialExitConsumer={}
          self.DpotentialExitConsumer={} 
          self.DbondsInterest={} 
          self.DpastBondsInterest={}
          self.DpastPotentialExitCB={}
          self.DpotentialExitCB={}
          self.Dlosses={}
          self.DpastLosses={} 
          self.DpastSalvatage={}
          self.DSalvatage={}  
          self.DpastLoss={}
          self.Dloss={} 
          self.DcountryCollectData={} 
          for country in Lcountry:
              self.DpastDismissedA[country]=0
              self.DdismissedA[country]=0
              self.DpastServiceFirm[country]=0
              self.DserviceFirm[country]=0 
              self.DpastPotentialExitConsumer[country]=0
              self.DpotentialExitConsumer[country]=0 
              self.DbondsInterest[country]=0
              self.DpastBondsInterest[country]=0
              self.DpastPotentialExitCB[country]=0
              self.DpotentialExitCB[country]=0 
              self.Dlosses[country]=0  
              self.DpastLosses[country]=0    
              self.DpastSalvatage[country]=0
              self.DSalvatage[country]=0    
              self.DpastLoss[country]=0
              self.Dloss[country]=0     
              self.DcountryCollectData[country]=[] 
          self.avPriceGlobal=0
          self.avPhiGlobal=0
          self.avPhiGlobalTradable=0    
          self.avPriceGlobalTradable=0 
 
         

      def unemployement(self,McountryConsumer):
          #self.McountryUnemployement={}
          for country in McountryConsumer: 
              laborEmployed=0
              totLabor=0 
              for consumer in McountryConsumer[country]:
                  laborEmployed=laborEmployed+McountryConsumer[country][consumer].l
                  totLabor=totLabor+McountryConsumer[country][consumer].ls
              self.McountryPastUnemployement[country]=self.McountryUnemployement[country]
              self.McountryUnemployement[country]=(totLabor-laborEmployed)/float(totLabor)
           
      def basicL(self,McountryConsumer):
          self.McountryL={}  
          for country in self.Lcountry:
              Lsupply=len(McountryConsumer[country]) 
              self.McountryL[country]=[0,Lsupply,0,0] 

                         
      def income(self,McountryConsumer,t,run,McountryFirm,McountryEtat,McountryBank,McountryCentralBank,DglobalPhi,DcountryFirmEnter,\
                 DcountryFirmExit,DcountryFirmEnterTradable,\
                 DcountryFirmExitTradable,DcountryBankEnter,DcountryBankExit,DglobalPhiTradable,DglobalPhiNotTradable,\
                 creditCapitalInflow,creditCapitalOutflow,creditBondInflow,creditBondOutflow,DcountryEnterValue):
          self.unemployement(McountryConsumer)
          L=0
          R=0
          Dismiss=0
          Y=0
          Consumption=0
          Expenditure=0
          quantityConsumed=0 
          Investing=0
          depositAllocated=0
          A=0
          nfirm=0
          nx=0
          production=0 
          self.firmA=0
          nexporter=0
          totalTB=0
          TProfit=0
          self.DTBC={}
          ncountry=0
          LProductProducedGlobal=[] 
          DcountryExport={}
          DcountryImport={}  
          sumProductionSoldGlobal=0
          sumPhiGlobal=0
          sumProductionQuantitySoldGlobal=0       
          sumProductionGlobal=0
          sumPhiGlobalTradable=0
          sumProductionGlobalTradable=0 
          sumProductionSoldGlobalTradable=0
          sumProductionQuantitySoldGlobalTradable=0  
          for country in McountryConsumer:
              DcountryExport[country]=0
              DcountryImport[country]=0 
          for country in McountryConsumer: 
              for consumer in McountryConsumer[country]:
                  for good in McountryConsumer[country][consumer].LConsumptionEff:
                      if good[3]!=McountryConsumer[country][consumer].country:
                         expCountry=good[3]
                         DcountryExport[expCountry]=DcountryExport[expCountry]+good[0]*good[1]
                         DcountryImport[country]=DcountryImport[country]+good[0]*good[1] 
          for country in McountryConsumer:
              LproductProduced=[]
              LproductProduced.sort() 
              nconsumer=len(McountryConsumer[country])
              ncountry=ncountry+1
              LC=0
              YC=0
              ConsumptionC=0
              ExpenditureC=0
              SavingC=0 
              ExpenditureCTradable=0
              ExpenditureCNotTradable=0 
              quantityConsumedC=0 
              quantityConsumedCTradable=0
              quantityConsumedCNotTradable=0    
              InvestingC=0
              DepositingC=0
              MvalueC=0
              AC=0
              AfirmC=0
              AbankC=0 
              wc=0
              Nworker=len(McountryConsumer[country])
              PastInvesting=0
              PastDepositing=0
              PastA=0
              pastFirmA=0         
              bankBonds=0
              bankLoan=0
              liqPref=0 
              bankLosses=0  
              disposableIncomeC=0
              totLabor=0
              for bank in McountryBank[country]:
                  bankBonds=bankBonds+McountryBank[country][bank].Bonds 
                  bankLoan=bankLoan+McountryBank[country][bank].Loan
                  bankLosses=bankLosses+McountryBank[country][bank].losses
              for consumer in  McountryConsumer[country]:
                  totLabor=totLabor+McountryConsumer[country][consumer].ls
                  LC=LC+McountryConsumer[country][consumer].l    
                  YC=YC+McountryConsumer[country][consumer].y          
                  disposableIncomeC=disposableIncomeC+McountryConsumer[country][consumer].disposableIncome
                  ConsumptionC=ConsumptionC+McountryConsumer[country][consumer].Consumption
                  ExpenditureC=ExpenditureC+McountryConsumer[country][consumer].Expenditure
                  ExpenditureCTradable=ExpenditureCTradable+McountryConsumer[country][consumer].ExpenditureTradable
                  ExpenditureCNotTradable=ExpenditureCNotTradable+McountryConsumer[country][consumer].ExpenditureNotTradable
                  quantityConsumedC=quantityConsumedC+McountryConsumer[country][consumer].quantityConsumed
                  quantityConsumedCTradable=quantityConsumedCTradable+McountryConsumer[country][consumer].quantityConsumedTradable
                  quantityConsumedCNotTradable=quantityConsumedCNotTradable+McountryConsumer[country][consumer].quantityConsumedNotTradable 
                  InvestingC=InvestingC+McountryConsumer[country][consumer].Investing
                  DepositingC=DepositingC+McountryConsumer[country][consumer].Depositing
                  AC=AC+McountryConsumer[country][consumer].A
                  AfirmC=AfirmC+McountryConsumer[country][consumer].Afirm
                  AbankC=AbankC+McountryConsumer[country][consumer].Abank   
                  wc=wc+McountryConsumer[country][consumer].wOffered*McountryConsumer[country][consumer].l
                  SavingC=SavingC+McountryConsumer[country][consumer].savingIncome\
                          +McountryConsumer[country][consumer].Consumption-McountryConsumer[country][consumer].Expenditure
                  liqPref=liqPref+McountryConsumer[country][consumer].liqPref
                  PastInvesting=PastInvesting+McountryConsumer[country][consumer].PastInvesting
                  PastDepositing=PastDepositing+McountryConsumer[country][consumer].PastDepositing
                  PastA=PastA+McountryConsumer[country][consumer].PastA 
                  depositAllocated=depositAllocated+McountryConsumer[country][consumer].depositAllocated 
              avliqPref=liqPref/float(len(McountryConsumer[country]))  
              print 
              print 'country ', country,'LC ', LC 
              print 'country ', country,'unemployment ', (totLabor-LC)/float(totLabor) 
              avWage=1.0
              if LC>0:
                 avWage=wc/float(LC)
              self.DcountryAvWage[country]=avWage
              print 'country ', country,'average wage', avWage
              L=L+LC
              Y=Y+YC
              Consumption=Consumption+ConsumptionC
              Expenditure=Expenditure+ExpenditureC
              quantityConsumed=quantityConsumed+quantityConsumedC
              Investing=Investing+InvestingC
              A=A+AC
              # firm
              nfirmC=len(McountryFirm[country])
              nbankC=len(McountryBank[country])
              nfirm=nfirm+nfirmC
              nxC=0
              productionC=0
              productionCE=0
              nexporterC=0
              lUsedC=0
              productionExp=0
              productionExpX=0  
              loanReceivedC=0
              loanDemandedC=0
              sumPhi=0
              sumX=0
              self.firmA=0 
              nfirmCTradable=0
              AfirmCTradable=0
              productionCTradable=0 
              nCreditLink=0 
              nWorkerDesired=0
              totalprofitA=0
              laborExpenditure=0 
              profitRate=0
              profitRateperA=0              
              productionQuantity=0 
              productionQuantityTradable=0
              productionCSold=0  
              productionQuantitySold=0 
              productionCTradableSold=0 
              productionQuantityTradableSold=0 
              laborTradable=0
              wageBillTradable=0 
              sumRatioGamma=0
              changeInventoryValue=0 
              inventory=0
              sumInterestRate=0
              inventoryValue=0 
              productionQuantity=0
              innovationExpenditure=0 
              self.DcountryGPhi[country]=0
              profitRate=0
              wageShare=0
              xESum=0
              xESumTradable=0
              innovationExpenditureCorr=0
              probInn=0
              innSuccess=0
              xProducing=0
              for firm in  McountryFirm[country]:
                  nCreditLink=nCreditLink+len(McountryFirm[country][firm].Lcreditor) 
                  self.firmA=self.firmA+McountryFirm[country][firm].A
                  totalprofitA=totalprofitA+McountryFirm[country][firm].profit 
                  nWorkerDesired=nWorkerDesired+McountryFirm[country][firm].nWorkerDesiredEffective 
                  laborExpenditure=laborExpenditure+McountryFirm[country][firm].laborExpenditure
                  sumRatioGamma=sumRatioGamma+McountryFirm[country][firm].ratioGamma
                  changeInventoryValue=changeInventoryValue+McountryFirm[country][firm].changeInventoryValue
                  inventory=inventory+McountryFirm[country][firm].inventory
                  sumInterestRate=sumInterestRate+McountryFirm[country][firm].loanReceived*McountryFirm[country][firm].interestRate
                  #productionQuantity=productionQuantity+McountryFirm[country][firm].productionEffective
                  inventoryValue=inventoryValue+McountryFirm[country][firm].inventoryValue
                  innovationExpenditure=innovationExpenditure+McountryFirm[country][firm].innovationExpenditure
                  self.DcountryGPhi[country]=self.DcountryGPhi[country]+McountryFirm[country][firm].gPhi/float(len(McountryFirm[country]))
                  xESum=xESum+McountryFirm[country][firm].mind.xE
                  innovationExpenditureCorr=innovationExpenditureCorr+McountryFirm[country][firm].lebalance.workerInnovationAvailableEffective
                  probInn=probInn+McountryFirm[country][firm].lebalance.probInn
                  innSuccess=innSuccess+McountryFirm[country][firm].lebalance.innSuccess  
                  xProducing=xProducing+McountryFirm[country][firm].mind.xProducing
                  if McountryFirm[country][firm].tradable=='yes':
                     AfirmCTradable=AfirmCTradable+McountryFirm[country][firm].A 
                     nfirmCTradable=nfirmCTradable+1
                     xTradable=McountryFirm[country][firm].productionEffective
                     xSold=McountryFirm[country][firm].xSold
                     p=McountryFirm[country][firm].price
                     productionCTradable=productionCTradable+p*xTradable
                     productionQuantityTradable=productionQuantityTradable+xTradable 
                     productionCTradableSold=productionCTradableSold+p*xSold
                     productionQuantityTradableSold=productionQuantityTradableSold+xSold  
                     wageBillTradable=wageBillTradable+McountryFirm[country][firm].w*McountryFirm[country][firm].l
                     laborTradable=laborTradable+McountryFirm[country][firm].l
                     sumPhiGlobalTradable=sumPhiGlobalTradable+xTradable*McountryFirm[country][firm].phi
                     sumProductionGlobalTradable=sumProductionGlobalTradable+xTradable 
                     sumProductionSoldGlobalTradable=sumProductionSoldGlobalTradable+p*xSold
                     sumProductionQuantitySoldGlobalTradable=sumProductionQuantitySoldGlobalTradable+xSold
                     xESumTradable=xESumTradable+McountryFirm[country][firm].mind.xE 
                  pastFirmA=pastFirmA+McountryFirm[country][firm].PreviousA
                  profitRate=profitRate+McountryFirm[country][firm].profitRate
                  profitRateperA=profitRateperA+McountryFirm[country][firm].profitRate*McountryFirm[country][firm].PreviousA
                  lUsedC=lUsedC+McountryFirm[country][firm].l
                  exporting=0
                  loanReceivedC=loanReceivedC+McountryFirm[country][firm].loanReceived
                  loanDemandedC=loanDemandedC+McountryFirm[country][firm].loanDemand                          
                  x=McountryFirm[country][firm].productionEffective
                  p=McountryFirm[country][firm].price 
                  xSold=McountryFirm[country][firm].xSold
                  sumPhi=sumPhi+McountryFirm[country][firm].phi*x   
                  productionC=productionC+x*p
                  productionCSold=productionCSold+xSold*p 
                  sumX=sumX+x
                  productionQuantity=productionQuantity+McountryFirm[country][firm].productionEffective
                  productionQuantitySold=productionQuantitySold+xSold
                  profitRate=profitRate+(McountryFirm[country][firm].profit/McountryFirm[country][firm].PreviousA)*p*xSold
                  wageShare=wageShare+\
                         ((McountryFirm[country][firm].w/McountryFirm[country][firm].price)/McountryFirm[country][firm].phi)*p*xSold 
              HI=0
              innovationExpenditureWeighted=0
              for firm in  McountryFirm[country]:
                  marketShare=0
                  if productionCSold>0:
                     marketShare=(McountryFirm[country][firm].xSold*McountryFirm[country][firm].price)/float(productionCSold)
                  HI=HI+marketShare**2  
                  innovationExpenditureWeighted=innovationExpenditureWeighted+McountryFirm[country][firm].innovationExpenditure*marketShare 
                  
              avPhi=0
              avPrice=0
              if sumX>0:
                 avPhi=sumPhi/float(sumX)  
                 avPrice=productionC/float(sumX)  
              sumProductionGlobal=sumProductionGlobal+sumX
              sumProductionSoldGlobal=sumProductionSoldGlobal+productionCSold
              sumPhiGlobal=sumPhiGlobal+sumPhi
              sumProductionQuantitySoldGlobal=sumProductionQuantitySoldGlobal+productionQuantitySold
              productionCE=productionC 
              production=production+productionCE 
              nexporter=nexporter+nexporterC
              pastAvPC=self.McountryAvPrice[country]
              avPC=self.McountryAvPrice[country]
              avPCTradable=self.McountryAvPriceTradable[country]
              avPCNotTradable=self.McountryAvPriceNotTradable[country]
              if productionQuantitySold>0: 
                 avPC=productionCSold/float(productionQuantitySold)
              if productionQuantityTradableSold>0: 
                 avPCTradable=productionCTradableSold/float(productionQuantityTradableSold)
              if quantityConsumedCNotTradable>0: 
                 avPCNotTradable=ExpenditureCNotTradable/float(quantityConsumedCNotTradable)    
              if productionCSold>0:
                 profitRate=profitRate/productionCSold
                 wageShare=wageShare/productionCSold
              if productionCSold==0:
                 profitRate=0
                 wageShare=0   
              inflation=0
              if pastAvPC>0:
                 inflation=(avPC-pastAvPC)/float(pastAvPC)
              self.McountryAvPrice[country]=avPC
              self.McountryAvPriceTradable[country]=avPCTradable
              self.McountryAvPriceNotTradable[country]=avPCNotTradable
              self.McountryInflation[country]=inflation 
              averageFirmProfit=0
              if pastFirmA>0:
                 averageFirmProfit=totalprofitA/float(pastFirmA) 
              averageFirmProfitRate=0
              if len(McountryFirm[country])>0:
                 averageFirmProfitRate=profitRate/float(len(McountryFirm[country]))
              averageFirmProfitRateperA=0
              if pastFirmA>0:
                 averageFirmProfitRateperA=profitRateperA/float(pastFirmA)
              productivity=1.0
              if LC>0:
                 productivity=productionQuantity/float(LC)  
              avWageTradable=0
              if laborTradable>0:
                 avWageTradable=wageBillTradable/float(laborTradable) 
              avRatioGamma=0
              if sumRatioGamma>0:
                 avRatioGamma=sumRatioGamma/float(len(McountryFirm[country])) 
              rSoldProd=0
              if  productionQuantity>0:
                  rSoldProd=productionQuantitySold/productionQuantity
              self.McountryY[country]=productionCSold+changeInventoryValue
              if productionQuantitySold>0:
                 self.McountryYReal[country]=(productionCSold+changeInventoryValue)/avPC
                 self.McountryDebtY[country]=McountryEtat[country].Bonds/(productionCSold+changeInventoryValue)
              if productionQuantitySold<=0:
                 self.McountryYReal[country]=0
                 self.McountryDebtY[country]=0  
              print 'country ', country, 'average Price ', avPC
              print 'country ', country, 'w/p ', avWage/avPC
              print 'country ', country, 'productivity ', productivity
              print 'country ', country, 'avPhi ', avPhi  
              print 'country ', country, 'wage share ', (avWage/avPC)/productivity 
              print 'country ', country, 'z ', (avPC*productivity)/avWage-1
              print 'country ', country, 'zPhi ', (avPC*avPhi)/avWage-1
              #print 'country ', country, 'wage/phi ', (avWage)/productivity  
              print 'country ', country, 'avPCTradable ', avPCTradable
              if  self.McountryY[country]>0:
                  print 'country ', country, 'Credit/Y ', loanReceivedC/self.McountryY[country]
              print 'country ', country, 'bank NW ', AbankC
              print 'country ', country, 'firm NW ', AfirmC
              print 'country ', country, 'firm Tradable NW', AfirmCTradable  
              print 'country ', country, 'n. bank ', nbankC 
              print 'country ', country, 'n. firm NW', nfirmC
              print 'country ', country, 'n.firm Tradable ', nfirmCTradable 
              print 'country ', country, 'taxRate ', McountryEtat[country].taxRate
              print 'country ', country, 'Y ', productionCSold+changeInventoryValue
              print 'country ', country, 'realY ', (productionCSold+changeInventoryValue)/avPC
              if DglobalPhiTradable[country]>0:
                 print 'country ', country,   'w/phi Tradable',  avWageTradable/float(DglobalPhiTradable[country])  
              pastProductionC=self.McountryY[country]
              
              self.McountryGrowth[country]=0 
              if pastProductionC>0: 
                  self.McountryGrowth[country]=(productionC-pastProductionC)/float(pastProductionC)
              if productionC>0:
                 print 'country ', country,  'debt/Y ', McountryEtat[country].Bonds/float(productionCSold+changeInventoryValue)
              if productionC>0: 
                 print 'country ', country,   'G/Y', McountryEtat[country].realG/float(productionCSold+changeInventoryValue)
              if  self.McountryY[country]>0:
                  print 'country ', country, 'deficit/Y ', McountryEtat[country].publicDeficit/self.McountryY[country]
                  print 'country ', country, '(X+M)/Y ', (DcountryExport[country]+DcountryImport[country])/self.McountryY[country] 
                  print 'country ', country, 'HI ', HI
              averageInterestRate=0
              if bankLoan>0:
                 averageInterestRate=sumInterestRate/float(bankLoan)
              TBC=DcountryExport[country]-DcountryImport[country]
              self.DcountryTradeBalance[country]=TBC
              self.DTBC[country]=TBC
              self.McountryPastYL[country]=self.McountryYL[country]
              self.McountryYL[country]=1.0  
              if  self.McountryY[country]>0:
                  self.McountryYL[country]=avPC*avPhi#/float(LC)
                  print 'country ', country, 'TBC/Y ', TBC/Y  
                  print 'country ', country, 'self.McountryYL[country]', self.McountryYL[country]   
              print 'country ', country, 'labPolicy ', McountryEtat[country].labPolicy
              print 'country ', country, 'whichPolicy ', McountryEtat[country].whichPolicy
              MK=creditCapitalInflow[country]-creditCapitalOutflow[country]+creditBondInflow[country]-creditBondOutflow[country]
              BdP=creditCapitalInflow[country]-creditCapitalOutflow[country]+creditBondInflow[country]-creditBondOutflow[country]\
                 +TBC      
              CA=TBC
              PrivateSaving=disposableIncomeC-ExpenditureC
              PublicSaving=-1*McountryEtat[country].publicDeficit   
              if lUsedC<LC-0.000001 or  lUsedC>LC+0.000001:
                 print 'stop', stop
              self.DcountryMinWage[country]=self.wmin
              self.DcountryFailureProbability[country]=0
              if nfirmC+nbankC>0:
                 self.DcountryFailureProbability[country]=(DcountryBankExit[country]+DcountryFirmExit[country])/float(nfirmC+nbankC)
              nfirmCNotTradable=nfirmC-nfirmCTradable 
              #print
              #print 'McountryCentralBank[country].rDiscount', McountryCentralBank[country].rDiscount,
              #print    
              self.DcountryCollectData[country]=[run,t,country,productionC,DcountryExport[country],DcountryImport[country],nfirmC,\
                                   avWage,LC,avPhi,DglobalPhi[country],nbankC,McountryEtat[country].publicDeficit,
                                    McountryEtat[country].Bonds,avPC,bankLoan,bankBonds,\
                                   McountryCentralBank[country].Bonds,self.firmA,DcountryFirmEnter[country],DcountryFirmExit[country],\
                                   DcountryFirmEnterTradable[country],DcountryFirmExitTradable[country],\
                                   DcountryBankEnter[country],DcountryBankExit[country],AbankC,\
                                   nfirmCTradable,nfirmCNotTradable,AfirmCTradable,\
                                   DglobalPhiTradable[country],DglobalPhiNotTradable[country],\
                                   avPCTradable,avPCNotTradable,SavingC,nCreditLink,averageFirmProfit,McountryEtat[country].adjust,\
                                   productionCSold+changeInventoryValue,McountryEtat[country].Salvatage,bankLosses,\
                                   McountryEtat[country].taxRate,\
                                   McountryEtat[country].realG,\
                                   creditCapitalInflow[country],creditCapitalOutflow[country],creditBondInflow[country],\
                                   creditBondOutflow[country],ExpenditureC,disposableIncomeC,\
                                   productionCSold,changeInventoryValue,inventory,\
                                   McountryCentralBank[country].rDiscount\
                                   ,loanDemandedC,averageInterestRate,inventoryValue,productionQuantity,\
                                   DcountryEnterValue[country],innovationExpenditure,McountryEtat[country].labPolicy,nWorkerDesired,\
                                   McountryEtat[country].whichPolicy,HI,profitRate,wageShare,xESum,xESumTradable\
                                   ,innovationExpenditureCorr,probInn,\
                                   innSuccess,innovationExpenditureWeighted,loanReceivedC,xProducing]
          totalTB=0
          totalY=0      
          for country in McountryConsumer:
              TBC=DcountryExport[country]-DcountryImport[country] 
              totalTB=totalTB+TBC
              totalY=totalY+self.McountryY[country] 
          for country in McountryConsumer:
              if self.McountryY[country]>0:
                 self.DcumulativeTBC[country]=self.DcumulativeTBC[country]+self.DcountryTradeBalance[country]
                 self.DcumulativeDTBC[country]=self.DcumulativeTBC[country]/float(self.McountryY[country])
          self.avPriceGlobal=0
          if sumProductionQuantitySoldGlobal>0:
             self.avPriceGlobal=sumProductionSoldGlobal/float(sumProductionQuantitySoldGlobal)
          self.avPriceGlobalTradable=0
          if sumProductionQuantitySoldGlobalTradable>0:
             self.avPriceGlobalTradable=sumProductionSoldGlobalTradable/float(sumProductionQuantitySoldGlobalTradable)
          self.avPhiGlobal=0
          if sumProductionGlobal>0:
             self.avPhiGlobal=sumPhiGlobal/float(sumProductionGlobal)
          self.avPhiGlobalTradable=0
          if sumProductionGlobalTradable>0:
             self.avPhiGlobalTradable=sumPhiGlobalTradable/float(sumProductionGlobalTradable) 
          if R<0:
             print 'stop', stop 
          if quantityConsumed>0:     
               avP=Expenditure/float(quantityConsumed) 
          if quantityConsumed==0:     
               avP=0
          if t==1 or t==0:
             self.avP0=avP
          #if totalTB>0.00001 or totalTB<-0.00001:
          #   print 'totalTB', totalTB
          #   print 'stop', stop      
          #self.PastDismiss=Dismiss 

      def checkCA(self,McountryConsumer,t,run,McountryFirm,McountryEtat,McountryBank,McountryCentralBank,
                 creditCapitalInflow,creditCapitalOutflow,creditBondInflow,creditBondOutflow,DcountryFirmGone,DcountryBankGone,\
                 DcountryForeignBankLosses,time):
          for country in McountryConsumer:
              disposableIncomeC=0
              ExpenditureC=0
              firmProfit=0
              pastFirmProfit=0
              pastBankProfit=0
              bankProfit=0
              pastFirmSaving=0
              pastBankSaving=0
              self.DpastDismissedA[country]=self.DdismissedA[country]
              self.DdismissedA[country]=0
              self.DpastPotentialExitConsumer[country]=self.DpotentialExitConsumer[country]
              self.DpotentialExitConsumer[country]=0 
              self.DpastBondsInterest[country]=self.DbondsInterest[country] 
              self.DbondsInterest[country]=0
              self.DpastServiceFirm[country]=self.DserviceFirm[country]
              self.DserviceFirm[country]=0
              self.DpastPotentialExitCB[country]=self.DpotentialExitCB[country]
              self.DpotentialExitCB[country]=0
              self.DpastLosses[country]=self.Dlosses[country]
              self.Dlosses[country]=0               
              self.DpastSalvatage[country]=self.DSalvatage[country]
              self.DSalvatage[country]=0 
              self.DpastLoss[country]=self.Dloss[country]
              self.Dloss[country]=0 
              profitRate=0
              agentA=0
              profitRateA=0
              for consumer in McountryConsumer[country]:
                  disposableIncomeC=disposableIncomeC+McountryConsumer[country][consumer].disposableIncome
                  ExpenditureC=ExpenditureC+McountryConsumer[country][consumer].Expenditure
              for firm in McountryFirm[country]:
                     firmProfit=firmProfit+McountryFirm[country][firm].profit
                     profitRate=profitRate+McountryFirm[country][firm].profitRate
                     profitRateA=profitRateA+McountryFirm[country][firm].profitRate*McountryFirm[country][firm].PreviousA 
                     pastFirmProfit=pastFirmProfit+McountryFirm[country][firm].pastProfit
                     pastFirmSaving=pastFirmSaving+McountryFirm[country][firm].pastFirmSaving
                     agentA=agentA+McountryFirm[country][firm].PreviousA
              for firm in DcountryFirmGone[country]:
                  firmProfit=firmProfit+DcountryFirmGone[country][firm].profit
                  pastFirmProfit=pastFirmProfit+DcountryFirmGone[country][firm].pastProfit
                  pastFirmSaving=pastFirmSaving+DcountryFirmGone[country][firm].pastFirmSaving  
                  profitRate=profitRate+DcountryFirmGone[country][firm].profitRate
                  profitRateA=profitRateA+DcountryFirmGone[country][firm].profitRate*DcountryFirmGone[country][firm].PreviousA
                  agentA=agentA+DcountryFirmGone[country][firm].PreviousA
                  if   DcountryFirmGone[country][firm].profit+DcountryFirmGone[country][firm].PreviousA>0:
                      self.DdismissedA[country]=self.DdismissedA[country]+(DcountryFirmGone[country][firm].profit+DcountryFirmGone[country][firm].PreviousA)
              for bank in McountryBank[country]:
                     bankProfit=bankProfit+McountryBank[country][bank].profit
                     pastBankProfit=pastBankProfit+McountryBank[country][bank].pastProfit 
                     pastBankSaving=pastBankSaving+McountryBank[country][bank].pastBankSaving
                     self.DpotentialExitConsumer[country]=self.DpotentialExitConsumer[country]+McountryBank[country][bank].potentialExitConsumer 
                     self.DbondsInterest[country]=self.DbondsInterest[country]+McountryBank[country][bank].bondsInterest
                     self.DpotentialExitCB[country]=self.DpotentialExitCB[country]+McountryBank[country][bank].potentialExitCB 
                     self.Dlosses[country]=self.Dlosses[country]+McountryBank[country][bank].losses
                     profitRate=profitRate+McountryBank[country][bank].profitRate
                     profitRateA=profitRateA+McountryBank[country][bank].profitRate*McountryBank[country][bank].PreviousA 
                     agentA=agentA+McountryBank[country][bank].PreviousA 
              for bank in DcountryBankGone[country]:
                  bankProfit=bankProfit+DcountryBankGone[country][bank].profit
                  pastBankProfit=pastBankProfit+DcountryBankGone[country][bank].pastProfit 
                  pastBankSaving=pastBankSaving+DcountryBankGone[country][bank].pastBankSaving
                  self.DpotentialExitConsumer[country]=self.DpotentialExitConsumer[country]+DcountryBankGone[country][bank].potentialExitConsumer 
                  self.DbondsInterest[country]=self.DbondsInterest[country]+DcountryBankGone[country][bank].bondsInterest
                  self.DpotentialExitCB[country]=self.DpotentialExitCB[country]+DcountryBankGone[country][bank].potentialExitCB  
                  self.DserviceFirm[country]=self.DserviceFirm[country]+DcountryBankGone[country][bank].pastServiceFirm
                  self.Dlosses[country]=self.Dlosses[country]+DcountryBankGone[country][bank].losses
                  self.Dloss[country]=self.Dloss[country]+DcountryBankGone[country][bank].loss
                  profitRate=profitRate+DcountryBankGone[country][bank].profitRate
                  profitRateA=profitRateA+DcountryBankGone[country][bank].profitRate*+DcountryBankGone[country][bank].PreviousA 
                  agentA=agentA+DcountryBankGone[country][bank].PreviousA 
                  if  DcountryBankGone[country][bank].profit+DcountryBankGone[country][bank].PreviousA>0:
                      self.DdismissedA[country]=self.DdismissedA[country]+(DcountryBankGone[country][bank].profit+DcountryBankGone[country][bank].PreviousA)
              BdP=self.DTBC[country]+creditCapitalInflow[country]-creditCapitalOutflow[country]+creditBondInflow[country]-creditBondOutflow[country]
              pastProfit=0
              pastProfit=pastProfit+pastFirmProfit
              pastProfit=pastProfit+pastBankProfit  
              PrivateSaving=disposableIncomeC-ExpenditureC+firmProfit+bankProfit\
                            -(pastProfit-pastFirmSaving-pastBankSaving)-self.DpastDismissedA[country]\
                            +self.DpotentialExitConsumer[country]-self.DpastPotentialExitConsumer[country]\
                            -self.DbondsInterest[country]+self.DpastBondsInterest[country]\
                            +self.DpotentialExitCB[country]-self.DpastPotentialExitCB[country]\
                            +self.Dlosses[country]+self.DpastLoss[country]
              PublicSaving=-1*McountryEtat[country].publicDeficit 
              CA=self.DTBC[country]+McountryCentralBank[country].diffInflowOutflow+DcountryForeignBankLosses[country]\
                 +McountryCentralBank[country].pastDiffBondRepeymentInflowOutflow
              self.DcountryCollectData[country].append(CA)
              self.DcountryCollectData[country].append(PrivateSaving)
              self.DcountryCollectData[country].append(McountryCentralBank[country].diffInflowOutflow+DcountryForeignBankLosses[country])
              self.DcountryCollectData[country].append(McountryCentralBank[country].pastDiffBondRepeymentInflowOutflow) 
              self.writingData(time,country)
              self.McountryCumCA[country]=self.McountryCumCA[country]+CA
              CAOnY=0 
              Y=self.DcountryCollectData[country][3]  
              if Y>0:
                 CAOnY=CA/float(Y)
              if  self.McountryY[country]>0: 
                  if CA<PrivateSaving+PublicSaving-0.001 or CA>PrivateSaving+PublicSaving+0.001 or country=='0' or country=='1':
                     print 'stop', stop
            
      def writingData(self,time,country):
          if time==self.timeCollectingStart and self.firstCountry=='no':
                 self.firstCountry='yes'  
                 self.WriteInitial()
          self.Lprint=self.DcountryCollectData[country]
          c=open(self.nameCollect,'a')  
          writer = csv.writer(c)
          writer.writerow(self.Lprint)
          c.close()
              
                 
      def WriteInitial(self):
          self.nameCollect=self.folder+'/'+self.name+'AggData.csv' 
          L=['run','time','country','Yprod','Export','Import','nFirm', 'avWage','nOccupied',\
             'avPhi','phiCountry','nBank','publicDeficit', 'publicDebt','avPrice',\
             'bankLoan','bankBonds','cbBonds','netWorthFirm','enteringFirm','exitingFirm','enteringFirmTradable',\
             'exitingFirmTradable','enteringBank',\
             'exitingBank','netWorthBank',\
             'nFirmTradable','nfirmNotTradable',\
             'netWorthFirmTradable','avPhiTradable','avPhiNotTradable',\
             'avPCTradable','avPCNotTradable','Saving','nCreditLink','averageFirmProfit','adjust','Ysold',\
             'Salvatage','badDebt','taxRate','G',\
             'creditCapitalInflow','creditCapitalOutflow','creditBondInflow','creditBondOutflow','ExpenditureC','disposableIncomeC',\
             'productionSoldValue','changeInventoryValue','inventoryQuantity',\
             'rDiscount','loanDemanded','averageInterestRate','inventoryValue','productionQuantity',\
             'EnterValue','innovationExpenditure','labPolicy','nWorkerDesired','whichPolicy','HI','profitRate',\
             'wageShare','xESum','xESumTradable','innovationExpenditureCorr','probInn',\
             'innSuccess','innovationExpenditureWeighted','loanReceived','xProducing',\
             'CA','PrivateSaving',\
             'diffCreditFlow','diffBondFlow']
          c=open(self.nameCollect,'wb')  
          writer = csv.writer(c)
          writer.writerow(L)
          c.close()
          if  self.printAgent=='yes':
              nameCollectFirm=self.folder+'/'+self.name+'Firm.csv' 
              L=['run', 'ide','time','country', 'phi','profit','p','w','l','x_prod',\
               'xE','x_sold','inventory', 'workForceNumberDesired','A','revenue'] 
              c=open(nameCollectFirm,'wb')  
              writer = csv.writer(c)
              writer.writerow(L)
              c.close()
              nameCollectBank=self.folder+'/'+self.name+'Bank.csv' 
              L=['run', 'ide','time','country', 'A','profit','Bonds','Loan','Deposit']
              c=open(nameCollectBank,'wb')  
              writer = csv.writer(c)
              writer.writerow(L)
              c.close()

      def checkNetWorth(self,McountryConsumer,McountryFirm,McountryBank,McountryCentralBank,McountryEtat,DpastBondExit):
          for country in McountryConsumer:
              netWorthConsumer=0
              netWorthBank=0
              netWorthFirm=0
              netWorthCentralBank=0
              netWorthEtat=0
              assetsFirm=1
              assetsBank=1 
              for consumer in McountryConsumer[country]:
                  nW=McountryConsumer[country][consumer].Deposit+McountryConsumer[country][consumer].A                  
                  netWorthConsumer=netWorthConsumer+nW
              for firm in McountryFirm[country]:
                  McountryFirm[country][firm].computeDeposit()
                  nW=McountryFirm[country][firm].Deposit-McountryFirm[country][firm].A
                  assetsFirm=assetsFirm+McountryFirm[country][firm].Deposit+McountryFirm[country][firm].A  
                  netWorthFirm=netWorthFirm+nW
              for bank in McountryBank[country]:
                  netWorthBank=netWorthBank+McountryBank[country][bank].Reserves+McountryBank[country][bank].Bonds+\
                                McountryBank[country][bank].Loan-McountryBank[country][bank].Deposit-McountryBank[country][bank].A
                  assetsBank=assetsBank+McountryBank[country][bank].Reserves+McountryBank[country][bank].Bonds+\
                                McountryBank[country][bank].Loan+McountryBank[country][bank].Deposit-McountryBank[country][bank].A
              netWorthCentralBank=McountryCentralBank[country].Bonds+McountryCentralBank[country].loanDiscount\
                                  -McountryCentralBank[country].DepositEtatCentralBank-McountryCentralBank[country].Deposit\
                                  -McountryCentralBank[country].Reserves
              netWorthEtat=McountryEtat[country].LiquidityEtat-McountryEtat[country].Bonds
              netWorth=netWorthConsumer+netWorthBank+netWorthFirm+netWorthCentralBank+netWorthEtat
              if netWorth/float(netWorthConsumer)>0.0001 or netWorth/float(netWorthConsumer)<-0.0001\
                 or netWorthFirm/float(assetsFirm)>0.0001 or netWorthFirm/float(assetsFirm)<-0.0001\
                 or netWorthBank/float(assetsBank)>0.0001 or netWorthBank/float(assetsBank)<-0.0001:                        
                 print 'stop', stop
              McountryCentralBank[country].checkNetWorth() 
              McountryCentralBank[country].checkReserves(McountryBank) 
    
