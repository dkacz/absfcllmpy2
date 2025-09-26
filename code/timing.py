# timing.py

#    This is the code behind the paper The Effects of Fiscal Targets in a Monetary Union: a Multi-Country Agent Based-Stock Flow Consistent Model
#    Copyright (C) 2017  Alessandro Caiani, Ermanno Catullo, Mauro Gallegati.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from parameter import *
from initialize import *
from firm import *
from consumer import *
from matchingConsumption import *
from matchingLaborCapital import *
from enterExit import *
from aggregator import *
#from aggregatorAle import *
from time import *
import random
from bank import *
from matchingCredit import *
from matchingBonds import *
from matchingDeposit import *
from globalInnovation import *
from printParameters import *
from centralBankUnion import *
from policy import *

# parameter
para=Parameter()
para.directory()
printPa=PrintParameters(para.name,para.folder)

for run in para.Lrun:
    if para.weSeedRun=='yes':
       random.seed(run) 
    # initialization
    printPa.printingPara(para,run)
    ite=Initialize(para.ncountry,para.nconsumer,para.A,para.phi,\
                   para.beta,para.folder,para.name,run,para.delta,\
                   para.taxRatio,para.rDiscount,para.G,\
                   para.cDisposableIncome,para.cWealth,para.liqPref,para.rDeposit,para.rBonds,\
                   para.upsilon,para.maxPublicDeficit,para.xiBonds,para.ls,para.taxRatioMin,\
                   para.taxRatioMax,para.gMin,para.gMax,para.w0,para.wBar,para.upsilon2) 
    ite.createCentralBank()
    ite.createConsumer() 
    ite.createBasic()
    ite.createEtat()  
    name=para.name+'r'+str(run)
    gloInnovation=GlobalInnovation(ite.Lcountry,para.phi)
 
    enEx=enterExit(ite.Lcountry,ite.McountryFirmMaxNumber,\
                  para.folder,para.name,run,para.delta,para.A,\
                  ite.McountryBankMaxNumber,para.probBank,para.minReserve,\
                  para.rDiscount,para.xi,para.dividendRate,para.iota,para.rDeposit,\
                  para.upsilon,para.gamma,para.deltaInnovation,para.mu1,\
                  para.propTradable,para.Fcost,para.ni,para.minMarkUp,\
                  para.iotaE,para.theta,para.sigma,para.upsilon2,para.jobDuration)
                 
     
    maConsumption=MatchingConsumption(ite.Lcountry,para.bound,para.propTradable)
    maLaborCapital=MatchingLaborCapital(para.bound)
    aggrega=Aggregator(ite.Lcountry,name,para.folder,para.timeCollectingStart,\
                            para.LtimeCollecting,para.printAgent)
    maCredit=MatchingCredit() 
    maBonds=MatchingBonds()
    maDeposit=MatchingDeposit(ite.Lcountry)  
    aggrega.basicL(ite.McountryConsumer) 
    centralBankUnion=CentralBankUnion(para.rDiscount,para.rDeposit,para.zeta,para.rBar,para.csi,para.csiDP,para.inflationTarget)
    maDeposit.creatingAccount(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank) 
    poli=policy(para.startingPolicy,para.policyKind,para.maxPublicDeficitAusterity,\
                para.maxPublicDeficit,para.upsilonConsumer,para.deltaLaborPolicy,ite.Lcountry,para.k,para.epsilon)
  
    
    # here we go
    for t in range(para.ncycle):
        print 
        print 'name ', para.name, '---- run', run, ' --- t ',  t

        maLaborCapital.bargaining(ite.McountryFirm,ite.McountryConsumer,\
                                 aggrega.McountryUnemployement,aggrega.McountryPastUnemployement,aggrega.McountryYL,aggrega.McountryPastYL,t)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]: 
                ite.McountryFirm[country][firm].learning()  
                #ite.McountryFirm[country][firm].wageOffered(aggrega.McountryAvPrice,\
                #                   aggrega.McountryUnemployement,para.nconsumer,aggrega.DcountryAvWage)          
                ite.McountryFirm[country][firm].productionDesired(ite.McountryBank,ite.McountryCentralBank,t,aggrega.McountryAvPrice)
                         
        maCredit.creditNetworkEvolution(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,\
                                        gloInnovation.DglobalPhiNotTradable,gloInnovation.DglobalPhiTradable,aggrega.avPhiGlobalTradable)

        for country in ite.McountryBank: 
            for bank in ite.McountryBank[country]:
                ite.McountryBank[country][bank].reservingCompulsory(ite.McountryCentralBank)
        
        maLaborCapital.working(ite.McountryFirm,ite.McountryConsumer,ite.McountryEtat,\
                               ite.McountryBank,ite.McountryCentralBank,aggrega.McountryUnemployement)

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]: 
                ite.McountryFirm[country][firm].effectiveSelling(gloInnovation.DglobalPhiNotTradable,aggrega.avPhiGlobalTradable,\
                                           aggrega.avPriceGlobalTradable,aggrega.McountryAvPriceNotTradable,gloInnovation.DglobalPhi,aggrega.McountryAvPrice)
   
        for country in ite.McountryConsumer:
            for consumer in ite.McountryConsumer[country]:             
                ite.McountryConsumer[country][consumer].income(ite.McountryBank,ite.McountryCentralBank)      

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].expectingTaxation(ite.McountryConsumer,ite.McountryCentralBank,aggrega.McountryUnemployement)

        poli.implementingPolicy(t,ite.McountryEtat,aggrega.McountryYReal,gloInnovation.DglobalPhi,aggrega.DcountryAvWage,\
                                aggrega.McountryAvPrice,aggrega.McountryUnemployement,aggrega.DcumulativeDTBC,\
                                aggrega.DcountryTradeBalance,ite.McountryConsumer,ite.McountryFirm,\
                                enEx.DcountryUpsilon,enEx.DcountryJobDuration,aggrega.McountryDebtY,aggrega.McountryCumCA,\
                                aggrega.McountryY,ite.McountryBank,enEx.DcountryIotaRelPhi) 

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].governmentPlannedExpenditure(ite.McountryConsumer,\
                                                  ite.McountryBank,ite.McountryCentralBank,\
                                                  aggrega.McountryAvPrice,aggrega.McountryY,t,\
                                                  aggrega.DcountryAvWage,poli.policy,\
                                                  aggrega.DcountryTradeBalance,aggrega.McountryUnemployement,gloInnovation.DglobalPhi)

        maBonds.allocatingBonds(ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat) 

        for etat in ite.McountryEtat:
           ite.McountryEtat[etat].taxationConsumer(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank) 
           
        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].redistributionConsumer(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank,aggrega.McountryAvPrice,t) 

        for country in ite.McountryConsumer:
            for consumer in ite.McountryConsumer[country]:
                ite.McountryConsumer[country][consumer].consumptionDemand(ite.McountryBank,ite.McountryCentralBank,aggrega.DcountryFailureProbability) 
             
        maConsumption.consuming(ite.McountryConsumer,ite.McountryFirm,t,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank\
                                ,aggrega.McountryAvPrice,aggrega.avPriceGlobalTradable,\
                                 aggrega.McountryAvPriceNotTradable)    

        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].changingInventory()   

        if para.printAgent=='yes':     
           for country in ite.McountryFirm:
               for firm in ite.McountryFirm[country]:
                   ite.McountryFirm[country][firm].write(t,run)
           for country in ite.McountryBank:
               for bank in ite.McountryBank[country]:  
                   ite.McountryBank[country][bank].write(t,run)
    
        aggrega.income(ite.McountryConsumer,t,\
                       run,ite.McountryFirm,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank,\
                       gloInnovation.DglobalPhi,enEx.DcountryFirmEnter,enEx.DcountryFirmExit,\
                       enEx.DcountryFirmEnterTradable,enEx.DcountryFirmExitTradable,\
                       enEx.DcountryBankEnter,enEx.DcountryBankExit,gloInnovation.DglobalPhiTradable,\
                       gloInnovation.DglobalPhiNotTradable,maCredit.creditCapitalInflow,maCredit.creditCapitalOutflow,
                       maBonds.creditBondInflow,maBonds.creditBondOutflow,enEx.DcountryEnterValue) 

        gloInnovation.spillover(ite.McountryFirm,t)
       
        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].existence(ite.McountryBank,ite.McountryCentralBank)
           
        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].taxationFirm(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)
        
        for country in ite.McountryFirm:
            for firm in ite.McountryFirm[country]:
                ite.McountryFirm[country][firm].distributingDividends(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank)
           
        enEx.exitFirm(ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)
            
        for country in ite.McountryBank:
            for bank in ite.McountryBank[country]:
                ite.McountryBank[country][bank].existence(ite.McountryConsumer,ite.McountryFirm,\
                                      ite.McountryCentralBank,ite.McountryEtat[country].rBonds,ite.McountryEtat,aggrega.DcountryAvWage)

        for etat in ite.McountryEtat:
            ite.McountryEtat[etat].taxationBank(ite.McountryBank,ite.McountryCentralBank)

        for country in ite.McountryBank:
            for bank in ite.McountryBank[country]:
                ite.McountryBank[country][bank].distributingDividends(ite.McountryConsumer,ite.McountryBank,ite.McountryCentralBank)

        enEx.exitBank(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat)
           
        enEx.enter(ite.McountryConsumer,ite.McountryFirm,t,ite.McountryBank,ite.McountryCentralBank,aggrega.McountryAvPrice,ite.McountryEtat) 
    
        for country in ite.McountryConsumer:
            for consumer in ite.McountryConsumer[country]:
                ite.McountryConsumer[country][consumer].ownershipCheck(ite.McountryBank)

        maDeposit.creatingAccount(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank)

        maDeposit.allocatingConsumerDeposit(ite.McountryConsumer,ite.McountryBank)
 
        for country in ite.McountryCentralBank:
            ite.McountryCentralBank[country].balancing(ite.McountryConsumer,ite.McountryFirm,ite.McountryEtat,centralBankUnion,aggrega.DTBC) 

        aggrega.checkCA(ite.McountryConsumer,t,run,ite.McountryFirm,ite.McountryEtat,ite.McountryBank,ite.McountryCentralBank,
                 maCredit.creditCapitalInflow,maCredit.creditCapitalOutflow,
                 maBonds.creditBondInflow,maBonds.creditBondOutflow,enEx.DcountryFirmGone,enEx.DcountryBankGone,\
                 enEx.DcountryForeignBankLosses,t)
       
        aggrega.checkNetWorth(ite.McountryConsumer,ite.McountryFirm,ite.McountryBank,ite.McountryCentralBank,ite.McountryEtat,\
                                   enEx.DpastBondExit) 
        
        centralBankUnion.taylorRule1(aggrega.McountryInflation,aggrega.McountryUnemployement,\
                                    ite.McountryBank,ite.McountryCentralBank,t,ite.McountryConsumer,ite.McountryFirm)

        ite.debtExplotionBreak(aggrega.McountryY,t)
  
        if ite.breaking=='yes':
              break 
    
        
print        
print 'the end'       
      
