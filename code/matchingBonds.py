#matchingbonds.py
import random

class MatchingBonds:

      def allocatingBonds(self,McountryBank,McountryCentralBank,McountryEtat):
          self.extractingBondsOpen(McountryBank,McountryEtat)
          self.matchingBondsOpen(McountryBank,McountryCentralBank,McountryEtat)  

      def extractingBondsOpen(self,McountryBank,McountryEtat):          
          self.MbondsDemand=[]
          self.MbondsSupply=[]
          for country  in McountryEtat:
              leverage=McountryEtat[country].leverage
              nTranches=100.0
              for i in range(int(nTranches)):
                  McountryEtat[country].bondsAllocated=0 
                  self.MbondsSupply.append([country,McountryEtat[country].bondsSupply/float(nTranches),0,leverage,i])  
              for bank in McountryBank[country]:
                  bankIde=bank
                  McountryBank[country][bank].Mbonds=[] 
                  McountryBank[country][bank].demandingBonds()
                  demand=McountryBank[country][bank].bondsDemand 
                  self.MbondsDemand.append([bankIde,demand,0,country]) 
        
      def matchingBondsOpen(self,McountryBank,McountryCentralBank,McountryEtat):
                  self.creditBondInflow={}
                  self.creditBondOutflow={}
                  for country in McountryCentralBank:
                      self.creditBondInflow[country]=0
                      self.creditBondOutflow[country]=0
                  random.shuffle(self.MbondsDemand) 
                  i=0
                  li=len(self.MbondsDemand)
                  while i<li:
                        random.shuffle(self.MbondsSupply)    
                        bankIde=self.MbondsDemand[i][0]    
                        j=0
                        lj=len(self.MbondsSupply)
                        while j<lj:
                                 supply=self.MbondsSupply[j][1]
                                 ideBank=self.MbondsDemand[i][0] 
                                 demand=self.MbondsDemand[i][1]  
                                 leverage=self.MbondsSupply[j][3]
                                 countryBank=self.MbondsDemand[i][3] 
                                 countryEtat=self.MbondsSupply[j][0]
                                 probBond=McountryBank[countryBank][ideBank].computeProbBuyingBondLoan(leverage)                             
                                 a=random.uniform(0,1)
                                 if a>probBond:
                                    demand=0                                 
                                 if demand>=supply:
                                    bondExchange=supply
                                 if demand<supply:
                                    bondExchange=demand                                
                                 if bondExchange>0.001:
                                    self.MbondsDemand[i][1]=self.MbondsDemand[i][1]-bondExchange
                                    self.MbondsDemand[i][2]=self.MbondsDemand[i][2]+bondExchange
                                    self.MbondsSupply[j][1]=self.MbondsSupply[j][1]-bondExchange
                                    self.MbondsSupply[j][2]=self.MbondsSupply[j][2]+bondExchange         
                                    rBonds=McountryEtat[countryEtat].rBonds                              
                                    McountryBank[countryBank][ideBank].buyingBondsOpen(bondExchange,rBonds,McountryCentralBank,countryEtat)
                                    McountryEtat[countryEtat].bondsAllocated=McountryEtat[countryEtat].bondsAllocated+bondExchange
                                    McountryEtat[countryEtat].LiquidityEtat=McountryEtat[countryEtat].LiquidityEtat+bondExchange
                                    McountryCentralBank[countryEtat].DepositEtatCentralBank=\
                                         McountryCentralBank[countryEtat].DepositEtatCentralBank+bondExchange
                                    if countryBank!=countryEtat:
                                       self.creditBondInflow[countryEtat]=self.creditBondInflow[countryEtat]+bondExchange
                                       self.creditBondOutflow[countryBank]=self.creditBondOutflow[countryBank]+bondExchange  
                                       McountryCentralBank[countryEtat].bondRepeymentInflow=McountryCentralBank[countryEtat].bondRepeymentInflow+bondExchange
                                       McountryCentralBank[countryBank].bondRepeymentOutflow=McountryCentralBank[countryBank].bondRepeymentOutflow+bondExchange  
                                 if self.MbondsDemand[i][1]<=0.001:
                                    lj=0
                                 ja=j
                                 if self.MbondsSupply[j][1]>=0.001:
                                    j=j+1 
                                 if self.MbondsSupply[ja][1]<0.001:
                                    del self.MbondsSupply[ja]
                                    lj=lj-1                                  
                        i=i+1
                  for country in McountryEtat:
                      McountryEtat[country].bondsToCentralBank(McountryCentralBank)
             
                  
