# firm.py
from mind import *
from lebalance import *
import csv
from time import *
import math
from llm_runtime import firm_enabled, get_client, get_firm_guard_caps, log_fallback

class Firm:
      def __init__(self,ide,country,A,phi,Lcountry,w,folder,name,run,delta,dividendRate,xi,iota,\
                        upsilon,gamma,deltaInnovation,avPrice,Fcost,ni,minMarkUp,eX,theta,upsilon2,jobDuration):               
          self.ide=ide
          self.country=country 
          self.A=A
          self.phi=phi
          self.Lcountry=Lcountry
          self.w=w
          self.PreviouswAv=self.w
          self.delta=delta  
          self.Fcost=Fcost  
          self.upsilon=upsilon
          self.minMarkUp=minMarkUp
          x=(self.A/float(self.w))*phi
          self.xE=max(x,eX)
          lForecasted=x/float(phi)
          p=avPrice
          #self.minMarkUp=0.2 
          if p<(1.0+self.minMarkUp)*(self.w/float(phi)):
             p=(1.0+self.minMarkUp)*(self.w/float(phi))
          #if p<(1.0+0.2)*(self.w/float(phi)):
          #   p=(1.0+0.2)*(self.w/float(phi))
          self.price=p   
          self.markUp=self.price*(phi/float(self.w))-1  
          profit=p*x-self.A
          Resources=lForecasted*self.w
          self.dividendRate=dividendRate 
          self.productionEffective=0
          self.spendingA=self.A
          self.xSold=0  
          xSold=0
          xProd=0
          loan=0        
          self.lebalance=Lebalance(delta,self.country,self.ide,self.dividendRate,iota,gamma,deltaInnovation,self.Fcost,ni,xi,self.A)
          self.gamma=gamma  
          self.mind=Mind(ide,delta,self.country,self.minMarkUp,self.xE,theta)
          self.folder=folder
          self.name=name
          self.run=run
          self.llm_tick=0
          self.omega=1*random.uniform(0,2*math.pi) 
          self.theta=theta
          self.jobDuration=jobDuration 
          # for the first cycle
          self.Lowner=[]
          self.l=0 
          self.closing='no' 
          self.ListOwners=[]
          self.loanReceived=0
          self.Mloan={}
          self.loanDemand=0
          self.lebalance.loanDemand=self.loanDemand
          self.ResourceAvailable=0
          self.PreviousA=self.A
          self.xi=xi
          self.iota=iota  
          self.PastA=self.A
          self.CapitalDismiss=0
          self.Downer={}
          self.Mdeposit={}
          self.depositInterest=0
          self.profit=0
          self.pastProfit=0 
          self.profitRate=0
          self.nWorkerDesiredEffective=lForecasted
          self.nWorkerDesiredOptimalEffective=lForecasted  
          self.innovationExpenditure=0 
          self.ratioGamma=self.gamma  
          self.firmSaving=0 
          self.pastFirmSaving=0
          self.laborExpenditure=0
          self.inventory=0
          self.pastInventory=0 
          self.changeInventory=0
          self.changeInventoryValue=0 
          self.inventoryValue=0 
          self.upsilon2=upsilon2 
          self.deltaLabor=self.delta 
          self.wageMax=float('inf')
          self.wageMin=0.0#float('inf') 
          self.Lemployed=[]
          self.pastPhi=self.phi 
          self.pastPrice=self.price
          #self.gPhi=self.price*self.phi
          self.gPhi=0
          self.alpha=0.8  
          self.wageExpected=self.w 
          self.memory=4#12
          self.LpastEmployment=[]
          for i in range(self.memory):
              self.LpastEmployment.append(0)
          self.memPastEmployment=0    
          self.loanEffReceived=0  
          #self.LpastEmployment=[0,0,0,0] 
          #self.LpastEmployment=[0,0,0,0,0,0,0,0,0,0]    
          
          
      def learning(self):       
          # Eq. 12-14 (Caiani et al. 2016): pricing/expec update pre-LLM.
          if self.closing!='no':
             return

          previous_price=self.price
          baseline=self._baseline_pricing_update()
          guard_caps=get_firm_guard_caps()

          if not firm_enabled():
             return

          client=get_client()
          if client is None:
             log_fallback('firm','client_unavailable')
             self._apply_baseline(baseline)
             return

          payload, feature_error=self._build_llm_payload(previous_price,baseline,guard_caps)
          if payload is None:
             log_fallback('firm','feature_pack_missing',feature_error)
             self._apply_baseline(baseline)
             return
          decision,error=client.decide_firm(payload)
          if error:
             reason='error'
             detail=None
             if isinstance(error,dict):
                reason=error.get('reason','error')
                detail=error.get('detail')
             log_fallback('firm',reason,detail)
             self._apply_baseline(baseline)
             return

          if not self._validate_llm_decision(decision):
             log_fallback('firm','invalid_response')
             self._apply_baseline(baseline)
             return

          self._apply_llm_decision(previous_price,baseline,decision,guard_caps)

      def _baseline_pricing_update(self):
          self.mind.alphaParameterSmooth16(self.phi,self.w,self.inventory,self.pastInventory,\
                                           self.price,self.productionEffective,self.xSold)
          self.pastPrice=self.price
          self.price=self.mind.pSelling
          unit_cost=self._unit_cost()
          price_floor=max(unit_cost,(1.0+self.minMarkUp)*unit_cost)
          return {
              'price': self.price,
              'expected_demand': getattr(self.mind,'xE',0.0),
              'producing': getattr(self.mind,'xProducing',0.0),
              'price_floor': price_floor,
          }

      def _apply_baseline(self,baseline):
          self.price=baseline.get('price',self.price)
          self.mind.pSelling=self.price
          self.mind.xE=baseline.get('expected_demand',self.mind.xE)
          self.mind.xProducing=baseline.get('producing',getattr(self.mind,'xProducing',0.0))

      def _build_llm_payload(self,previous_price,baseline,guard_caps):
          """Construct the Decider payload including guard caps and feature pack.

          Feature ranges (pre-decision state):
              - ``inv_ratio`` ≥ 0: inventory ÷ max(expected demand, 1e-9).
              - ``backlog`` ≥ 0: max(0, expected demand − offered supply).
              - ``delta_price_comp`` ∈ ℝ: baseline price − last-period price.
              - ``last_sales`` ≥ 0: quantity sold in the previous tick.
              - ``capacity`` ≥ 0: effective production carried from the last tick.
              - ``liquidity`` ∈ ℝ: working capital flagged by the accounting block.
              - ``sector_code`` ∈ {``tradable``, ``non_tradable``}.
          Missing/non-finite values trigger a baseline fallback.
          """

          unit_cost=self._unit_cost()
          price_floor=baseline.get('price_floor',unit_cost)
          production_effective=getattr(self,'productionEffective',0.0)
          expected=self._safe_numeric(baseline.get('expected_demand',0.0))
          if expected is None:
             expected=0.0
          max_step=guard_caps.get('max_price_step',0.04)
          max_bias=guard_caps.get('max_expectation_bias',0.04)
          baseline_price=baseline.get('price',previous_price)
          features,missing=self._compute_feature_pack(previous_price,baseline_price,expected,production_effective)
          if missing:
             return None, ','.join(missing)
          payload={
              'schema_version':'1.0',
              'run_id':getattr(self,'run',0),
              'tick':getattr(self,'llm_tick',0),
              'country_id':self.country,
              'firm_id':self.ide,
              'price':previous_price,
              'unit_cost':features['unit_cost'],
              'inventory':self.inventory,
              'inventory_value':getattr(self,'inventoryValue',0.0),
              'production_effective':production_effective,
              'baseline':{
                  'price':baseline_price,
                  'expected_demand':expected,
              },
              'guards':{
                  'max_price_step':max_step,
                  'max_expectation_bias':max_bias,
                  'price_floor':price_floor,
              },
          }
          payload.update({
              'inv_ratio':features['inv_ratio'],
              'backlog':features['backlog'],
              'delta_price_comp':features['delta_price_comp'],
              'last_sales':features['last_sales'],
              'capacity':features['capacity'],
              'liquidity':features['liquidity'],
              'sector_code':features['sector_code'],
          })
          return payload, None

      def _validate_llm_decision(self,decision):
          if not isinstance(decision,dict):
             return False
          direction=decision.get('direction')
          if direction not in ('up','down','hold'):
             return False
          try:
             decision['price_step']=float(decision.get('price_step',0.0))
          except (TypeError,ValueError):
             return False
          try:
             decision['expectation_bias']=float(decision.get('expectation_bias',0.0))
          except (TypeError,ValueError):
             decision['expectation_bias']=0.0
          return True

      def _apply_llm_decision(self,previous_price,baseline,decision,guard_caps):
          max_step=max(0.0,float(guard_caps.get('max_price_step',self.delta)))
          step=decision.get('price_step',0.0)
          if step<0:
             step=0.0
          if step>max_step:
             log_fallback('firm','price_step_clamped')
             step=max_step

          direction=decision.get('direction')
          price_floor=baseline.get('price_floor',self._unit_cost())
          baseline_price=baseline.get('price',previous_price)
          if direction=='up':
             new_price=previous_price*(1.0+step)
          elif direction=='down':
             new_price=previous_price*(1.0-step)
          elif direction=='hold':
             new_price=previous_price
          else:
             new_price=baseline_price
          if new_price<price_floor:
             log_fallback('firm','price_floor_enforced')
             new_price=price_floor
          self.price=new_price
          self.mind.pSelling=self.price

          max_bias=max(0.0,float(guard_caps.get('max_expectation_bias',max_step)))
          bias=decision.get('expectation_bias',0.0)
          if bias>max_bias:
             log_fallback('firm','expectation_bias_clamped_high')
             bias=max_bias
          if bias<-max_bias:
             log_fallback('firm','expectation_bias_clamped_low')
             bias=-max_bias
          baseline_expected=baseline.get('expected_demand',0.0)
          target_expected=baseline_expected*(1.0+bias)
          if target_expected<0.0:
             target_expected=0.0
          self.mind.xE=target_expected
          theta=getattr(self.mind,'theta',0.0)
          inventory=self.inventory
          new_producing=target_expected*(1+theta)-inventory
          if new_producing<0.0:
             new_producing=0.0
          self.mind.xProducing=new_producing

      def _unit_cost(self):
          if self.phi==0:
             return 0.0
          return self.w/float(self.phi)

      def _compute_feature_pack(self,previous_price,baseline_price,expected,production_effective):
          inventory=max(0.0,getattr(self,'inventory',0.0))
          offered=getattr(self,'xOfferedEffective',production_effective+inventory)
          offered=max(0.0,offered)
          inv_ratio=0.0
          if expected>0:
             inv_ratio=inventory/expected
          backlog=max(0.0,expected-offered)
          delta_price_comp=baseline_price-previous_price
          last_sales=max(0.0,getattr(self,'xSold',0.0))
          capacity=max(0.0,production_effective)
          liquidity=self._safe_numeric(getattr(self,'ResourceAvailable',0.0))
          if liquidity is None:
             liquidity=self._safe_numeric(getattr(self,'sellingMoney',0.0))
          unit_cost=self._safe_numeric(self._unit_cost())
          inv_ratio=self._safe_numeric(inv_ratio)
          backlog=self._safe_numeric(backlog)
          delta_price_comp=self._safe_numeric(delta_price_comp)
          last_sales=self._safe_numeric(last_sales)
          capacity=self._safe_numeric(capacity)
          sector_code=self._resolve_sector_code()
          numeric_map={
              'unit_cost':unit_cost,
              'inv_ratio':inv_ratio,
              'backlog':backlog,
              'delta_price_comp':delta_price_comp,
              'last_sales':last_sales,
              'capacity':capacity,
              'liquidity':liquidity,
          }
          missing=[label for (label,value) in numeric_map.items() if value is None]
          if sector_code is None:
             missing.append('sector_code')
          if missing:
             return {}, missing
          return {
              'unit_cost':numeric_map['unit_cost'],
              'inv_ratio':numeric_map['inv_ratio'],
              'backlog':numeric_map['backlog'],
              'delta_price_comp':numeric_map['delta_price_comp'],
              'last_sales':numeric_map['last_sales'],
              'capacity':numeric_map['capacity'],
              'liquidity':numeric_map['liquidity'],
              'sector_code':sector_code,
          }, []

      def _resolve_sector_code(self):
          category=getattr(self,'tradable',None)
          if category=='yes':
             return 'tradable'
          if category=='no':
             return 'non_tradable'
          return None

      def _safe_numeric(self,value):
          try:
             numeric=float(value)
          except (TypeError,ValueError):
             return None
          if math.isnan(numeric) or math.isinf(numeric):
             return None
          return numeric

      def changingInventory(self):
          if self.xOfferedEffective>=self.xSold:
             self.pastInventory=self.inventory 
             self.inventory=1.0*(self.xOfferedEffective-self.xSold)
             self.changeInventory=self.inventory-self.pastInventory
             self.changeInventoryValue=(self.w/self.phi)*(self.inventory-self.pastInventory)
             self.inventoryValue=(self.w/self.phi)*(self.inventory)

      def checkExistence(self):
          self.PreviousA=self.A
          if self.A<=self.Fcost or self.A<=0.001:
             self.closing='yes' 

      def existence(self,McountryBank,McountryCentralBank):          
          self.PreviousA=self.A 
          self.pastX=self.productionEffective
          self.receiving(self.sellingMoney,McountryBank,McountryCentralBank)  
          self.depositInterest=0 
          for bank in self.Mdeposit:
                 self.depositInterest=self.depositInterest+self.Mdeposit[bank][2]*self.Mdeposit[bank][3]
          self.receivingInterestDeposit(McountryBank,McountryCentralBank)
          if self.closing=='yes':
             self.A=self.A+self.depositInterest
             self.pastDepositInterest=self.depositInterest 
             self.profitRate=0
          if self.closing=='no':
             self.debtService=0
             for bank in self.Mloan:
                 self.debtService=self.debtService+self.Mloan[bank][2]*self.Mloan[bank][3] 
             self.netInterest=self.debtService-self.depositInterest
             self.pastDepositInterest=self.depositInterest 
             self.lebalance.rebalancing(self.A,self.netInterest,self.innovationExpenditure,self.loanReceived,\
                                  self.laborExpenditure,self.xSold,self.price)
             self.toWorkers=self.lebalance.toWorkers
             self.loanUsed=self.lebalance.loanUsed
             self.loanEffReceived=self.lebalance.loanEffReceived
             self.Entrance=self.lebalance.Entrance
             self.profitRate=self.lebalance.totProfit/float(self.A)                
             self.A=self.A+self.lebalance.totProfit
             self.pastProfit=self.profit
             self.profit=self.lebalance.totProfit
             self.netProfit=self.profit   
             self.loanNotUsed=self.lebalance.loanNotUsed 
             if self.loanReceived<-0.000000001:
                print 'stop', stop 
             self.loanReimboursed=0
             inte=0
             for bank in self.Mdeposit:
                 inte=inte+self.Mdeposit[bank][2]*self.Mdeposit[bank][3]   
          if self.closing=='no' and self.A>self.Fcost*self.w:
             for bank in self.Mloan:
                 bankIde=self.Mloan[bank][1]
                 loanValue=self.Mloan[bank][2]
                 service=self.Mloan[bank][2]*self.Mloan[bank][3] 
                 countryBank=self.Mloan[bank][4]
                 loanVolume=loanValue+service    
                 self.repayingLoan(bankIde,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank)    
             self.checkNetWorth()    
          if  self.closing=='yes' or self.A<=self.Fcost*self.w:   
             self.closing='yes' 
             self.ResourceAvailable=0
             if self.A>=0:
                self.CapitalDismiss=self.A
                self.loanReimboursed=self.loanReceived+self.debtService  
             if self.A<0:
                self.CapitalDismiss=0
                self.loanReimboursed=self.A+self.loanReceived+self.debtService               
             self.A=0
          if self.A<-0.000001:
             print 'stop', stop 

      def distributingDividends(self,McountryConsumer,McountryBank,McountryCentralBank):
          self.dividending()
          self.capitalVariation(McountryConsumer,McountryBank,McountryCentralBank)

      def dividending(self):
          self.lebalance.dividending(self.A,self.closing,self.netProfit,self.loanDemand)
          self.dividends=self.lebalance.dividends
          self.pastFirmSaving=self.firmSaving 
          self.firmSaving=self.netProfit-self.dividends
          self.A=self.A-self.dividends 

      def alreadyEmployedCompute(self):
          nAlreadyEmployed=0 
          for employed in  self.Lemployed:
              if employed[2]>0.01:
                 nAlreadyEmployed=nAlreadyEmployed+1
          return  nAlreadyEmployed            

      def productionDesired(self,McountryBank,McountryCentralBank,time,McountryAvPrice):
          self.loanDemand=0 
          pastSold_x=self.xSold
          if self.closing=='no':
                nAlreadyEmployed=self.alreadyEmployedCompute()   
                self.lebalance.producingObjectives4(self.w,self.A,self.phi,self.mind.xProducing,self.price,nAlreadyEmployed)
                self.lebalance.innovatingAttempt(self.A, McountryCentralBank[self.country].rDiscount,\
                                                 self.mind.xProducing,self.price,self.w,self.inventory,self.profit,self.mind.xE,self.xSold,self.pastPrice)
                self.ResourceAvailable=self.lebalance.ResourceAvailable
                p=self.price
                self.lebalance.loanDemanding(self.A,self.w,self.phi,p,McountryCentralBank[self.country].rDiscount,self.xi)  
                self.loanDemand=self.lebalance.loanDemand
                self.workForceNumberDesired=self.lebalance.workForceNumberDesired
                self.workForceExpenditureNoInnovation=self.lebalance.workForceExpenditureNoInnovation
                self.workForceNumberInnovation=self.lebalance.workForceNumberInnovation
                self.workForceNumberProduction=self.lebalance.workForceNumberProduction 
                self.workForceNumberDesiredOptimal=self.lebalance.workForceNumberProduction  
                self.workForceInnovationExpenditureDesired=self.lebalance.workForceInnovationExpenditureDesired 
                self.ratioGamma=0
                if self.workForceExpenditureNoInnovation>0:
                   self.ratioGamma=self.workForceInnovationExpenditureDesired/float(self.workForceExpenditureNoInnovation)
          if self.closing=='yes':
             self.loanDemand=0 

      def capitalVariation(self,McountryConsumer,McountryBank,McountryCentralBank):
          self.PastA=self.A
          self.ResourceAvailable=0
          Ashare=0 
          if  self.PreviousA+self.CapitalDismiss>0:
              Ashare=self.A/float(self.PreviousA+self.CapitalDismiss)                  
          if self.PreviousA+self.CapitalDismiss<-0.000000000001 and len(self.ListOwners)>0:
             print 'stop', stop  
          if self.CapitalDismiss>0.00001 and self.closing=='no':
             print 'stop', stop   
          lastA=0
          Avariation=self.A-self.PreviousA        
          totalPayement=0 
          for consumerIde in self.Downer:             
              if self.closing=='yes':
                    ConsumerA=McountryConsumer[self.country][consumerIde].DLA[self.ide][2] 
                    DismissShareCapital=self.CapitalDismiss*ConsumerA/float(self.PreviousA)
                    DividendShare=self.dividends*ConsumerA/float(self.PreviousA)   
                    McountryConsumer[self.country][consumerIde].capitalDismiss=\
                    McountryConsumer[self.country][consumerIde].capitalDismiss\
                                                               +DismissShareCapital
                    McountryConsumer[self.country][consumerIde].DividendShare=\
                    McountryConsumer[self.country][consumerIde].DividendShare\
                                                               +DividendShare
                    totalPayement=totalPayement+DismissShareCapital+DividendShare
                    oldShare=McountryConsumer[self.country][consumerIde].DLA[self.ide][2]
                    McountryConsumer[self.country][consumerIde].totProfit=\
                            McountryConsumer[self.country][consumerIde].totProfit+self.profitRate*oldShare 
                    paymentConsumer=DismissShareCapital+DividendShare
                    McountryConsumer[self.country][consumerIde].receiving(paymentConsumer,McountryBank,McountryCentralBank)                                      
                    del McountryConsumer[self.country][consumerIde].DLA[self.ide]
              else:
                  oldShare=McountryConsumer[self.country][consumerIde].DLA[self.ide][2] 
                  ConsumerAshare=self.A*McountryConsumer[self.country][consumerIde].DLA[self.ide][4]
                  if self.CapitalDismiss>0.00001:
                     print 'stop', stop   
                  DismissShareCapital=self.CapitalDismiss*ConsumerAshare/float(self.A)     
                  DividendShare=self.dividends*ConsumerAshare/float(self.A)
                  ratioA=ConsumerAshare/float(self.A)
                  McountryConsumer[self.country][consumerIde].DLA[self.ide][2]=ConsumerAshare
                  McountryConsumer[self.country][consumerIde].DLA[self.ide][4]=ratioA
                  McountryConsumer[self.country][consumerIde].totProfit=McountryConsumer[self.country][consumerIde].totProfit+self.profitRate*oldShare
                  self.Downer[consumerIde][2]=McountryConsumer[self.country][consumerIde].DLA[self.ide][2]
                  self.Downer[consumerIde][4]=McountryConsumer[self.country][consumerIde].DLA[self.ide][4]
                  McountryConsumer[self.country][consumerIde].capitalDismiss=\
                  McountryConsumer[self.country][consumerIde].capitalDismiss+DismissShareCapital
                  McountryConsumer[self.country][consumerIde].DividendShare=\
                    McountryConsumer[self.country][consumerIde].DividendShare+DividendShare           
                  totalPayement=totalPayement+DismissShareCapital+DividendShare
                  paymentConsumer=DismissShareCapital+DividendShare
                  McountryConsumer[self.country][consumerIde].receiving(paymentConsumer,McountryBank,McountryCentralBank)     
          self.paying(totalPayement,McountryBank,McountryCentralBank) 
          self.CapitalDismiss=0  
          
      def effectiveSelling(self,DglobalPhiNotTradable,avPhiGlobalTradable,avPriceGlobalTradable,McountryAvPriceNotTradable,\
                           DglobalPhi,McountryAvPrice): 
          workersProductionAvailable=self.l#*(1-self.gamma)
          workerInnovationAvailable=0
          #self.workForceNumberProduction=0
          #innovationExpenditure=0#self.gamma*self.l#0 
          if self.l>self.workForceNumberProduction+0.01:
             print 'self.l', self.l
             print 'self.workForceNumberProduction',self.workForceNumberProduction 
             #innovationExpenditure=self.l-self.workForceNumberProduction 
             print 'stop', stop   
          if workersProductionAvailable<=0:
             self.productionEffective=0
          if workersProductionAvailable>0:
             self.productionEffective=min(workersProductionAvailable,self.workForceNumberDesiredOptimal)*self.phi
             #self.productionEffective=workersProductionAvailable*self.phi   
          self.xOfferedEffective=self.productionEffective+self.inventory
          self.pastPhi=self.phi           
          self.phi=self.lebalance.innovatingEffective4(self.innovationExpenditure,self.phi,self.l,\
                                                      DglobalPhiNotTradable,avPhiGlobalTradable,self.tradable,\
                                                  avPriceGlobalTradable,McountryAvPriceNotTradable,self.w,\
                                                  DglobalPhi,McountryAvPrice) 
          self.gPhi=(self.phi-self.pastPhi)/float(self.pastPhi)
          #self.gPhi=(self.price*self.phi-self.pastPhi*self.pastPrice)/float(self.pastPhi*self.pastPrice)
          #self.gPhi=self.price*self.phi

      def wageOffered1(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL,t,McountryConsumer):
          self.pastWage=self.w  
          unemploymentVariation=0  
          if McountryPastUnemployement[self.country]>0:
             unemploymentVariation=(McountryUnemployement[self.country]\
                               -McountryPastUnemployement[self.country])#/McountryPastUnemployement[self.country]
          productivityVariation=self.gPhi
          #if McountryPastYL[self.country]>0: 
          #   productivityVariation=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country]
          ratioUnemployment=0
          if self.nWorkerDesiredEffective>0:
             ratioUnemployment=(self.nWorkerDesiredEffective-self.l)/self.nWorkerDesiredEffective
          #if self.nWorkerDesiredEffective>self.l:
          #      d=self.delta
          #if self.nWorkerDesiredEffective<=self.l:
          #      d=-self.delta 
          u=McountryUnemployement[self.country]
          #self.w=self.w*(1+d-0.0*unemploymentVariation+productivityVariation)
          self.w=self.w*(1+0.03*ratioUnemployment+productivityVariation-0.1*(u-0.04))
          #if self.w<self.pastWage:
          #   a=random.uniform(0,1)   
          #   u=McountryUnemployement[self.country]
          #   if a<=self.upsilon2*math.exp(-u*self.upsilon):
          #      self.w=self.pastWage 
          if self.w<1:
             self.w=1
          if self.w>self.pastWage*(1+0.03):
             self.w=self.pastWage*(1+0.03)
          if self.w<self.pastWage*(1-0.03):
             self.w=self.pastWage*(1-0.03)   
          if self.ide=='F0n0':
             print
             print 'self.ide', self.ide
             print 'self.w', self.w
             print 'self.pastWage', self.pastWage 
             print 'ratioUnemployment', ratioUnemployment
             print 'unemploymentVariation', unemploymentVariation
             print 'productivityVariation', productivityVariation
              

      def wageOffered(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL,t,McountryConsumer):
          # Eq. 15 (Caiani et al. 2016): firm offered wage baseline rule.
          nWorkerDesired=self.nWorkerDesiredEffective
          l=self.l 
          p=self.price
          u=McountryUnemployement[self.country]
          a=random.uniform(0,1)   
          self.pastWage=self.w 
          direction='stay' 
          firmUpsilon=1.0#1/2.5#0.25  
          if nWorkerDesired>self.l:
                #direction='plus'
                if a>firmUpsilon*math.exp(-u*self.upsilon):
                #if a<=u*self.upsilon*firmUpsilon: 
                   direction='stay'
                if a<=firmUpsilon*math.exp(-u*self.upsilon):
                #if a>u*self.upsilon*firmUpsilon:
                   direction='plus' 
          if nWorkerDesired<=self.l:
             #direction='stay'    
             if  a>firmUpsilon*math.exp(-u*self.upsilon):
             #if  a<=u*self.upsilon*firmUpsilon:
                 direction='minus' 
             if a<=firmUpsilon*math.exp(-u*self.upsilon):
             #if  a>u*self.upsilon*firmUpsilon: 
                direction='stay'
          if direction=='plus':
             self.w=random.uniform(self.w,self.w*(1+self.deltaLabor)) 
          if direction=='minus':
             self.w=random.uniform(self.w,self.w*(1-self.deltaLabor))          
          if self.w<self.wageMin:
             self.w=self.wageMin 
          if self.w>self.wageMax:
             self.w=self.wageMax 
         

      def wageOffered3(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL,t,McountryConsumer):
          LwageEmployed=[] 
          LwageEmployedDemand=[]
          g=min(self.delta,(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country]) 
          self.pastWage=self.w
          for employed in self.Lemployed:
              #print 'self.Lemployed', self.Lemployed 
              if employed[2]>0.01: 
                 ideConsumer=employed[0]
                 wageDemanded=McountryConsumer[self.country][ideConsumer].wageDemanded 
                 LwageEmployed.append(employed[3])#(employed[3])
                 LwageEmployedDemand.append(wageDemanded)#(employed[4])
          if len(LwageEmployed)>0:
             wageEmployed=LwageEmployed[0]
          #   averageWageEmployed=sum(LwageEmployed)/float(len(LwageEmployed))  
          if len(LwageEmployed)==0:
             wageEmployed=0
          #   averageWageEmployed=0
          #if wageEmployed>averageWageEmployed+0.01 or wageEmployed+0.01<averageWageEmployed:
          #   print 'stop', stop
          nWorkerDesired=self.nWorkerDesiredEffective
          nWorkerDesiredOptimal=self.nWorkerDesiredOptimalEffective
          l=self.l 
          p=self.price
          u=McountryUnemployement[self.country]
          a=random.uniform(0,1)   
          self.pastWage=self.w 
          #self.upsilon=1.0
          if nWorkerDesired>self.l: 
             direction='plus'
             #    if a>math.exp(-1*(u*self.upsilon-self.gPhi*self.upsilon2)-1*0.0): #and self.gPhi<=0:
             #       direction='stay' 
             #    if a<=math.exp(-1*(u*self.upsilon-self.gPhi*self.upsilon2)-1*0.0):# or self.gPhi>0:
             #       direction='plus'
             #if self.l<=nWorkerDesiredOptimal:
             #   direction='plus' 
             #   if a>math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0): #and self.gPhi<=0:
             #       direction='stay' 
             #   if a<=math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0):# or self.gPhi>0:
             #       direction='plus'
             #if self.l>nWorkerDesiredOptimal:
             #    if a>math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0): #and self.gPhi<=0:
             #       direction='minus' 
             #    if a<=math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0):# or self.gPhi>0:
             #       direction='stay'
          if nWorkerDesired<=self.l:# and self.gPhi<=g:
             #if self.gPhi>0:# and self.gPhi>0: 
             #   direction='plus' 
             #if self.gPhi<=0:# or self.gPhi<=0:
             #if nWorkerDesired<=nWorkerDesiredOptimal:
             #   direction='stay' 
             #   if a>math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0): #and self.gPhi<=0:
             #       direction='stay' 
             #   if a<=math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0):# or self.gPhi>0:
             #       direction='plus'
             #if nWorkerDesired>nWorkerDesiredOptimal:
                 if a>math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0): #and self.gPhi<=0:
                    direction='minus' 
                 if a<=math.exp(-1*(u*self.upsilon-0.0*self.gPhi*self.upsilon2)-1*0.0):# or self.gPhi>0:
                    direction='stay'
             #if self.gPhi<=0:
             #   direction='minus' 
                 #if self.gPhi>0:
                  #  direction='plus' 
          if direction=='plus':
             #self.w=random.uniform(self.w,self.w*(1+self.deltaLabor)) 
             self.wageExpected=random.uniform(self.wageExpected,self.wageExpected*(1+self.deltaLabor)) 
          if direction=='minus':
             #self.w=random.uniform(self.w,self.w*(1-self.deltaLabor))    
             self.wageExpected=random.uniform(self.wageExpected,self.wageExpected*(1-self.deltaLabor))  
          #self.wBargaining=           
          self.bargaining='no'      
          self.dis='nn' 
          self.wageBeforeBargaining=self.wageExpected 
          if len(LwageEmployedDemand)>0:
             LwageEmployedDemand.sort()  
             maxWageDemanded=max(LwageEmployedDemand)#/float(len(LwageEmployedDemand))
             lenEmployed=len(LwageEmployedDemand)
             self.alpha=0.8
             alphaWage=LwageEmployedDemand[int(lenEmployed*self.alpha)]
             self.probDis=0 
             if self.wageExpected<maxWageDemanded:
                #self.alpha=0.9
                #self.w=alphaWage
                self.wBargaining=maxWageDemanded#random.uniform(self.wageExpected,self.wageExpected*(1+self.deltaLabor))
                #self.wBargaining=random.uniform(self.wageExpected,maxWageDemanded)
                #self.w=min(max(self.wageExpected,self.pastWage*(1+self.gPhi)),maxWageDemanded)
                #self.w=min(self.alpha*self.phi*self.price,maxWageDemanded)  
                self.w=self.wageExpected
                b=random.uniform(0,1)
                #dis1=(maxWageDemanded-self.wBargaining)/float(self.wBargaining) 
                #dis2=(self.wBargaining-maxWageDemanded)/float(maxWageDemanded)  
                dis1=(maxWageDemanded-self.wageExpected)/float(self.wageExpected)
                #self.probDis=math.exp(-1*dis1*self.upsilon2)
                if b<math.exp(-1*dis1*self.upsilon2):
                   self.w=self.wBargaining
                   self.bargaining='yes'  
                self.dis=dis1
             if self.wageExpected>=maxWageDemanded:
                self.w=self.wageExpected
                #self.wBargaining=self.w
             #if self.w<self.pastWage*(1+self.gPhi):
             #   self.w=self.pastWage*(1+self.gPhi) 
          if len(LwageEmployedDemand)==0:
              self.w=self.wageExpected 
          if self.whichPolicy=='LF':
             if self.w<self.pastWage*(1+self.gPhi) and len(LwageEmployedDemand)>0 and self.gPhi>0:
                self.w=self.pastWage*(1+self.gPhi)
          #if self.w<wageEmployed:
          #   self.w=wageEmployed
          if self.w<1.0:#self.wageMin:
             self.w=1.0#self.wageMin 
          if self.w>self.wageMax:
             self.w=self.wageMax 
          self.wageExpected=self.w
          self.direction=direction



      def wageOffered4(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL,t,McountryConsumer):
          LwageEmployed=[] 
          LwageEmployedDemand=[]
          g=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country] 
          self.pastWage=self.w
          for employed in self.Lemployed:
              #print 'self.Lemployed', self.Lemployed 
              if employed[2]>0.01: 
                 ideConsumer=employed[0]
                 wageDemanded=McountryConsumer[self.country][ideConsumer].wageDemanded 
                 LwageEmployed.append(employed[3])#(employed[3])
                 LwageEmployedDemand.append(wageDemanded)#(employed[4])
          if len(LwageEmployed)>0:
             wageEmployed=LwageEmployed[0]
          #   averageWageEmployed=sum(LwageEmployed)/float(len(LwageEmployed))  
          if len(LwageEmployed)==0:
             wageEmployed=0
          #   averageWageEmployed=0
          #if wageEmployed>averageWageEmployed+0.01 or wageEmployed+0.01<averageWageEmployed:
          #   print 'stop', stop
          nWorkerDesired=self.nWorkerDesiredEffective
          l=self.l 
          p=self.price
          u=McountryUnemployement[self.country]
          a=random.uniform(0,1)   
          self.pastWage=self.w 
          del self.LpastEmployment[0]
          #if nWorkerDesired>self.l:# and g<=0:
          #   self.LpastEmployment.append(0)
          #if nWorkerDesired<=self.l:# and g<=0:
          #   self.LpastEmployment.append(1)
          if nWorkerDesired>0: 
             self.LpastEmployment.append(self.l/float(nWorkerDesired))  
          if nWorkerDesired==0:
             self.LpastEmployment.append(0)
          sumLpastEmployment=sum(self.LpastEmployment)
          #memory=4 
          if sumLpastEmployment==0:#self.memory:# and g<=0:
             direction='plus'#'stay
          if sumLpastEmployment<self.memory and sumLpastEmployment>0:# and g<=0:
             direction='plus'#'stay'  
             #if a>self.upsilon2*math.exp(-u*self.upsilon): #and self.gPhi<=0:
             #       direction='stay' 
             #if a<=self.upsilon2*math.exp(-u*self.upsilon):# or self.gPhi>0:
             #       direction='plus' 
          #if sumLpastEmployment>=0.8*self.memory and sumLpastEmployment>0:# and g<=0:
          #   direction='stay'#
          if sumLpastEmployment>=self.memory and sumLpastEmployment>0:# and g<=0:
             #direction='minus'#'stay'
             if a>self.upsilon2*math.exp(-u*self.upsilon): #and self.gPhi<=0:
                    direction='minus' 
             if a<=self.upsilon2*math.exp(-u*self.upsilon):# or self.gPhi>0:
                    direction='stay'  
          if direction=='plus':
             #self.w=random.uniform(self.w,self.w*(1+self.deltaLabor)) 
             self.wageExpected=random.uniform(self.wageExpected,self.wageExpected*(1+self.deltaLabor)) 
          if direction=='minus':
             #self.w=random.uniform(self.w,self.w*(1-self.deltaLabor))    
             self.wageExpected=random.uniform(self.wageExpected,self.wageExpected*(1-self.deltaLabor))                 
          if len(LwageEmployedDemand)>0:
             LwageEmployedDemand.sort()  
             maxWageDemanded=max(LwageEmployedDemand)#/len(LwageEmployedDemand)
             lenEmployed=len(LwageEmployedDemand)
             self.alpha=0.8
             alphaWage=LwageEmployedDemand[int(lenEmployed*self.alpha)]
             if self.wageExpected<maxWageDemanded:
                #self.alpha=0.9
                #self.w=alphaWage
                #self.w=random.uniform(self.wageExpected,maxWageDemanded)
                #self.w=min(max(self.wageExpected,self.pastWage*(1+self.gPhi)),maxWageDemanded)
                #self.w=min(self.alpha*self.phi*self.price,maxWageDemanded)  
                self.w=self.wageExpected
             if self.wageExpected>=maxWageDemanded:
                self.w=self.wageExpected
          if len(LwageEmployedDemand)==0:
              self.w=self.wageExpected 
          if self.whichPolicy=='LF':
             if self.w<self.pastWage*(1+self.gPhi) and len(LwageEmployedDemand)>0 and self.gPhi>0:
                self.w=self.pastWage*(1+self.gPhi)
          #if self.w<wageEmployed:
          #   self.w=wageEmployed
          if self.w<1.0:#self.wageMin:
             self.w=1.0#self.wageMin 
          if self.w>self.wageMax:
             self.w=self.wageMax 
          self.wageExpected=self.w
          if self.ide=='F0n0':
             print
             print 'self.ide', self.ide
             print 'self.w', self.w
             print 'self.LpastEmployment', self.LpastEmployment
             print 'direction', direction
             print 'self.wageExpected', self.wageExpected
             print 'self.w', self.w
             print 'self.pastWage', self.pastWage 
 
      def wageOffered5(self,McountryUnemployement,McountryPastUnemployement,McountryYL,McountryPastYL,t,McountryConsumer):
          LwageEmployed=[] 
          LwageEmployedDemand=[]
          g=(McountryYL[self.country]-McountryPastYL[self.country])/McountryPastYL[self.country] 
          self.pastWage=self.w
          for employed in self.Lemployed:
              #print 'self.Lemployed', self.Lemployed 
              if employed[2]>0.01: 
                 ideConsumer=employed[0]
                 wageDemanded=McountryConsumer[self.country][ideConsumer].wageDemanded 
                 LwageEmployed.append(employed[3])#(employed[3])
                 LwageEmployedDemand.append(wageDemanded)#(employed[4])
          if len(LwageEmployed)>0:
             wageEmployed=LwageEmployed[0]
          #   averageWageEmployed=sum(LwageEmployed)/float(len(LwageEmployed))  
          if len(LwageEmployed)==0:
             wageEmployed=0
          #   averageWageEmployed=0
          #if wageEmployed>averageWageEmployed+0.01 or wageEmployed+0.01<averageWageEmployed:
          #   print 'stop', stop
          nWorkerDesired=self.nWorkerDesiredEffective
          l=self.l 
          p=self.price
          u=McountryUnemployement[self.country]
          a=random.uniform(0,1)   
          b=random.uniform(0,1)
          self.pastWage=self.w 
          #del self.LpastEmployment[0]
          if nWorkerDesired>0:
             self.memPastEmployment=0.8*self.memPastEmployment+0.2*self.l/float(nWorkerDesired)  
          #if nWorkerDesired>self.l:# and g<=0:
          #   self.memPastEmployment=0.8*self.memPastEmployment+0.2*1
          #if nWorkerDesired<=self.l:# and g<=0:
          #   self.memPastEmployment=0.8*self.memPastEmployment+0.2*0
          #sumLpastEmployment=sum(self.LpastEmployment)
          #memory=4 
          #if sumLpastEmployment==0:#self.memory:# and g<=0:
          #   direction='plus'#'stay
          if self.memPastEmployment<0.7:
             direction='plus'
          #if b>self.memPastEmployment and self.memPastEmployment>=0.8:# and sumLpastEmployment>0:# and g<=0:
          #   direction='stay'#'plus'#'stay'  
          #if b<=self.memPastEmployment and self.memPastEmployment>=0.8:# and g<=0:
          if self.memPastEmployment>=0.7:
             #direction='minus'#'stay'
             if a>self.upsilon2*math.exp(-u*self.upsilon): #and self.gPhi<=0:
                    direction='minus' 
             if a<=self.upsilon2*math.exp(-u*self.upsilon):# or self.gPhi>0:
                    direction='stay'  
          if direction=='plus':
             #self.w=random.uniform(self.w,self.w*(1+self.deltaLabor)) 
             self.wageExpected=random.uniform(self.wageExpected,self.wageExpected*(1+self.deltaLabor)) 
          if direction=='minus':
             #self.w=random.uniform(self.w,self.w*(1-self.deltaLabor))    
             self.wageExpected=random.uniform(self.wageExpected,self.wageExpected*(1-self.deltaLabor))                 
          if len(LwageEmployedDemand)>0:
             LwageEmployedDemand.sort()  
             maxWageDemanded=max(LwageEmployedDemand)#/len(LwageEmployedDemand)
             lenEmployed=len(LwageEmployedDemand)
             self.alpha=0.8
             alphaWage=LwageEmployedDemand[int(lenEmployed*self.alpha)]
             if self.wageExpected<maxWageDemanded:
                #self.alpha=0.9
                #self.w=alphaWage
                #self.w=random.uniform(self.wageExpected,maxWageDemanded)
                #self.w=min(max(self.wageExpected,self.pastWage*(1+self.gPhi)),maxWageDemanded)
                #self.w=min(self.alpha*self.phi*self.price,maxWageDemanded)  
                self.w=self.wageExpected
             if self.wageExpected>=maxWageDemanded:
                self.w=self.wageExpected
          if len(LwageEmployedDemand)==0:
              self.w=self.wageExpected 
          if self.whichPolicy=='LF':
             if self.w<self.pastWage*(1+self.gPhi) and len(LwageEmployedDemand)>0 and self.gPhi>0:
                self.w=self.pastWage*(1+self.gPhi)
          #if self.w<wageEmployed:
          #   self.w=wageEmployed
          if self.w<1.0:#self.wageMin:
             self.w=1.0#self.wageMin 
          if self.w>self.wageMax:
             self.w=self.wageMax 
          self.wageExpected=self.w
          if self.ide=='F0n0':
             print
             print 'self.ide', self.ide
             print 'self.w', self.w
             #print 'self.LpastEmployment', self.LpastEmployment
             print 'direction', direction
             print 'self.wageExpected', self.wageExpected
             print 'self.w', self.w
             print 'self.pastWage', self.pastWage
             print 'self.memPastEmployment', self.memPastEmployment
             print 'b', b   
          
                    
      def initialCycleVariable(self):
          self.PreviousA=self.A
          self.l=0
          self.CapitalDismiss=0
          self.laborExpenditure=0
          
      def write(self,t,run):
          nameWrite=self.folder+'/'+self.name+'r'+str(run)+'Firm.csv'
          f=open(nameWrite,'a')  
          x_prod=self.productionEffective
          x_programmed=self.mind.xProducing
          x_sold=self.xSold          
          p=self.price
          revenue=x_sold*p  
          F=[self.run, self.ide,t,self.country, self.phi,self.profit,p,self.w,self.l,x_prod,\
             self.mind.xE,x_sold,self.inventory, self.workForceNumberDesired,self.A,revenue]             
          writer = csv.writer(f)
          writer.writerow(F)
          f.close() 
             
      def orderCreditor(self):
          self.Lcreditor=[]
          for bank in self.Mloan:
              #print 'stop', stop
              self.Lcreditor.append(self.Mloan[bank][1])
          random.shuffle(self.Lcreditor) 
          #self.Mloan=[] 

      def orderBankDeposit(self,McountryBank):
          self.LbankDeposit=[]
          LdelBank=[]
          for bank in self.Mdeposit:
              countryBank=self.Mdeposit[bank][4]
              if (bank in  McountryBank[countryBank])==True or bank==self.country:
                 self.LbankDeposit.append(bank)
              else:
                if self.Mdeposit[bank][2]>0.000001:
                   print 'stop', stop
                LdelBank.append(bank) 
          for bank in LdelBank:
              del self.Mdeposit[bank]

      def paying(self,payment,McountryBank,McountryCentralBank):
          random.shuffle(self.LbankDeposit)
          for bank in self.LbankDeposit:
              volumeDeposit=self.Mdeposit[bank][2]
              countryBank=self.Mdeposit[bank][4]
              if payment<=volumeDeposit:
                 reduction=payment
                 self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction
                 if bank!=self.country: 
                    volumeCheck=McountryBank[countryBank][bank].Mdeposit[self.ide][2]
                 if bank==self.country: 
                    volumeCheck=McountryCentralBank[countryBank].Mdeposit[self.ide][2] 
                 if volumeDeposit<volumeCheck-0.00001 or volumeDeposit>volumeCheck+0.00001:
                    print 'stop', stop
                 if bank!=self.country:
                    McountryBank[countryBank][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank) 
                 if bank==self.country:
                    McountryCentralBank[self.country].depositWithdrawal(reduction,self.ide) 
                    if len(self.LbankDeposit)>1:
                       print 'stop', stop
                 payment=payment-reduction 
                 if countryBank!=self.country:
                    McountryCentralBank[self.country].moneyInflow=McountryCentralBank[self.country].moneyInflow+reduction 
                    McountryCentralBank[countryBank].moneyOutflow=McountryCentralBank[countryBank].moneyOutflow+reduction 
                 break    
              else:
                 reduction=volumeDeposit
                 self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction
                 if bank!=self.country:
                    volumeCheck=McountryBank[countryBank][bank].Mdeposit[self.ide][2]
                 if bank==self.country:
                    volumeCheck=McountryCentralBank[countryBank].Mdeposit[self.ide][2] 
                 if volumeDeposit<volumeCheck-0.00001 or volumeDeposit>volumeCheck+0.00001:
                    print 'stop', stop
                 if bank!=self.country:
                    McountryBank[countryBank][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank)
                 if bank==self.country:     
                    McountryCentralBank[self.country].depositWithdrawal(reduction,self.ide)
                 payment=payment-reduction
                 if countryBank!=self.country:
                    McountryCentralBank[self.country].moneyInflow=McountryCentralBank[self.country].moneyInflow+reduction 
                    McountryCentralBank[countryBank].moneyOutflow=McountryCentralBank[countryBank].moneyOutflow+reduction
          if payment>0.001:
             print 'stop', stop

      def receivingInterestDeposit(self,McountryBank,McountryCentralBank):
          for bank in self.Mdeposit: 
              if bank!=self.country: 
                 volume=self.Mdeposit[bank][2]   
                 interest=self.Mdeposit[bank][3]
                 countryBank=self.Mdeposit[bank][4] 
                 service=volume*interest 
                 self.Mdeposit[bank][2]=self.Mdeposit[bank][2]+service
                 McountryBank[countryBank][bank].Mdeposit[self.ide][2]=\
                 McountryBank[countryBank][bank].Mdeposit[self.ide][2]+service
                 McountryBank[countryBank][bank].Deposit=McountryBank[countryBank][bank].Deposit+service
                 McountryBank[countryBank][bank].serviceFirm=McountryBank[countryBank][bank].serviceFirm+service
                 if countryBank!=self.country:
                    McountryCentralBank[self.country].moneyInflow=McountryCentralBank[self.country].moneyInflow+service
                    McountryCentralBank[countryBank].moneyOutflow=McountryCentralBank[countryBank].moneyOutflow+service  
                 
      def receiving(self,payment,McountryBank,McountryCentralBank):
          random.shuffle(self.LbankDeposit)
          ideBank=self.LbankDeposit[0]
          volumeDeposit=self.Mdeposit[ideBank][2] 
          countryBank=self.Mdeposit[ideBank][4] 
          if ideBank!=self.country:
             volumeCheck=McountryBank[countryBank][ideBank].Mdeposit[self.ide][2]
          if ideBank==self.country:
             volumeCheck=McountryCentralBank[self.country].Mdeposit[self.ide][2] 
          if volumeDeposit<volumeCheck-0.00001 or volumeDeposit>volumeCheck+0.00001:   
             print 'stop', stop
          if ideBank!=self.country: 
             self.Mdeposit[ideBank][2]=self.Mdeposit[ideBank][2]+payment
             McountryBank[countryBank][ideBank].depositInjection(payment,self.ide,McountryCentralBank)
             if countryBank!=self.country:
                McountryCentralBank[countryBank].moneyInflow=McountryCentralBank[countryBank].moneyInflow+payment
                McountryCentralBank[self.country].moneyOutflow=McountryCentralBank[self.country].moneyOutflow+payment
          if ideBank==self.country:
             if len(self.LbankDeposit)>1:
                print 'stop', stop
             self.Mdeposit[ideBank][2]=self.Mdeposit[ideBank][2]+payment
             McountryCentralBank[self.country].depositInjection(payment,self.ide) 
        
      def receavingLoan(self,ideBank,loan,interestRate,interestRateDeposit,countryBank,McountryBank,McountryCentralBank):
          if self.country==countryBank:
             self.receavingLoanDomestic(ideBank,loan,interestRate,interestRateDeposit,countryBank)
          if self.country!=countryBank:
             self.receavingLoanForeigner(ideBank,loan,interestRate,interestRateDeposit,countryBank,McountryBank,McountryCentralBank) 

      def receavingLoanDomestic(self,ideBank,loan,interestRate,interestRateDeposit,countryBank):
          self.Mloan[ideBank]=[self.ide,ideBank,loan,interestRate,countryBank]
          if (ideBank in self.Mdeposit)==True:
             self.Mdeposit[ideBank][2]=self.Mdeposit[ideBank][2]+loan
          elif (ideBank in self.Mdeposit)==False:
             self.Mdeposit[ideBank]=[self.ide,ideBank,loan,interestRateDeposit,countryBank] 
          self.loanReceived=self.loanReceived+loan
          self.interestRate=interestRate   
          self.Lcreditor.append(ideBank) 
          self.LbankDeposit.append(ideBank)

      def receavingLoanForeigner(self,ideBank,loan,interestRate,interestRateDeposit,countryBank,McountryBank,McountryCentralBank):
          self.Mloan[ideBank]=[self.ide,ideBank,loan,interestRate,countryBank]
          self.loanReceived=self.loanReceived+loan
          self.interestRate=interestRate   
          self.Lcreditor.append(ideBank) 
          self.receiving(loan,McountryBank,McountryCentralBank)

      def repayingLoan(self,bankIde,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank):
          if countryBank==self.country:
             self.repayingLoanDomestic(bankIde,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank)
          if countryBank!=self.country:
             self.repayingLoanForeigner(bankIde,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank)
          
                              
      def repayingLoanDomestic(self,bankIde,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank): 
          countryBank=self.Mdeposit[bankIde][4]               
          McountryBank[countryBank][bankIde].Loan=McountryBank[countryBank][bankIde].Loan-loanValue  
          volumeDeposit=self.Mdeposit[bankIde][2] 
          if loanVolume<=volumeDeposit:
             reduction=loanVolume
             self.Mdeposit[bankIde][2]=self.Mdeposit[bankIde][2]-reduction             
             McountryBank[countryBank][bankIde].Mdeposit[self.ide][2]=McountryBank[countryBank][bankIde].Mdeposit[self.ide][2]-reduction
             McountryBank[countryBank][bankIde].Deposit=McountryBank[countryBank][bankIde].Deposit-reduction
             if countryBank!=self.country:
                McountryCentralBank[countryBank].moneyInflow=McountryCentralBank[countryBank].moneyInflow+reduction 
                McountryCentralBank[self.country].moneyOutflow=McountryCentralBank[self.country].moneyOutflow+reduction
          if loanVolume>volumeDeposit:
             reduction=volumeDeposit
             self.Mdeposit[bankIde][2]=self.Mdeposit[bankIde][2]-reduction
             McountryBank[countryBank][bankIde].Mdeposit[self.ide][2]=McountryBank[countryBank][bankIde].Mdeposit[self.ide][2]-reduction
             McountryBank[countryBank][bankIde].Deposit=McountryBank[countryBank][bankIde].Deposit-reduction            
             loanVolume=loanVolume-reduction 
             random.shuffle(self.LbankDeposit)
             for bank in self.LbankDeposit:
                 volumeDeposit=self.Mdeposit[bank][2]
                 countryBankNew=self.Mdeposit[bank][4]
                 if loanVolume<=volumeDeposit:
                    reduction=loanVolume
                    self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction  
                    McountryBank[countryBankNew][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank) 
                    McountryBank[countryBank][bankIde].Reserves=McountryBank[countryBank][bankIde].Reserves+reduction
                    McountryCentralBank[countryBank].Reserves=McountryCentralBank[countryBank].Reserves+reduction    
                    if countryBankNew!=self.country:
                       McountryCentralBank[self.country].moneyInflow=McountryCentralBank[self.country].moneyInflow+reduction 
                       McountryCentralBank[countryBank].moneyOutflow=McountryCentralBank[countryBank].moneyOutflow+reduction
                    break    
                 else:
                    reduction=volumeDeposit
                    self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction
                    McountryBank[countryBankNew][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank)
                    McountryBank[countryBank][bankIde].Reserves=McountryBank[countryBank][bankIde].Reserves+reduction 
                    McountryCentralBank[countryBank].Reserves=McountryCentralBank[countryBank].Reserves+reduction 
                    loanVolume=loanVolume-reduction  
                    if countryBankNew!=self.country:
                       McountryCentralBank[self.country].moneyInflow=McountryCentralBank[self.country].moneyInflow+reduction 
                       McountryCentralBank[countryBank].moneyOutflow=McountryCentralBank[countryBank].moneyOutflow+reduction  

      def repayingLoanForeigner(self,bankIde,loanValue,loanVolume,McountryBank,McountryCentralBank,countryBank):              
          McountryBank[countryBank][bankIde].Loan=McountryBank[countryBank][bankIde].Loan-loanValue   
          random.shuffle(self.LbankDeposit)
          for bank in self.LbankDeposit:
              volumeDeposit=self.Mdeposit[bank][2]
              countryBankNew=self.Mdeposit[bank][4]
              if loanVolume<=volumeDeposit:
                 reduction=loanVolume
                 self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction
                 if   bank==self.country:
                      McountryCentralBank[self.country].depositWithdrawal(reduction,self.ide) 
                 if   bank!=self.country:
                      McountryBank[countryBankNew][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank) 
                 McountryBank[countryBank][bankIde].Reserves=McountryBank[countryBank][bankIde].Reserves+reduction
                 McountryCentralBank[countryBank].Reserves=McountryCentralBank[countryBank].Reserves+reduction    
                 McountryCentralBank[countryBank].moneyInflow=McountryCentralBank[countryBank].moneyInflow+reduction 
                 McountryCentralBank[self.country].moneyOutflow=McountryCentralBank[self.country].moneyOutflow+reduction
                 break    
              else:
                    reduction=volumeDeposit
                    self.Mdeposit[bank][2]=self.Mdeposit[bank][2]-reduction
                    if   bank==self.country:
                      McountryCentralBank[self.country].depositWithdrawal(reduction,self.ide) 
                    if   bank!=self.country:
                      McountryBank[countryBankNew][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank)
                    #McountryBank[countryBankNew][bank].depositWithdrawal(reduction,self.ide,McountryCentralBank)
                    McountryBank[countryBank][bankIde].Reserves=McountryBank[countryBank][bankIde].Reserves+reduction 
                    McountryCentralBank[countryBank].Reserves=McountryCentralBank[countryBank].Reserves+reduction 
                    loanVolume=loanVolume-reduction  
                    McountryCentralBank[countryBank].moneyInflow=McountryCentralBank[countryBank].moneyInflow+reduction 
                    McountryCentralBank[self.country].moneyOutflow=McountryCentralBank[self.country].moneyOutflow+reduction      

      def computeDeposit(self):
          self.Deposit=0 
          for bank in self.Mdeposit:
              self.Deposit=self.Deposit+self.Mdeposit[bank][2]  
                   
      def checkNetWorth(self):
          Liabilities=self.A
          Deposit=0 
          for bank in self.Mdeposit:
              Deposit=Deposit+self.Mdeposit[bank][2]  
          Assets=Deposit
          if (Liabilities-Assets)/float(Liabilities+Assets)>0.0001 or (Liabilities-Assets)/float(Liabilities+Assets)<-0.0001:      
             print 'stop', stop  

      def checkOwnerhip(self,McountryConsumer):
          totConsumerA=0
          totFirmA=0  
          for consumerIde in self.Downer:
              totConsumerA=totConsumerA+McountryConsumer[self.country][consumerIde].DLA[self.ide][2]
              totFirmA=totFirmA+self.Downer[consumerIde][2] 
         
          
           
  
               
