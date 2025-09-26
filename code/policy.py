# policy.py

import random
import math

class policy:
      def __init__(self,timeStarting,policyKind,maxPublicDeficitAusterity,\
                   maxPublicDeficit,upsilonConsumer,deltaLaborPolicy,Lcountry,k,epsilon):
          self.timeStarting=timeStarting
          self.policyKind=policyKind
          self.maxPublicDeficit=maxPublicDeficit 
          self.maxPublicDeficitAusterity=maxPublicDeficitAusterity
          self.upsilonConsumer=upsilonConsumer
          self.deltaLaborPolicy=deltaLaborPolicy
          self.policyVariable=upsilonConsumer
          self.McountryYPolicy={}
          self.McountryYRealPolicy={}
          self.McountryDebtYPolicy={}  
          self.McountryCumCAPolicy={} 
          for country in Lcountry:
              self.McountryYPolicy[country]=1.0
              self.McountryYRealPolicy[country]=1.0 
              self.McountryDebtYPolicy[country]=0.0 
              self.McountryCumCAPolicy[country]=0.0  
          #self.Lstra=['no','compre']
          #self.DstraUpsilon={'no':1.0,'compre':self.policyVariable}
          self.LstraThree=['no','compre','expa']
          self.LstraTwo=['no','expa'] 
          #self.DstraUpsilonThree={'no':1.0,'compre':self.policyVariable,'expa':1/float(self.policyVariable)}
          self.DstraUpsilonThree={'no':1.625,'compre':2.876,'expa':0.512}
          self.k=k
          self.epsilon=epsilon  
           
          

      def implementingPolicy(self,time,McountryEtat,McountryYReal,DglobalPhi,DcountryAvWage,McountryAvPrice,McountryUnemployement,\
                             DcumulativeDTBC,DcountryTradeBalance,McountryConsumer,\
                             McountryFirm,DcountryUpsilon,DcountryJobDuration,McountryDebtY,\
                             McountryCumCA,McountryY,McountryBank,DcountryIotaRelPhi):
          self.policy='no' 
          if time==self.timeStarting and self.policyKind=='Mod':            
             McountryEtat[0].labPolicy='yes'
             for consumer in McountryConsumer[0]:
                 McountryConsumer[0][consumer].upsilon=self.policyVariable
             for firm in McountryFirm[0]:
                 McountryFirm[0][firm].upsilon=self.policyVariable    
             DcountryUpsilon[0]=self.policyVariable
             #print 'stop', stop 
             self.policy=self.policyKind      
          if time==self.timeStarting and self.policyKind=='ModAll': 
             for country in McountryConsumer: 
                 McountryEtat[country].labPolicy='yes'
                 for consumer in McountryConsumer[country]:
                     McountryConsumer[country][consumer].upsilon=self.policyVariable
                 for firm in McountryFirm[country]:
                      McountryFirm[country][firm].upsilon=self.policyVariable
                 DcountryUpsilon[country]=self.policyVariable 
             self.policy=self.policyKind  
             #print 'stop', stop     
          if time==self.timeStarting and self.policyKind=='ModPic':            
             McountryEtat[0].labPolicy='yes'
             for consumer in McountryConsumer[0]:
                 McountryConsumer[0][consumer].upsilon=self.policyVariable
             for firm in McountryFirm[0]:
                 McountryFirm[0][firm].upsilon=self.policyVariable 
             for bank in McountryBank[0]:
                 McountryBank[0][bank].iotaRelPhi=McountryBank[0][bank].iotaRelPhi*10     
             DcountryUpsilon[0]=self.policyVariable
             DcountryIotaRelPhi[0]=DcountryIotaRelPhi[0]*10
             #print 'stop', stop 
             self.policy=self.policyKind 
          if time==self.timeStarting and self.policyKind=='ModH':
             LPhi=[]
             for country in DglobalPhi:
                 LPhi.append([DglobalPhi[country],country])
             LPhi.sort()
             LPhi.reverse()
             policyCountry=LPhi[0][1]
             print 
             print 'LPhi', LPhi
             print 'policyCountry', policyCountry
             McountryEtat[policyCountry].labPolicy='yes' 
             #print 'stop', stop   
             for consumer in McountryConsumer[policyCountry]:
                 McountryConsumer[policyCountry][consumer].upsilon=self.policyVariable
             for firm in McountryFirm[policyCountry]:
                 McountryFirm[policyCountry][firm].upsilon=self.policyVariable    
             DcountryUpsilon[policyCountry]=self.policyVariable
          if time==self.timeStarting and self.policyKind=='ModL':
             LPhi=[]
             for country in DglobalPhi:
                 LPhi.append([DglobalPhi[country],country])
             LPhi.sort()
             #LPhi.reverse()
             policyCountry=LPhi[0][1]
             print 
             print 'LPhi', LPhi
             print 'policyCountry', policyCountry
             McountryEtat[policyCountry].labPolicy='yes' 
             #print 'stop', stop   
             for consumer in McountryConsumer[policyCountry]:
                 McountryConsumer[policyCountry][consumer].upsilon=self.policyVariable
             for firm in McountryFirm[policyCountry]:
                 McountryFirm[policyCountry][firm].upsilon=self.policyVariable    
             DcountryUpsilon[policyCountry]=self.policyVariable
          if time>=self.timeStarting and self.policyKind=='StraThree' and time%20==0:
             LgY=[] 
             for country in McountryYReal:
                 g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                 LgY.append([g,country])
             maxg=max(LgY)[0]
             maxCountry=max(LgY)[1]
             maxStra=McountryEtat[maxCountry].labPolicy 
             print
             print 'maxStra', maxStra
             print 'maxCountry', maxCountry
             print 'maxg', maxg
             print 'LgY', LgY 
             #print 'stop', stop      
             for country in McountryYReal:
                 a=random.uniform(0,1)
                 print 
                 print 'country', country
                 print 'a', a
                 print 'self.epsilon', self.epsilon
                 if a<self.epsilon and country!=maxCountry:
                    print 
                    print 'random'
                    #print 'country', country
                    #print 'a', a
                    print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy
                    #print 'stop', stop
                    g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                    p=1-math.exp(-self.k*(maxg-g)) 
                    b=random.uniform(0,1)
                    print 
                    print 'country', country 
                    print 'g', g
                    print 'maxg',maxg
                    print 'p', p
                    print 'b', b      
                    if b<p:
                     x=random.randint(0,len(self.LstraThree)-1)
                     if  McountryEtat[country].labPolicy!=self.LstraThree[x]:
                        McountryEtat[country].labPolicy=self.LstraThree[x]
                        upsilonPolicy=self.DstraUpsilonThree[self.LstraThree[x]]
                        for consumer in McountryConsumer[country]:
                            McountryConsumer[country][consumer].upsilon=upsilonPolicy
                        for firm in McountryFirm[country]:
                            McountryFirm[country][firm].upsilon=upsilonPolicy   
                        DcountryUpsilon[country]=upsilonPolicy
                     print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy
                     print 'x', x
                     #print 'upsilonPolicy', upsilonPolicy
                     print 'random new strategy'
                     print 'self.LstraThree[x]', self.LstraThree[x]                       
                 else:
                      print 
                      print 'notRandom'
                      print 'country==maxCountry', country==maxCountry
                      if country!=maxCountry:
                         g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                         p=1-math.exp(-self.k*(maxg-g)) 
                         b=random.uniform(0,1)
                         print 
                         print 'country', country 
                         print 'g', g
                         print 'maxg',maxg
                         print 'maxg-g', maxg-g
                         print 'self.k*(maxg-g)', self.k*(maxg-g) 
                         print 'McountryYReal[country]', McountryYReal[country]
                         print 'self.McountryYRealPolicy[country]', self.McountryYRealPolicy[country] 
                         print 'p', p
                         print 'b', b      
                         print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                         print 'McountryEtat[maxCountry].labPolicy',  McountryEtat[maxCountry].labPolicy
                         if b<p:
                            if  McountryEtat[country].labPolicy!=maxStra:
                                McountryEtat[country].labPolicy=maxStra
                                upsilonPolicy=self.DstraUpsilonThree[maxStra]
                                for consumer in McountryConsumer[country]:
                                    McountryConsumer[country][consumer].upsilon=upsilonPolicy
                                for firm in McountryFirm[country]:
                                    McountryFirm[country][firm].upsilon=upsilonPolicy 
                                DcountryUpsilon[country]=upsilonPolicy
                                print 'upsilonPolicy', upsilonPolicy 
                                print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy  
          #   for country in McountryY:
          #       self.McountryYPolicy[country]=McountryY[country] 
          if time>=self.timeStarting and self.policyKind=='StraThreeInd' and time%20==0:
             maxg=0.005#max(LgY)[0]
             for country in McountryYReal:      
                 g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                 p=1-math.exp(-self.k*(maxg-g)) 
                 b=random.uniform(0,1)
                 print 
                 print 'country', country 
                 print 'g', g
                 print 'maxg',maxg
                 print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                 if b<p:
                    x=random.randint(0,len(self.LstraThree)-1)
                    if  McountryEtat[country].labPolicy!=self.LstraThree[x]:
                        McountryEtat[country].labPolicy=self.LstraThree[x]
                        upsilonPolicy=self.DstraUpsilonThree[self.LstraThree[x]]
                    for consumer in McountryConsumer[country]:
                        McountryConsumer[country][consumer].upsilon=upsilonPolicy
                    for firm in McountryFirm[country]:
                        McountryFirm[country][firm].upsilon=upsilonPolicy   
                    DcountryUpsilon[country]=upsilonPolicy  
                 print 'new McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy 
          if time>=self.timeStarting and self.policyKind=='StraTwo' and time%20==0:
             LgY=[] 
             for country in McountryYReal:
                 g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                 LgY.append([g,country])
             maxg=max(LgY)[0]
             maxCountry=max(LgY)[1]
             maxStra=McountryEtat[maxCountry].labPolicy 
             print
             print 'maxStra', maxStra
             print 'maxCountry', maxCountry
             print 'maxg', maxg
             print 'LgY', LgY 
             #print 'stop', stop      
             for country in McountryYReal:
                 a=random.uniform(0,1)
                 print 
                 print 'country', country
                 print 'a', a
                 print 'self.epsilon', self.epsilon
                 if a<self.epsilon and country!=maxCountry:
                    print 
                    print 'random'
                    #print 'country', country
                    #print 'a', a
                    print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy
                    #print 'stop', stop
                    g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                    p=1#1-math.exp(-self.k*(maxg-g)) 
                    b=0#random.uniform(0,1)   
                    if b<p:
                     x=random.randint(0,len(self.LstraTwo)-1)
                     if  McountryEtat[country].labPolicy!=self.LstraTwo[x]:
                        McountryEtat[country].labPolicy=self.LstraTwo[x]
                        upsilonPolicy=self.DstraUpsilonThree[self.LstraTwo[x]]
                        for consumer in McountryConsumer[country]:
                            McountryConsumer[country][consumer].upsilon=upsilonPolicy
                        for firm in McountryFirm[country]:
                            McountryFirm[country][firm].upsilon=upsilonPolicy   
                        DcountryUpsilon[country]=upsilonPolicy
                     print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy
                     print 'x', x
                     #print 'upsilonPolicy', upsilonPolicy
                     print 'random new strategy'
                     print 'self.LstraTwo[x]', self.LstraTwo[x]                       
                 else:
                      print 
                      print 'notRandom'
                      print 'country==maxCountry', country==maxCountry
                      if country!=maxCountry:
                         g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                         p=1-math.exp(-self.k*(maxg-g)) 
                         b=random.uniform(0,1)
                         print 
                         print 'country', country 
                         print 'g', g
                         print 'maxg',maxg
                         print 'maxg-g', maxg-g
                         print 'self.k*(maxg-g)', self.k*(maxg-g) 
                         print 'McountryYReal[country]', McountryYReal[country]
                         print 'self.McountryYRealPolicy[country]', self.McountryYRealPolicy[country] 
                         print 'p', p
                         print 'b', b      
                         print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                         print 'McountryEtat[maxCountry].labPolicy',  McountryEtat[maxCountry].labPolicy
                         if b<p:
                            if  McountryEtat[country].labPolicy!=maxStra:
                                McountryEtat[country].labPolicy=maxStra
                                upsilonPolicy=self.DstraUpsilonThree[maxStra]
                                for consumer in McountryConsumer[country]:
                                    McountryConsumer[country][consumer].upsilon=upsilonPolicy
                                for firm in McountryFirm[country]:
                                    McountryFirm[country][firm].upsilon=upsilonPolicy 
                                DcountryUpsilon[country]=upsilonPolicy
                                print 'upsilonPolicy', upsilonPolicy 
                                print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy  
          #   for country in McountryY:
          #       self.McountryYPolicy[country]=McountryY[country]  
          if time>=self.timeStarting and self.policyKind=='StraThreeCorr' and time%20==0:
             Lg=[]   
             LgY=[] 
             LgD=[]
             LdiffCumCA=[]
             for country in McountryYReal:
                 gD=0
                 diffCumCA=0 
                 if self.McountryDebtYPolicy[country]>0:
                    gD=(McountryDebtY[country]/self.McountryDebtYPolicy[country])**(1/5.0)-1
                    LgD.append([gD,country])  
                 if McountryY[country]>0 and self.McountryYPolicy[country]>0:
                    diffCumCA=McountryCumCA[country]/McountryY[country]-self.McountryCumCAPolicy[country]/self.McountryYPolicy[country]
                    LdiffCumCA.append([diffCumCA,country])
                 gY=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                 g=gY-gD  
                 #if gD<0.001:
                 LgY.append([gY,country]) 
                 Lg.append([g,country])
                 #if diffCumCA>=0.0 and gD<=0:
                 #   LgY.append([g,country]) 
             if len(Lg)>0:    
                maxg=max(Lg)[0]
                maxCountry=max(Lg)[1]
                maxStra=McountryEtat[maxCountry].labPolicy 
             if len(Lg)==0:    
                maxg='NA'#max(LgY)[0]
                maxCountry='NA'#max(LgY)[1]
                maxStra='NA'#McountryEtat[maxCountry].labPolicy 
             print
             print 'maxStra', maxStra
             print 'maxCountry', maxCountry
             print 'maxg', maxg
             print 'Lg', Lg 
             print 'LgY', LgY
             print 'LgD', LgD 
             print 'LdiffCumCA', LdiffCumCA  
             #print 'stop', stop      
             for country in McountryYReal:
                 a=random.uniform(0,1)
                 print 
                 print 'country', country
                 print 'a', a
                 print 'self.epsilon', self.epsilon
                 if a<self.epsilon:
                    print 
                    print 'random'
                    #print 'country', country
                    #print 'a', a
                    print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy
                    #print 'stop', stop
                    x=random.randint(0,len(self.LstraThree)-1)
                    if  McountryEtat[country].labPolicy!=self.LstraThree[x]:
                        McountryEtat[country].labPolicy=self.LstraThree[x]
                        upsilonPolicy=self.DstraUpsilonThree[self.LstraThree[x]]
                        for consumer in McountryConsumer[country]:
                            McountryConsumer[country][consumer].upsilon=upsilonPolicy
                        for firm in McountryFirm[country]:
                            McountryFirm[country][firm].upsilon=upsilonPolicy   
                        DcountryUpsilon[country]=upsilonPolicy
                    print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy
                    print 'x', x
                    #print 'upsilonPolicy', upsilonPolicy
                    #print 'self.LstraThree[x]', self.LstraThree[x]                       
                 if a>=self.epsilon and  maxStra!='NA':
                      print 
                      print 'notRandom'
                      print 'country==maxCountry', country==maxCountry
                      if country!=maxCountry:
                         gY=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                         gD=0
                         if self.McountryDebtYPolicy[country]>0:
                             gD=(McountryDebtY[country]/self.McountryDebtYPolicy[country])**(1/5.0)-1
                         g=gY-gD
                         p=1-math.exp(-self.k*(maxg-g)) 
                         b=random.uniform(0,1)
                         print 
                         print 'country', country 
                         print 'g', g
                         print 'maxg',maxg
                         print 'maxg-g', maxg-g
                         print 'self.k*(maxg-g)', self.k*(maxg-g) 
                         print 'McountryYReal[country]', McountryYReal[country]
                         print 'self.McountryYRealPolicy[country]', self.McountryYRealPolicy[country] 
                         print 'p', p
                         print 'b', b      
                         print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                         print 'McountryEtat[maxCountry].labPolicy',  McountryEtat[maxCountry].labPolicy
                         if b<p:
                            if  McountryEtat[country].labPolicy!=maxStra:
                                McountryEtat[country].labPolicy=maxStra
                                upsilonPolicy=self.DstraUpsilonThree[maxStra]
                                for consumer in McountryConsumer[country]:
                                    McountryConsumer[country][consumer].upsilon=upsilonPolicy
                                for firm in McountryFirm[country]:
                                    McountryFirm[country][firm].upsilon=upsilonPolicy 
                                DcountryUpsilon[country]=upsilonPolicy
                                print 'upsilonPolicy', upsilonPolicy 
                                print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
          if time>=self.timeStarting and self.policyKind=='StraG' and time%20==0:
             LgY=[] 
             for country in McountryYReal:
                 g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                 LgY.append([g,country])
             maxg=max(LgY)[0]
             maxCountry=max(LgY)[1]
             maxStra=McountryEtat[maxCountry].labPolicy 
             print
             print 'maxStra', maxStra
             print 'maxCountry', maxCountry
             print 'maxg', maxg
             print 'LgY', LgY 
             #print 'stop', stop      
             for country in McountryYReal:
                 g=(McountryYReal[country]/self.McountryYRealPolicy[country])**(1/5.0)-1
                 p=1-math.exp(-self.k*(maxg-g)) 
                 a=random.uniform(0,1)
                 print 
                 print 'country', country
                 print 'p', p
                 print 'a', a
                 if a<p:
                    if McountryEtat[country].labPolicy!=maxStra:
                       print 'in different strategy' 
                       print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                       McountryEtat[country].labPolicy=maxStra
                       upsilonPolicy=self.DstraUpsilonThree[maxStra]
                       for consumer in McountryConsumer[country]:
                           McountryConsumer[country][consumer].upsilon=upsilonPolicy
                       for firm in McountryFirm[country]:
                           McountryFirm[country][firm].upsilon=upsilonPolicy 
                       DcountryUpsilon[country]=upsilonPolicy
                       print 'upsilonPolicy', upsilonPolicy 
                       print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                    else:
                       print 'in same strategy' 
                       print 'McountryEtat[country].labPolicy',  McountryEtat[country].labPolicy
                       LpossibleStrategy=[]
                       for strategy in  self.LstraThree:
                           if strategy!=McountryEtat[country].labPolicy:
                              LpossibleStrategy.append(strategy)
                       x=random.randint(0,len(LpossibleStrategy)-1)
                       newStrategy=LpossibleStrategy[x]
                       McountryEtat[country].labPolicy=newStrategy
                       upsilonPolicy=self.DstraUpsilonThree[newStrategy]
                       for consumer in McountryConsumer[country]:
                           McountryConsumer[country][consumer].upsilon=upsilonPolicy
                       for firm in McountryFirm[country]:
                           McountryFirm[country][firm].upsilon=upsilonPolicy   
                       DcountryUpsilon[country]=upsilonPolicy
                       print 'upsilonPolicy', upsilonPolicy
                       print 'McountryEtat[country].labPolicy', McountryEtat[country].labPolicy       
          if time%20==0:
             for country in McountryYReal:
                 self.McountryYPolicy[country]=McountryY[country]
                 self.McountryYRealPolicy[country]=McountryYReal[country]
                 self.McountryDebtYPolicy[country]=McountryDebtY[country]  
                 self.McountryCumCAPolicy[country]=McountryCumCA[country]  
          if time>=self.timeStarting and self.policyKind=='austerity':
             LwageOnPhi=[]     
             Lphi=[]
             LY=[]  
             Ldebt=[]
             for country in McountryEtat:         
                 wageOnPhi=DcountryAvWage[country]/float(DglobalPhi[country])
                 LwageOnPhi.append(wageOnPhi)
                 Lphi.append(DglobalPhi[country]) 
                 LY.append(McountryY[country])
                 Ldebt.append(McountryEtat[country].Bonds)
             avWageOnPhi=sum(LwageOnPhi)/float(len(LwageOnPhi))
             avPhi=sum(Lphi)/float(len(Lphi))
             avY=sum(LY)/float(len(LY))
             avDebt=sum(Ldebt)/float(len(Ldebt))
             self.policy=self.policyKind                                        
             if self.policy=='austerity': 
                for country in McountryEtat: 
                    Lreturn=self.austerityPolicy(McountryY[country],McountryEtat[country].pastTaxCollected,\
                                McountryEtat[country].interestExpenditure,McountryEtat[country].addingSurplus,McountryEtat[country].G,\
                                McountryEtat[country].delta,McountryEtat[country].taxRate,DcountryAvWage[country],\
                                DglobalPhi[country],avWageOnPhi,McountryEtat[country].initialG,\
                                McountryAvPrice[country],McountryEtat[country].Bonds,avPhi,avY,\
                                McountryUnemployement[country],avDebt,McountryEtat[country].publicDeficit,DcumulativeDTBC[country],\
                                DcountryTradeBalance[country])  
                    McountryEtat[country].adjust=Lreturn[0] 
                    McountryEtat[country].realG=Lreturn[1]
                    McountryEtat[country].followingTaxRate=Lreturn[2] 
                    McountryEtat[country].G=Lreturn[1] 
          if time>=self.timeStarting and self.policyKind=='ModAus':
             LwageOnPhi=[]     
             Lphi=[]
             LY=[]  
             Ldebt=[]
             for country in McountryEtat:         
                 wageOnPhi=DcountryAvWage[country]/float(DglobalPhi[country])
                 LwageOnPhi.append(wageOnPhi)
                 Lphi.append(DglobalPhi[country]) 
                 LY.append(McountryY[country])
                 Ldebt.append(McountryEtat[country].Bonds)
             avWageOnPhi=sum(LwageOnPhi)/float(len(LwageOnPhi))
             avPhi=sum(Lphi)/float(len(Lphi))
             avY=sum(LY)/float(len(LY))
             avDebt=sum(Ldebt)/float(len(Ldebt))
             self.policy=self.policyKind                                        
             countryPolicy=0 
             Lreturn=self.austerityPolicy(McountryY[countryPolicy],McountryEtat[countryPolicy].pastTaxCollected,\
                     McountryEtat[countryPolicy].interestExpenditure,McountryEtat[country].addingSurplus,McountryEtat[countryPolicy].G,\
                     McountryEtat[countryPolicy].delta,McountryEtat[countryPolicy].taxRate,DcountryAvWage[countryPolicy],\
                     DglobalPhi[countryPolicy],avWageOnPhi,McountryEtat[countryPolicy].initialG,\
                     McountryAvPrice[countryPolicy],McountryEtat[countryPolicy].Bonds,avPhi,avY,\
                     McountryUnemployement[countryPolicy],avDebt,McountryEtat[countryPolicy].publicDeficit,DcumulativeDTBC[countryPolicy],\
                     DcountryTradeBalance[countryPolicy])  
             McountryEtat[countryPolicy].adjust=Lreturn[0] 
             McountryEtat[countryPolicy].realG=Lreturn[1]
             McountryEtat[countryPolicy].followingTaxRate=Lreturn[2] 
             McountryEtat[countryPolicy].G=Lreturn[1]
             McountryEtat[countryPolicy].labPolicy='yes'
             for consumer in McountryConsumer[countryPolicy]:
                 McountryConsumer[countryPolicy][consumer].upsilon=self.policyVariable
             for firm in McountryFirm[countryPolicy]:
                 McountryFirm[countryPolicy][firm].upsilon=self.policyVariable    
             DcountryUpsilon[countryPolicy]=self.policyVariable             
          #else:
          #  print 'stop', stop 
           
      def austerityPolicy(self,Y,pastTaxCollected,interestExpenditure,addingSurplus,G,delta,taxRate,wage,phi,\
                                 avWageOnPhi,initialG,price,debt,avPhi,avY,U,avDebt,publicDeficit,cumulativeDTBC,TradeBalance):
          adjust='no' 
          realG=G
          #if self.policy=='austerity' and  Y>0:
          if Y>0: 
                desiredG=min(price*phi*initialG,0.6*Y)
                desiredG=max(desiredG,0.4*Y) 
                expectedDeficit=publicDeficit/float(Y)
                maxPublicDeficit=self.maxPublicDeficitAusterity              
                if desiredG<=G and expectedDeficit>=maxPublicDeficit:
                   realG=G*(1-random.uniform(0,delta))
                   followingTaxRate=taxRate*(1+random.uniform(0,delta))
                if desiredG>G and expectedDeficit>=maxPublicDeficit:
                   realG=G
                   followingTaxRate=taxRate*(1+random.uniform(0,delta))
                if desiredG<=G and expectedDeficit<maxPublicDeficit:
                   realG=G*(1-random.uniform(0,delta))
                   followingTaxRate=taxRate*(1-random.uniform(0,delta))
                if desiredG>G and expectedDeficit<maxPublicDeficit:
                   realG=G*(1+random.uniform(0,delta))
                   followingTaxRate=taxRate
                adjust='yes'   
          Lreturn=[adjust,realG,followingTaxRate]        
          return Lreturn 

     

    
