# matchingLaborCapital.py
import random

class MatchingLaborCapital:
      def __init__(self,bound):
          self.bound=bound  
          #self.jobDuration=jobDuration

      def bargaining(self,McountryFirm,McountryConsumer,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL,t):
          for country in McountryConsumer:
              for consumer in McountryConsumer[country]:
                  McountryConsumer[country][consumer].laborSupply(McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL) 
              for firm in McountryFirm[country]:
                  McountryFirm[country][firm].wageOffered(McountryUnemployement,McountryPastUnemployement,\
                                  McountryYL,McountryPastYL,t,McountryConsumer)             
              
                       

      def working(self,McountryFirm,McountryConsumer,McountryEtat,McountryBank,McountryCentralBank,McountryUnemployement):
          self.laborExtract(McountryFirm,McountryConsumer,McountryEtat,McountryUnemployement)
          #self.laborMatchStillEmployed(McountryFirm,McountryConsumer,McountryEtat,McountryUnemployement)
          self.laborMatch(McountryFirm,McountryConsumer,McountryEtat,McountryUnemployement)
          self.laborDisMatch(McountryFirm,McountryConsumer,McountryEtat,McountryBank,McountryCentralBank) 

   
      def laborMatchStillEmployed(self,McountryFirm,McountryConsumer,McountryEtat,McountryUnemployement):
          for country in self.McountryDemandLabor: 
              for firm in self.McountryDemandLabor[country]:
                  McountryFirm[country][firm].LalreadyEmployed=[]
                  McountryFirm[country][firm].LnotStillEmployed=[]
                  for employed in  McountryFirm[country][firm].Lemployed:
                      if employed[2]>0.01:
                         McountryFirm[country][firm].LalreadyEmployed.append(employed)
                      if employed[2]<0.01:
                         McountryFirm[country][firm].LnotStillEmployed.append(employed)
                  McountryFirm[country][firm].Lemployed=[]
                  McountryFirm[country][firm].nAlreadyEmployed=len(McountryFirm[country][firm].LalreadyEmployed)
                  McountryFirm[country][firm].nNotStillEmployed=len(McountryFirm[country][firm].LnotStillEmployed) 
                  random.shuffle(McountryFirm[country][firm].LalreadyEmployed)
                  if McountryFirm[country][firm].nAlreadyEmployed>=McountryFirm[country][firm].nWorkerDesiredEffective:
                     nEmployedAgain=McountryFirm[country][firm].nWorkerDesiredEffective 
                     nOldWorkerEmployedAgain=0
                  if McountryFirm[country][firm].nAlreadyEmployed<McountryFirm[country][firm].nWorkerDesiredEffective:
                     nEmployedAgain=McountryFirm[country][firm].nAlreadyEmployed     
                  nEmployedAgainReally=0     
                  random.shuffle(McountryFirm[country][firm].LnotStillEmployed)            
                  if McountryFirm[country][firm].nWorkerDesiredEffective>0 and  McountryFirm[country][firm].nAlreadyEmployed>0:
                     for employed in  McountryFirm[country][firm].LalreadyEmployed[0:nEmployedAgain]:
                         ideWorker=employed[0]
                         wOffered=McountryFirm[country][firm].w
                         wDemanded=McountryConsumer[country][ideWorker].wageDemanded
                         #if McountryFirm[country][firm].bargaining=='yes':
                         #   wDemanded=McountryFirm[country][firm].w  
                         #if McountryConsumer[country][ideWorker].wageDemanded>wOffered:
                         #   McountryConsumer[country][ideWorker].wageDemanded=wOffered
                         #wDemanded=McountryConsumer[country][ideWorker].wageDemanded                        
                         if ideWorker=='C0n0':
                            print 
                            print 'in second match'
                            print 'firm', firm
                            print 'employed', employed
                            print 'wOffered', wOffered
                            print 'wDemanded', wDemanded 
                            print 'McountryFirm[country][firm].wageExpected', McountryFirm[country][firm].wageExpected   
                            print 'McountryFirm[country][firm].wageBeforeBargaining', McountryFirm[country][firm].wageBeforeBargaining
                            print 'McountryFirm[country][firm].dis', McountryFirm[country][firm].dis
                            print 'McountryFirm[country][firm].probDis', McountryFirm[country][firm].probDis  
                            print 'McountryFirm[country][firm].bargaining', McountryFirm[country][firm].bargaining 
                            print 'McountryFirm[country][firm].direction', McountryFirm[country][firm].direction  
                         if wOffered>=wDemanded:
                         #if wOffered>=0:
                            jobDuration=employed[2]-1
                            #if jobDuration==0:
                            #   print 'stop', stop  
                            labor=McountryConsumer[country][ideWorker].ls
                            self.McountrySupplyLabor[country][ideWorker][4]=self.McountrySupplyLabor[country][ideWorker][4]+labor
                            self.McountrySupplyLabor[country][ideWorker][5]=self.McountrySupplyLabor[country][ideWorker][5]+labor*wOffered  
                            self.McountryDemandLabor[country][firm][2]=self.McountryDemandLabor[country][firm][2]+labor
                            self.McountryDemandLabor[country][firm][4]=self.McountryDemandLabor[country][firm][4]+wOffered*labor
                            self.McountryDemandLabor[country][firm][6]=self.McountryDemandLabor[country][firm][6]-wOffered*labor
                            self.McountryDemandLabor[country][firm][12]=self.McountryDemandLabor[country][firm][12]-labor
                            self.McountryDemandLabor[country][firm][13]=self.McountryDemandLabor[country][firm][13]-labor
                            McountryConsumer[country][ideWorker].LwOffered.append(wOffered)   
                            McountryConsumer[country][ideWorker].gPhi=McountryFirm[country][firm].gPhi 
                            McountryFirm[country][firm].Lemployed.append([ideWorker,labor,jobDuration,wOffered,wDemanded])
                            nEmployedAgainReally=nEmployedAgainReally+1
                            if ideWorker=='C0n0':
                                  print 
                                  print 'in second match'
                                  print 'firm', firm
                                  print '[ideWorker,labor,jobDuration,wOffered]', [ideWorker,labor,jobDuration,wOffered,wDemanded]
                                  print
                  if McountryFirm[country][firm].nWorkerDesiredOptimalEffective>nEmployedAgainReally:
                        if McountryFirm[country][firm].nNotStillEmployed<=\
                              (McountryFirm[country][firm].nWorkerDesiredOptimalEffective-nEmployedAgainReally):
                           nOldWorkerEmployedAgain=McountryFirm[country][firm].nNotStillEmployed 
                        if McountryFirm[country][firm].nNotStillEmployed>\
                               (McountryFirm[country][firm].nWorkerDesiredOptimalEffective-nEmployedAgainReally):
                           nOldWorkerEmployedAgain=McountryFirm[country][firm].nWorkerDesiredOptimalEffective-nEmployedAgainReally 
                  if McountryFirm[country][firm].nWorkerDesiredOptimalEffective-nEmployedAgainReally>0\
                           and  McountryFirm[country][firm].nNotStillEmployed>0:
                     for employed in  McountryFirm[country][firm].LnotStillEmployed[0:nOldWorkerEmployedAgain]:
                         ideWorker=employed[0]
                         wOffered=McountryFirm[country][firm].w
                         #McountryConsumer[country][ideWorker].laborSupply(McountryUnemployement)
                         self.McountrySupplyLabor[country][ideWorker][0]=McountryConsumer[country][ideWorker].wageDemanded
                         wDemanded=self.McountrySupplyLabor[country][ideWorker][0]
                         jobDuration=McountryFirm[country][firm].jobDuration
                         if wOffered>=wDemanded:
                            labor=McountryConsumer[country][ideWorker].ls
                            self.McountrySupplyLabor[country][ideWorker][4]=self.McountrySupplyLabor[country][ideWorker][4]+labor
                            self.McountrySupplyLabor[country][ideWorker][5]=self.McountrySupplyLabor[country][ideWorker][5]+labor*wOffered  
                            self.McountryDemandLabor[country][firm][2]=self.McountryDemandLabor[country][firm][2]+labor
                            self.McountryDemandLabor[country][firm][4]=self.McountryDemandLabor[country][firm][4]+wOffered*labor
                            self.McountryDemandLabor[country][firm][6]=self.McountryDemandLabor[country][firm][6]-wOffered*labor
                            self.McountryDemandLabor[country][firm][12]=self.McountryDemandLabor[country][firm][12]-labor
                            self.McountryDemandLabor[country][firm][13]=self.McountryDemandLabor[country][firm][13]-labor
                            McountryConsumer[country][ideWorker].LwOffered.append(wOffered) 
                            McountryConsumer[country][ideWorker].gPhi=McountryFirm[country][firm].gPhi  
                            McountryFirm[country][firm].Lemployed.append([ideWorker,labor,jobDuration,wOffered,wDemanded])
                            if ideWorker=='C0n0':
                                  print 
                                  print 'in third match'
                                  print 'firm', firm 
                                  print '[ideWorker,labor,jobDuration,wOffered]', [ideWorker,labor,jobDuration,wOffered,wDemanded]
                                  print
                           
      def laborExtract(self,McountryFirm,McountryConsumer,McountryEtat,McountryUnemployement): 
          self.McountryDemandLabor={}
          self.McountrySupplyLabor={}
          for country in McountryFirm:
              self.McountryDemandLabor[country]={}
              self.McountrySupplyLabor[country]={}
              LdemandLabor=[]
              LsupplyLabor=[]
              posFirm=0  
              #counter=0
              for firm in  McountryFirm[country]:
                  #if counter==0:
                  #   print 
                  #   print 'country', country
                  #   print 'McountryFirm[country][firm].jobDuration', McountryFirm[country][firm].jobDuration
                  #   print   
                  #   counter=1
                  Deposit=0 
                  McountryFirm[country][firm].Lemployed=[]
                  for bank in McountryFirm[country][firm].Mdeposit:
                      Deposit=Deposit+McountryFirm[country][firm].Mdeposit[bank][2]
                  if McountryFirm[country][firm].closing=='no': 
                     McountryFirm[country][firm].initialCycleVariable()   
                     #McountryFirm[country][firm].Lemployed=[]             
                     totAdisp=0
                     totAdispEffective=0 
                     McountryFirm[country][firm].workerSearching=0
                     x=McountryFirm[country][firm].mind.xProducing
                     nworkerPr=McountryFirm[country][firm].workForceNumberDesired
                     w=McountryFirm[country][firm].w   
                     Adisp=nworkerPr*w
                     AdispEffective=McountryFirm[country][firm].lebalance.Aspending+McountryFirm[country][firm].loanReceived 
                     p=McountryFirm[country][firm].price 
                     nWorkerPossible=AdispEffective/float(w)
                     nWorkerDesiredEffective=min(McountryFirm[country][firm].workForceNumberDesired,nWorkerPossible) 
                     nWorkerDesiredEffective=nWorkerDesiredEffective
                     nWorkerDesiredOptimalEffective=min(McountryFirm[country][firm].workForceNumberDesiredOptimal,nWorkerPossible)
                     nWorkerDesiredOptimalEffective=nWorkerDesiredOptimalEffective
                     McountryFirm[country][firm].nWorkerDesiredEffective=nWorkerDesiredEffective 
                     McountryFirm[country][firm].nWorkerDesiredOptimalEffective=nWorkerDesiredOptimalEffective
                     if nWorkerDesiredEffective<nWorkerDesiredOptimalEffective-0.01:
                        print  
                        print 'nWorkerDesiredOptimalEffective', nWorkerDesiredOptimalEffective
                        print 'nWorkerDesiredEffective',  nWorkerDesiredEffective 
                        print  'stop', stop
                     #LdemandLabor.append([McountryFirm[country][firm].ide,x,0,\
                     #                     McountryFirm[country][firm].country,0,posFirm,AdispEffective,\
                     #                     0,'firm',country,0,p,nWorkerDesiredEffective])
                     self.McountryDemandLabor[country][firm]=[McountryFirm[country][firm].ide,x,0,\
                                          McountryFirm[country][firm].country,0,posFirm,AdispEffective,\
                                          0,'firm',country,0,p,nWorkerDesiredEffective,nWorkerDesiredOptimalEffective]
                     totAdisp=totAdisp+Adisp
                     totAdispEffective=totAdispEffective+AdispEffective 
                     posFirm=posFirm+1
              #Consumers  
              posConsumer=0     
              for consumer in McountryConsumer[country]:   
                  McountryConsumer[country][consumer].pastL=McountryConsumer[country][consumer].l    
                  McountryConsumer[country][consumer].laborSupplyAlreadyRevised='no'  
                  #McountryConsumer[country][consumer].laborSupply(McountryUnemployement)           
                  McountryConsumer[country][consumer].l=0
                  McountryConsumer[country][consumer].laborIncome=0
                  McountryConsumer[country][consumer].innovationIncome=0
                  McountryConsumer[country][consumer].LwOffered=[]
                  McountryConsumer[country][consumer].Lphip=[]
                  McountryConsumer[country][consumer].gPhi=0 
                  wageDemanded=McountryConsumer[country][consumer].wageDemanded
                  LfirmConsumer=[]
                  #LsupplyLabor.append([wageDemanded,McountryConsumer[country][consumer].w,\
                  #                      McountryConsumer[country][consumer].ide,posConsumer,0,0,LfirmConsumer])
                  self.McountrySupplyLabor[country][consumer]=[wageDemanded,McountryConsumer[country][consumer].w,\
                                        McountryConsumer[country][consumer].ide,posConsumer,0,0,LfirmConsumer]
                  posConsumer=posConsumer+1

      def laborMatch(self,McountryFirm,McountryConsumer,McountryEtat,McountryUnemployement):
          for country in McountryConsumer:
              LsupplyLabor=[]
              LdemandLabor=[]  
              for consumer in self.McountrySupplyLabor[country]:
                  if self.McountrySupplyLabor[country][consumer][4]<0.01: 
                     #McountryConsumer[country][consumer].laborSupply(McountryUnemployement)
                     self.McountrySupplyLabor[country][consumer][0]=McountryConsumer[country][consumer].wageDemanded
                     LsupplyLabor.append(self.McountrySupplyLabor[country][consumer])
              for firm in self.McountryDemandLabor[country]:
                  if self.McountryDemandLabor[country][firm][12]>0.01:
                     LdemandLabor.append(self.McountryDemandLabor[country][firm]) 
              random.shuffle(LsupplyLabor)
              #LsupplyLabor.sort()
              for supply in LsupplyLabor:
                  wageDemanded=supply[0]
                  posWorker=supply[3]
                  ideWorker=supply[2]
                  lenJob=len(LdemandLabor)
                  length=self.bound#McountryConsumer[country][ideWorker].upsilon2
                  if  lenJob<length:
                      length=lenJob
                  LchoiceJob=[] 
                  if lenJob>0: 
                     LlenJob=range(lenJob)
                     LchoiceJob=random.sample(LlenJob,length)
                  LdelMcountryJob=[]
                  LwageOffered=[]
                  for job in LchoiceJob: 
                      posDemand=job              
                      if LdemandLabor[posDemand][8]=='firm':       
                         firmide=LdemandLabor[posDemand][0]   
                         countryFirm=LdemandLabor[posDemand][3]    
                         wOffered=McountryFirm[countryFirm][firmide].w
                         McountryFirm[countryFirm][firmide].workerSearching=McountryFirm[countryFirm][firmide].workerSearching+1 
                         if countryFirm!=country:
                            print 'stop', stop   
                         nWorkerDesiredOptimalEffective=LdemandLabor[posDemand][13]
                         nWorkerDesiredEffective=LdemandLabor[posDemand][12]
                         money=LdemandLabor[posDemand][6]                        
                         #LwageOffered.append([wOffered,posDemand,nWorkerDesiredOptimalEffective,money]) 
                         LwageOffered.append([wOffered,posDemand,nWorkerDesiredOptimalEffective,money]) 
                  random.shuffle(LwageOffered)
                  LwageOffered.sort()
                  LwageOffered.reverse()  
                  for wageOffer in LwageOffered:
                      posDemand=wageOffer[1]
                      posFirm=LdemandLabor[posDemand][5]
                      firmide=LdemandLabor[posDemand][0]   
                      countryFirm=LdemandLabor[posDemand][3]
                      p=McountryFirm[countryFirm][firmide].price
                      wOffered=McountryFirm[countryFirm][firmide].w
                      nWorkerDesiredOptimalEffective=LdemandLabor[posDemand][13]
                      nWorkerDesiredEffective=LdemandLabor[posDemand][12]
                      phi=McountryFirm[countryFirm][firmide].phi
                      jobDuration=McountryFirm[countryFirm][firmide].jobDuration
                      #if nWorkerDesiredEffective>0.001 and LdemandLabor[posDemand][6]>=0.001\
                      #   and supply[4]<=McountryConsumer[country][ideWorker].ls-0.001 and wOffered>=wageDemanded:
                      if McountryConsumer[country][ideWorker].ide=='zC0n0':
                         print
                         print 'ideWorker', ideWorker
                         print 'wOffered', wOffered
                         print 'wageDemanded', wageDemanded   
                         print 'nWorkerDesiredOptimalEffective', nWorkerDesiredOptimalEffective
                         print 'lenJob', lenJob 
                      if nWorkerDesiredOptimalEffective>=0.01 and LdemandLabor[posDemand][6]>=0.0\
                         and supply[4]<=McountryConsumer[country][ideWorker].ls-0.01 and wOffered>=wageDemanded:
                      #if nWorkerDesiredOptimalEffective>=1.0 and LdemandLabor[posDemand][6]>=0.0\
                      #   and supply[4]<=McountryConsumer[country][ideWorker].ls-0.99 and wOffered>=wageDemanded:
                         Adisp=LdemandLabor[posDemand][6] 
                         demandQuantity=LdemandLabor[posDemand][1]
                         supplyLabor=McountryConsumer[country][ideWorker].ls-supply[4]
                         if supplyLabor>=nWorkerDesiredOptimalEffective:
                            labor=nWorkerDesiredOptimalEffective
                         if supplyLabor<nWorkerDesiredOptimalEffective:
                            labor=supplyLabor
                         if McountryConsumer[country][ideWorker].ide=='zC0n0':
                            print
                            print 'ideWorker', ideWorker 
                            print 'labor', labor
                            print 'nWorkerDesiredOptimalEffective', nWorkerDesiredOptimalEffective
                            print 'wOffered', wageDemanded
                         if labor>=0.01:
                            if McountryConsumer[country][ideWorker].ide=='zC0n0':
                               print
                               print 'ideWorker', ideWorker 
                               print 'labor', labor
                               print 'LwageOffered', LwageOffered
                               #print 'stop', stop
                            supply[4]=supply[4]+labor
                            supply[5]=supply[5]+labor*wOffered  
                            LdemandLabor[posDemand][2]=LdemandLabor[posDemand][2]+labor
                            LdemandLabor[posDemand][4]=LdemandLabor[posDemand][4]+wOffered*labor
                            LdemandLabor[posDemand][6]=LdemandLabor[posDemand][6]-wOffered*labor
                            LdemandLabor[posDemand][13]=LdemandLabor[posDemand][13]-labor
                            LdemandLabor[posDemand][12]=LdemandLabor[posDemand][12]-labor
                            if labor>=0.01:
                               McountryConsumer[country][ideWorker].LwOffered.append(wOffered)   
                               McountryConsumer[country][ideWorker].Lphip.append(p*phi)
                               McountryConsumer[country][ideWorker].gPhi=McountryFirm[countryFirm][firmide].gPhi
                               McountryFirm[countryFirm][firmide].Lemployed.append([ideWorker,labor,jobDuration,wOffered,wageDemanded])
                               #print
                               #print 'ideWorker',ideWorker
                               #print 'stop', stop 
                               if ideWorker=='zC0n0':
                                  print 
                                  print 'in first match'
                                  print 'firmide', firmide
                                  print '[ideWorker,labor,jobDuration,wOffered]', [ideWorker,labor,jobDuration,wOffered,wageDemanded]
                                  print 'wOffered', wOffered
                                  print 'wDemanded', wageDemanded 
                                  #print 'McountryFirm[countryFirm][firmide].direction', McountryFirm[countryFirm][firmide].direction
                                  #print 'McountryFirm[countryFirm][firmide].bargaining', McountryFirm[countryFirm][firmide].bargaining 
                                  #if  McountryFirm[countryFirm][firmide].direction=='stay':
                                  #    print 'stop', stop    
                         if LdemandLabor[posDemand][6]<-0.001:
                            print 'stop', stop
                         if LdemandLabor[posDemand][1]<=0.001 or LdemandLabor[posDemand][6]<=0.001:
                            if LdemandLabor[posDemand][1]<-0.001:  
                               print 'stop', stop
                         if LdemandLabor[posDemand][6]<=0.001 or LdemandLabor[posDemand][12]<=0.001 or LdemandLabor[posDemand][13]<=0.001:
                            self.McountryDemandLabor[country][firmide]=LdemandLabor[posDemand]
                            LdelMcountryJob.append(posDemand)   
                         if supply[4]>McountryConsumer[country][ideWorker].ls+0.001:
                            print 'stop', stop
                         if supply[4]>McountryConsumer[country][ideWorker].ls-0.001:
                            li=0
                            break                      
                  LdelMcountryJob.sort()
                  shift=0   
                  for posi in LdelMcountryJob:
                          correctPosition=posi-shift
                          del LdemandLabor[correctPosition]                   
                          shift=shift+1 
                  if ideWorker=='zC0n0':
                     print 'LdelMcountryJob',LdelMcountryJob 
              for demandLabor in LdemandLabor:
                  firm=demandLabor[0]
                  self.McountryDemandLabor[country][firm].append(demandLabor)
              for supplyLabor in LsupplyLabor:
                  consumer=supplyLabor[2]
                  self.McountrySupplyLabor[country][consumer]=supplyLabor
                                                   
      def laborDisMatch(self,McountryFirm,McountryConsumer,McountryEtat,McountryBank,McountryCentralBank):
          for country in McountryFirm:
              for firm in  McountryFirm[country]:
                  McountryFirm[country][firm].l=0
                  McountryFirm[country][firm].laborExpenditure=0
                  McountryFirm[country][firm].innovationExpenditure=0
              sumExpInnovation=0 
              for firm in self.McountryDemandLabor[country]:
                     posFirm=self.McountryDemandLabor[country][firm][5]
                     firmide=self.McountryDemandLabor[country][firm][0]   
                     if McountryFirm[country][firmide].l>McountryFirm[country][firmide].nWorkerDesiredEffective:
                        print
                        print 'firm', firm 
                        print 'McountryFirm[country][firmide].l',McountryFirm[country][firmide].l
                        print 'McountryFirm[country][firmide].nWorkerDesiredEffective', McountryFirm[country][firmide].nWorkerDesiredEffective  
                        print 'stop', stop              
                     McountryFirm[country][firmide].l=McountryFirm[country][firmide].l+self.McountryDemandLabor[country][firm][2]
                     McountryFirm[country][firmide].laborExpenditure=self.McountryDemandLabor[country][firm][4]#
                     wagebill=self.McountryDemandLabor[country][firm][4]
                     AdispEffective=McountryFirm[country][firmide].lebalance.Aspending+McountryFirm[country][firmide].loanReceived 
                     resources=0 
                     if  AdispEffective>McountryFirm[country][firmide].workForceExpenditureNoInnovation: 
                         resources=AdispEffective-McountryFirm[country][firmide].workForceExpenditureNoInnovation 
                     McountryFirm[country][firmide].innovationExpenditure=0 
                     if McountryFirm[country][firmide].l>0:
                        #expenditureTotWorker=McountryFirm[country][firmide].workForceInnovationExpenditureDesired*\
                        #   (McountryFirm[country][firmide].l/float(McountryFirm[country][firmide].nWorkerDesiredEffective)) 
                        McountryFirm[country][firmide].innovationExpenditure=min(resources,\
                                          McountryFirm[country][firmide].workForceInnovationExpenditureDesired) 
                        McountryFirm[country][firmide].innovationExpenditurePerWorker=McountryFirm[country][firmide].innovationExpenditure/float(McountryFirm[country][firmide].l) 
                     sumExpInnovation=sumExpInnovation+McountryFirm[country][firmide].innovationExpenditure 
                     sumExpWorker=0 
                     for worker in  McountryFirm[country][firmide].Lemployed:
                         ideworker=worker[0] 
                         laborworker=worker[1] 
                         #worker[2]=worker[2]-1
                         McountryConsumer[country][ideworker].innovationIncome=\
                          McountryConsumer[country][ideworker].innovationIncome+\
                                           McountryFirm[country][firmide].innovationExpenditurePerWorker*laborworker 
                         sumExpWorker=sumExpWorker+McountryFirm[country][firmide].innovationExpenditurePerWorker*laborworker    
                         if McountryConsumer[country][ideworker].innovationIncome<-0.0001:
                            print 'stop', stop 
                     if sumExpWorker>McountryFirm[country][firmide].innovationExpenditure+0.001 or\
                         sumExpWorker<McountryFirm[country][firmide].innovationExpenditure-0.001:
                         print 'stop', stop
                     wagebill= McountryFirm[country][firmide].laborExpenditure+McountryFirm[country][firmide].innovationExpenditure
                     #if McountryFirm[country][firmide].innovationExpenditure>0.001:
                     #   print 'stop', stop  
                     McountryFirm[country][firmide].paying(wagebill,McountryBank,McountryCentralBank)
              for consumer in self.McountrySupplyLabor[country]:
                  posConsumer=self.McountrySupplyLabor[country][consumer][3]
                  ideConsumer=self.McountrySupplyLabor[country][consumer][2]
                  if self.McountrySupplyLabor[country][consumer][2]!=McountryConsumer[country][ideConsumer].ide:
                     print 'stop', stop
                  McountryConsumer[country][ideConsumer].l=self.McountrySupplyLabor[country][consumer][4]
                  McountryConsumer[country][ideConsumer].laborIncome=self.McountrySupplyLabor[country][consumer][5]
                  if McountryConsumer[country][ideConsumer].l>0.0:
                     wOffered=McountryConsumer[country][ideConsumer].laborIncome/float(McountryConsumer[country][ideConsumer].l)
                     McountryConsumer[country][ideConsumer].wOffered=wOffered
                     McountryConsumer[country][ideConsumer].maxwOffered=max(McountryConsumer[country][ideConsumer].LwOffered)
                     McountryConsumer[country][ideConsumer].minwOffered=min(McountryConsumer[country][ideConsumer].LwOffered)
                     #McountryConsumer[country][ideConsumer].minphip=min(McountryConsumer[country][ideConsumer].Lphip)
                     McountryConsumer[country][ideConsumer].averagewOffered=\
                                  sum(McountryConsumer[country][ideConsumer].LwOffered)/\
                                      float(len(McountryConsumer[country][ideConsumer].LwOffered))
                  if McountryConsumer[country][ideConsumer].l<=0.0:
                     McountryConsumer[country][ideConsumer].wOffered=0
                     McountryConsumer[country][ideConsumer].maxwOffered=0
                     McountryConsumer[country][ideConsumer].averagewOffered=0
                     McountryConsumer[country][ideConsumer].minwOffered=0
                     McountryConsumer[country][ideConsumer].minphip=0
                  McountryConsumer[country][ideConsumer].laborIncome=McountryConsumer[country][ideConsumer].laborIncome+\
                                McountryConsumer[country][ideConsumer].innovationIncome
                  McountryConsumer[country][ideConsumer].receiving(McountryConsumer[country][ideConsumer].laborIncome,\
                                   McountryBank,McountryCentralBank)

                                              
