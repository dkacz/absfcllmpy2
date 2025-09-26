#matchingcredit.py
import random

class MatchingCredit:

      def creditNetworkEvolution(self,McountryFirm,McountryBank,McountryCentralBank,DglobalPhiNotTradable,DglobalPhiTradable,\
                                 avPhiGlobalTradable):
          self.extractingCreditOpen(McountryFirm,McountryBank,DglobalPhiNotTradable,DglobalPhiTradable,avPhiGlobalTradable)
          self.matchCreditOpen(McountryFirm,McountryBank,McountryCentralBank)   

      def extractingCreditOpen(self,McountryFirm,McountryBank,DglobalPhiNotTradable,DglobalPhiTradable,avPhiGlobalTradable):
          self.MloanDemand=[]
          self.MloanSupply=[]
          self.ListLoanSupply={} 
          avPhiGlobalNotTradable=0
          for country in DglobalPhiNotTradable:
              avPhiGlobalNotTradable=avPhiGlobalNotTradable+DglobalPhiNotTradable[country]
          avPhiGlobalNotTradable=avPhiGlobalNotTradable/len(DglobalPhiNotTradable)
          for country  in McountryFirm:
              posFirm=0
              for firm in McountryFirm[country]:
                  McountryFirm[country][firm].orderCreditor()
                  McountryFirm[country][firm].Mloan={} 
                  McountryFirm[country][firm].loanReceived=0
                  McountryFirm[country][firm].losses=0
                  McountryFirm[country][firm].interestRate=0 
                  if McountryFirm[country][firm].loanDemand>0.001:
                     leverage=McountryFirm[country][firm].loanDemand/float(McountryFirm[country][firm].A) 
                     if McountryFirm[country][firm].tradable=='yes':
                        if avPhiGlobalTradable>0:
                           relPhi=McountryFirm[country][firm].phi/avPhiGlobalTradable
                        else:
                           relPhi=1.0
                     if McountryFirm[country][firm].tradable=='no':
                        if avPhiGlobalNotTradable>0:
                           relPhi=McountryFirm[country][firm].phi/avPhiGlobalNotTradable
                        else: 
                           relPhi=1.0
                     loanDemand=[McountryFirm[country][firm].ide,posFirm,McountryFirm[country][firm].country,\
                                McountryFirm[country][firm].loanDemand,0,leverage,relPhi]
                     self.MloanDemand.append(loanDemand)
                  posFirm=posFirm+1
              posBank=0
              for bank in McountryBank[country]:
                  McountryBank[country][bank].Mloan={}
                  McountryBank[country][bank].loanAllocated=0
                  McountryBank[country][bank].losses=0
                  McountryBank[country][bank].serviceReceived=0
                  McountryBank[country][bank].volumeLoanReceived=0 
                  McountryBank[country][bank].loanSupply=McountryBank[country][bank].mu1*McountryBank[country][bank].A#float('inf')
                  McountryBank[country][bank].maxLoanFirm=McountryBank[country][bank].loanSupply 
                  McountryBank[country][bank].checkNetWorth()
                  if McountryBank[country][bank].loanSupply>0.001:
                     loanSupply=[McountryBank[country][bank].ide,posBank,McountryBank[country][bank].country,\
                                 McountryBank[country][bank].loanSupply,0,McountryBank[country][bank].maxLoanFirm]
                     self.MloanSupply.append(loanSupply)
                     self.ListLoanSupply[McountryBank[country][bank].ide]=posBank   
                     posBank=posBank+1

      def matchCreditOpen(self,McountryFirm,McountryBank,McountryCentralBank):
                  self.creditCapitalInflow={}
                  self.creditCapitalOutflow={}
                  for country in McountryFirm:
                      self.creditCapitalInflow[country]=0
                      self.creditCapitalOutflow[country]=0 
                  random.shuffle(self.MloanDemand)   
                  i=0
                  li=len(self.MloanDemand)
                  while i<li:
                        random.shuffle(self.MloanSupply) 
                        posFirm=self.MloanDemand[i][1]
                        ideFirm=self.MloanDemand[i][0]                      
                        leverage=self.MloanDemand[i][5] 
                        countryFirm=self.MloanDemand[i][2]
                        Lcreditor=McountryFirm[countryFirm][ideFirm].Lcreditor
                        j=0
                        lj=len(self.MloanSupply) 
                        while j<lj:
                              if (self.MloanSupply[j][0] in McountryFirm[countryFirm][ideFirm].Lcreditor)==False:
                                 maxLoanFirm=self.MloanSupply[j][5]
                                 supply=self.MloanSupply[j][3]
                                 demand=self.MloanDemand[i][3]                              
                                 ideBank=self.MloanSupply[j][0]
                                 posBank=self.MloanSupply[j][1] 
                                 leverage=self.MloanDemand[i][5] 
                                 relPhi=self.MloanDemand[i][6]
                                 countryBank=self.MloanSupply[j][2] 
                                 probLoan=McountryBank[countryBank][ideBank].computeProbProvidingLoan(leverage,relPhi)
                                 loanOffered=min(maxLoanFirm,supply) 
                                 a=random.uniform(0,1)
                                 if a>probLoan:
                                    loanOffered=0                                 
                                 if demand>=loanOffered:
                                    loan=loanOffered
                                 if demand<loanOffered:
                                    loan=demand                               
                                 if loan>0.001:
                                    self.MloanDemand[i][3]=self.MloanDemand[i][3]-loan
                                    self.MloanDemand[i][4]=self.MloanDemand[i][4]+loan
                                    self.MloanSupply[j][3]=self.MloanSupply[j][3]-loan
                                    self.MloanSupply[j][4]=self.MloanSupply[j][4]+loan                                    
                                    if  ideBank!=McountryBank[countryBank][ideBank].ide:
                                        print 'stop', stop   
                                    interestRate=McountryBank[countryBank][ideBank].computeInterestRate(leverage)
                                    interestRateDeposit=McountryBank[countryBank][ideBank].rDeposit 
                                    McountryFirm[countryFirm][ideFirm].receavingLoan(ideBank,loan,interestRate,\
                                                                     interestRateDeposit,countryBank,McountryBank,McountryCentralBank)
                                    McountryBank[countryBank][ideBank].loanCreation(ideFirm,loan,interestRate,countryFirm,McountryCentralBank)   
                                    if countryFirm!=countryBank:
                                       self.creditCapitalInflow[countryFirm]=self.creditCapitalInflow[countryFirm]+loan
                                       self.creditCapitalOutflow[countryBank]=self.creditCapitalOutflow[countryBank]+loan  
                                       McountryCentralBank[countryFirm].moneyInflow=McountryCentralBank[countryFirm].moneyInflow+loan
                                       McountryCentralBank[countryBank].moneyOutflow=McountryCentralBank[countryBank].moneyOutflow+loan
                                 if self.MloanDemand[i][3]<=0.001:
                                    lj=0
                                 ja=j
                                 if self.MloanSupply[j][3]>=0.001:
                                    j=j+1 
                                 if self.MloanSupply[ja][3]<0.001:
                                    del self.MloanSupply[ja]
                                    lj=lj-1                                  
                              else:
                                   j=j+1
                        i=i+1
      


 
                            
      
        
                              
                             
       

