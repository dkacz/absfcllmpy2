# matchingConsumption.py
import random
import math

class MatchingConsumption:
      def __init__(self,Lcountry,bound,propTradable):
         self.Lcountry=Lcountry
         self.bound=bound
         self.propTradableInitial=propTradable  
         self.propTradable=propTradable 

      def consuming(self,McountryConsumer,McountryFirm,t,McountryEtat,McountryBank,McountryCentralBank,McountryAvPrice,avPriceGlobalTradable,\
                    McountryAvPriceNotTradable):
          self.consumptionExtract(McountryFirm,McountryConsumer,McountryEtat,McountryAvPrice,t) 
          if self.propTradable>0.001:
             self.consumptionConsumer5(McountryConsumer,McountryFirm,t,McountryEtat,McountryBank,McountryCentralBank,McountryAvPrice,avPriceGlobalTradable)
          if 1-self.propTradable>0.001:  
             self.consumptionConsumer5NotTradable(McountryConsumer,McountryFirm,t,McountryEtat,McountryBank,\
                           McountryCentralBank,McountryAvPrice,McountryAvPriceNotTradable) 

      def consumptionExtract(self,McountryFirm,McountryConsumer,McountryEtat,McountryAvPrice,time):
          self.Lsale=[]
          self.DcountrySaleNotTradable={}   
          self.DcountrySale={} 
          self.nFirmTradable=0
          pos=0   
          for country in self.Lcountry:    
                  self.DcountrySaleNotTradable[country]=[]
                  for firm in McountryFirm[country]: 
                      McountryFirm[country][firm].lebalance.Lsold=[]  
                      McountryFirm[country][firm].sellingMoney=0 
                      ide=McountryFirm[country][firm].ide
                      p=McountryFirm[country][firm].price
                      x=McountryFirm[country][firm].mind.xProducing
                      xProd=McountryFirm[country][firm].productionEffective+McountryFirm[country][firm].inventory
                      size=McountryFirm[country][firm].A+McountryFirm[country][firm].loanReceived                       
                      firmcountry=McountryFirm[country][firm].country
                      McountryFirm[country][firm].lebalance.Lsold=[p,x,0,xProd]
                      McountryFirm[country][firm].xSold=0 
                      omega=McountryFirm[country][firm].omega
                      if xProd>0 and McountryFirm[country][firm].closing=='no' and McountryFirm[country][firm].tradable=='yes':
                         self.Lsale.append([p,xProd,ide,firmcountry,0,pos,omega])
                         self.nFirmTradable=self.nFirmTradable+1  
                      if xProd>0 and McountryFirm[country][firm].closing=='no' and McountryFirm[country][firm].tradable=='no':
                         self.DcountrySaleNotTradable[country].append([p,xProd,ide,firmcountry,0,pos,omega])                           
                         pos=pos+1
          self.Lconsuming=[]
          self.DconsumingNotTradable={}  
          for country in McountryConsumer:
              self.DconsumingNotTradable[country]=[]
              posCons=0
              for consumer in McountryConsumer[country]:
                  ide=McountryConsumer[country][consumer].ide
                  McountryConsumer[country][consumer].Expenditure=0
                  McountryConsumer[country][consumer].ExpenditureTradable=0
                  McountryConsumer[country][consumer].ExpenditureNotTradable=0   
                  McountryConsumer[country][consumer].Import=0   
                  McountryConsumer[country][consumer].pastLConsumptionEff=[]
                  for consuPast in McountryConsumer[country][consumer].LConsumptionEff:
                      McountryConsumer[country][consumer].pastLConsumptionEff.append(consuPast[2]) 
                  McountryConsumer[country][consumer].LConsumptionEff=[] 
                  McountryConsumer[country][consumer].quantityConsumed=0
                  McountryConsumer[country][consumer].quantityConsumedTradable=0  
                  McountryConsumer[country][consumer].quantityConsumedNotTradable=0
                  McountryConsumer[country][consumer].orderBankDeposit()  
                  if McountryConsumer[country][consumer].Consumption>0: 
                     self.Lconsuming.append([ide,country])
                     self.DconsumingNotTradable[country].append([ide,country])
                  posCons=posCons+1
               
      def consumptionConsumer5(self,McountryConsumer,McountryFirm,t,McountryEtat,McountryBank,McountryCentralBank,McountryAvPrice,avPriceGlobalTradable):
             random.shuffle(self.Lconsuming)
             for Lconsumer in self.Lconsuming:
                 consumer=Lconsumer[0]
                 country=Lconsumer[1]     
                 consumption=McountryConsumer[country][consumer].Consumption*(self.propTradable) ####
                 lenSale=len(self.Lsale)
                 LconsumptionU=[]
                 length=self.bound
                 if  lenSale<length:
                     length=lenSale
                 LchoiceGood=[] 
                 if lenSale>0: 
                    LlenSale=range(lenSale)
                    LchoiceGood=random.sample(LlenSale,length)
                 for good in LchoiceGood:
                     position=good
                     p=self.Lsale[position][0]
                     firmide=self.Lsale[position][2]  
                     x=self.Lsale[position][1] 
                     omega=self.Lsale[position][6]
                     firmcountry=self.Lsale[position][3]
                     if x>0 and consumption>0:
                        avPrice=avPriceGlobalTradable
                        u=McountryConsumer[country][consumer].ordinating(p,firmide,omega,avPrice) ###
                        LconsumptionU.append([u,position])   
                     else:
                         u=0
                 controlConsumption=0 
                 controlConsumptionP=0  
                 totalPayment=0
                 if len(LconsumptionU)>0:
                    LconsumptionU.sort()
                    LconsumptionU.reverse()
                    avPrice=avPriceGlobalTradable
                    LdelSale=[]
                    LdelSaleIde=[]
                    j=0
                    lj=len(LconsumptionU) 
                    while j<lj:
                          position=LconsumptionU[j][1]
                          p=self.Lsale[position][0]
                          x=self.Lsale[position][1]
                          firmide=self.Lsale[position][2]
                          firmcountry=self.Lsale[position][3]
                          pos=self.Lsale[position][5] 
                          if p==0:
                             quantityConsumed=x
                          if p!=0: 
                             if x>consumption/float(p):
                                quantityConsumed=consumption/float(p)   
                             elif x<=consumption/float(p):
                                  quantityConsumed=x
                          consumption=consumption-quantityConsumed*p
                          controlConsumption=controlConsumption+quantityConsumed*p              
                          controlConsumptionP=controlConsumptionP+quantityConsumed*p
                          payment=quantityConsumed*p
                          McountryConsumer[country][consumer].LConsumptionEff.append([p,quantityConsumed,firmide,firmcountry])
                          McountryConsumer[country][consumer].Expenditure=McountryConsumer[country][consumer].Expenditure+quantityConsumed*p
                          McountryConsumer[country][consumer].ExpenditureTradable=McountryConsumer[country][consumer].ExpenditureTradable+quantityConsumed*p 
                          totalPayment=totalPayment+payment
                          McountryConsumer[country][consumer].quantityConsumed=McountryConsumer[country][consumer].quantityConsumed+quantityConsumed 
                          McountryConsumer[country][consumer].quantityConsumedTradable=\
                          McountryConsumer[country][consumer].quantityConsumedTradable+quantityConsumed
                          if firmcountry!=country:
                             McountryConsumer[country][consumer].Import=McountryConsumer[country][consumer].Import+quantityConsumed*p 
                          self.Lsale[position][1]=self.Lsale[position][1]-quantityConsumed
                          self.Lsale[position][4]=self.Lsale[position][4]+quantityConsumed
                          McountryFirm[firmcountry][firmide].lebalance.Lsold[2]=\
                                                 McountryFirm[firmcountry][firmide].lebalance.Lsold[2]+quantityConsumed 
                          McountryFirm[firmcountry][firmide].xSold=McountryFirm[firmcountry][firmide].xSold+quantityConsumed 
                          McountryFirm[firmcountry][firmide].sellingMoney=\
                                                 McountryFirm[firmcountry][firmide].sellingMoney+payment  
                          if  self.Lsale[position][1]<0.0000001:
                              LdelSale.append(position) 
                              LdelSaleIde.append(firmide) 
                          if consumption<=0:
                             lj=0
                             if consumption<-0.01:
                                print 'stop', stop
                          if consumption>0:
                             j=j+1
                    shift=0
                    McountryConsumer[country][consumer].paying(totalPayment,McountryBank,McountryCentralBank) 
                    LdelSale.sort()
                    for posi in LdelSale:
                        correctPosition=posi-shift
                        del self.Lsale[correctPosition]                   
                        shift=shift+1
                    

      def consumptionConsumer5NotTradable(self,McountryConsumer,McountryFirm,t,McountryEtat,McountryBank,McountryCentralBank,\
                                          McountryAvPrice,McountryAvPriceNotTradable):
        for country in McountryConsumer:
             random.shuffle(self.DconsumingNotTradable[country])
             for Lconsumer in self.DconsumingNotTradable[country]:
                 consumer=Lconsumer[0]
                 country=Lconsumer[1]  
                 consumption=McountryConsumer[country][consumer].Consumption*(1-self.propTradable)####
                 lenSale=len(self.DcountrySaleNotTradable[country])
                 LconsumptionU=[]
                 length=self.bound
                 if  lenSale<length:
                     length=lenSale
                 LchoiceGood=[] 
                 if lenSale>0: 
                    LlenSale=range(lenSale)
                    LchoiceGood=random.sample(LlenSale,length)           
                 for good in LchoiceGood:
                     position=good
                     p=self.DcountrySaleNotTradable[country][position][0]
                     firmide=self.DcountrySaleNotTradable[country][position][2]  
                     x=self.DcountrySaleNotTradable[country][position][1] 
                     omega=self.DcountrySaleNotTradable[country][position][6]   
                     if x>0 and consumption>0:
                        avPrice=McountryAvPriceNotTradable[country]
                        u=McountryConsumer[country][consumer].ordinating(p,firmide,omega,avPrice)
                        LconsumptionU.append([u,position])
                     else:
                         u=0
                 controlConsumption=0 
                 controlConsumptionP=0  
                 totalPayment=0 
                 if len(LconsumptionU)>0:
                    LconsumptionU.sort()
                    LconsumptionU.reverse()
                    avPrice=McountryAvPriceNotTradable[country]
                    LdelSale=[]
                    LdelSaleIde=[]
                    j=0
                    lj=len(LconsumptionU) 
                    while j<lj:
                          position=LconsumptionU[j][1]  
                          p=self.DcountrySaleNotTradable[country][position][0]
                          x=self.DcountrySaleNotTradable[country][position][1]
                          firmide=self.DcountrySaleNotTradable[country][position][2]
                          firmcountry=self.DcountrySaleNotTradable[country][position][3]
                          pos=self.DcountrySaleNotTradable[country][position][5] 
                          if p==0:
                             quantityConsumed=x
                          if p!=0: 
                             if x>consumption/float(p):
                                quantityConsumed=consumption/float(p)   
                             elif x<=consumption/float(p):
                                  quantityConsumed=x
                          consumption=consumption-quantityConsumed*p
                          controlConsumption=controlConsumption+quantityConsumed*p              
                          controlConsumptionP=controlConsumptionP+quantityConsumed*p
                          payment=quantityConsumed*p
                          if consumption<-0.0001:
                             print 'stop', stop
                          McountryConsumer[country][consumer].LConsumptionEff.append([p,quantityConsumed,firmide,firmcountry])
                          McountryConsumer[country][consumer].Expenditure=McountryConsumer[country][consumer].Expenditure+quantityConsumed*p
                          McountryConsumer[country][consumer].ExpenditureNotTradable=\
                                   McountryConsumer[country][consumer].ExpenditureNotTradable+quantityConsumed*p 
                          totalPayment=totalPayment+payment
                          McountryConsumer[country][consumer].quantityConsumed=McountryConsumer[country][consumer].quantityConsumed+quantityConsumed
                          McountryConsumer[country][consumer].quantityConsumedNotTradable=\
                          McountryConsumer[country][consumer].quantityConsumedNotTradable+quantityConsumed  
                          if firmcountry!=country:
                             McountryConsumer[country][consumer].Import=McountryConsumer[country][consumer].Import+quantityConsumed*p 
                          self.DcountrySaleNotTradable[country][position][1]=self.DcountrySaleNotTradable[country][position][1]-quantityConsumed
                          self.DcountrySaleNotTradable[country][position][4]=self.DcountrySaleNotTradable[country][position][4]+quantityConsumed
                          McountryFirm[firmcountry][firmide].lebalance.Lsold[2]=\
                                                 McountryFirm[firmcountry][firmide].lebalance.Lsold[2]+quantityConsumed
                          McountryFirm[firmcountry][firmide].xSold=McountryFirm[firmcountry][firmide].xSold+quantityConsumed 
                          McountryFirm[firmcountry][firmide].sellingMoney=\
                                                 McountryFirm[firmcountry][firmide].sellingMoney+payment  
                          if  self.DcountrySaleNotTradable[country][position][1]<0.0000001:
                              LdelSale.append(position) 
                              LdelSaleIde.append(firmide) 
                          if consumption<=0:
                             lj=0
                             if consumption<-0.0001:
                                print 'stop', stop
                          if consumption>0:
                             j=j+1
                    shift=0
                    McountryConsumer[country][consumer].paying(totalPayment,McountryBank,McountryCentralBank)
                    LdelSale.sort()
                    for posi in LdelSale:
                        correctPosition=posi-shift
                        del self.DcountrySaleNotTradable[country][correctPosition]                   
                        shift=shift+1
                  
  

