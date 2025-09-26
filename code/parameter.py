import csv
import os
import math

#mu5.8

class Parameter:
      def __init__(self):                         
          self.name='muxSnCo5upsilon20.7polModPolVar0.512'#1.625'#2.876'#2.231#1.625'#1.053#0.512'
          self.folder='/home/ermanno/Desktop/mu/mu7.1/data/data'+self.name
          #self.folder='/home/ermanno/mu/mu7.1/data/data'+self.name
          #Monte Carlo runs
          firstrun=0#
          lastrun=49#
          self.Lrun=range(firstrun,lastrun+1)
          self.weSeedRun='yes'      
          # LLM bridge configuration (defaults keep legacy heuristics)
          self.use_llm_firm_pricing = False
          self.use_llm_bank_credit = False
          self.use_llm_wage = False
          self.llm_server_url = 'http://127.0.0.1:8000'
          self.llm_timeout_ms = 200
          self.llm_batch = False
          # space and time
          self.ncycle=1001
          self.ncountry=5 #(K)
          self.nconsumer=500#1000 #(H)
          self.propTradable=0.4#0.4#(c_T)           
          # firms
          self.A=10#(A^0)
          self.upsilon=1.625#1.0# (upsilon)
          self.upsilon2=0.7#(upsilon2)  
          self.phi=1.0 # (phi_0)
          self.delta=0.04#0.03 (delta) 
          self.dividendRate=0.95#0.95# (rho)   
          self.gamma=0.03#(gamma)
          self.ni=0.8#1.0#(ni) 
          self.deltaInnovation=0.04# (delta) 
          self.Fcost=1.0# (F)
          self.minMarkUp=0.0#0.0# (minimum mark-up)
          self.theta=0.2
          self.jobDuration=0#self.ncycle#40
          #consumers         
          self.bound=10# # (psi)  n. matching       
          self.cDisposableIncome=0.9# (c_y)
          self.cWealth=0.1# (c_D)
          self.liqPref=0.1# (lambda) 
          self.beta=2.0#2.0#0.25#2.0#(beta)
          self.ls=1.0 #(l^S) 
          self.wBar=0.1 #(w bar)
          self.w0=1.0 #(w_0)          
          #bank
          self.probBank=0.1#0.1(eta)
          self.sigma=4.0 
          self.minReserve=0.1  #(mu_2)        
          self.xi=0.003#0.003# (chi)     
          self.rDeposit=0.001# (r_re)  
          self.mu1=20.0#12.0#(mu_1)
          self.iota=0.5#0.5#1.0#(iota_l)
          self.iotaE=0.1#(iota_b) 
          #etat
          self.taxRatio=0.4 #(tau_0)
          self.G=0.4*self.nconsumer  #(G)              
          self.xiBonds=self.xi#(chi_B)   
          self.maxPublicDeficit=0.03#(d^max)  
          self.taxRatioMin=0.35#0.35 #(tau_{min})
          self.taxRatioMax=0.45#0.45 #(tau_{max})
          self.gMin=0.4 #(g_min)
          self.gMax=0.6#float('inf')# #(g_max)       
          #central bank initial discount value
          self.rDiscount=0.001 #(r_ {re})
          self.rBonds=0.001 #(r_{b0})   
          self.zeta=0.1 #(zeta) 
          self.rBar=0.0075 #(rBar)
          self.csi=0.8 #(xi)
          self.csiDP=2.0#(xiDP)  
          self.inflationTarget=0.005#(DeltaP) 
          # policy
          self.policyKind='Mod'#'nn'#'ModAll'#'Mod'
          self.startingPolicy=500#(policy starting time)
          self.policyVariable=0.512#1.625##2.876#0.512#1.625#2.231#1.053
          self.maxPublicDeficitAusterity=self.policyVariable#(d)
          self.upsilonConsumer=self.policyVariable#10.0
          self.deltaLaborPolicy=self.delta/2.0
          self.epsilon=0.1
          self.k=30.0
          #timing  collecting simulation data
          self.timeCollectingStart=0#
          self.LtimeCollecting=[]
          self.printAgent='no' 
          for cycle in range(self.ncycle):
              self.LtimeCollecting.append(cycle)
          #name='munCo'+str(self.ncountry)+'beta'+str(self.beta)+'pol'+self.policyKind+'PolVar'+str(self.policyVariable) 
          name='muxSnCo'+str(self.ncountry)+'upsilon2'+str(self.upsilon2)+'pol'+self.policyKind+'PolVar'+str(self.policyVariable)
          #name='bdnCo'+str(self.ncountry)+'beta'+str(self.beta)+'pol'+self.policyKind+'PolVar'+str(self.policyVariable)
          # +'LPupsilon'+str(self.upsilonConsumer)+'epsilon'+str(self.epsilon)+'k'+str(self.k) 
          if name!=self.name:
             print 'self.name ', self.name
             print 'name      ', name 
             print 'stop', stop  
        
      def directory(self):
          newpath=self.folder
          if os.path.exists(newpath)==False:
             os.makedirs(newpath)   

     
