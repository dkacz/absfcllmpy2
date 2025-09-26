# mind.py


import random

class Mind:
      def __init__(self,ide,delta,country,minMarkUp,xE,theta):
          self.ide=ide
          self.delta=delta 
          self.country=country
          self.minMarkUp=minMarkUp
          self.xE=xE
          self.mk=minMarkUp  
          self.theta=theta

      def alphaParameterSmooth16(self,phi,w,inventory,pastInventory,price,productionEffective,xSold):
          x_prod=productionEffective
          x_sold=xSold        
          p=price
          xFullSelling='nn'
          pFullSelling='nn' 
          res=self.theta
          previousTargetInv=res*self.xE
          pastEx=self.xE
          self.deltaX=self.delta#/2.0   
          if x_sold>=pastEx:
             self.xE=random.uniform(self.xE,self.xE*(1+self.deltaX))
             pE=random.uniform(p,p*(1+self.delta))
             if pE<(1+self.minMarkUp)*(w/float(phi)):  
                pE=(1+self.minMarkUp)*(w/float(phi))   
             xE=self.xE
             if xE*(1+res)-inventory>0:
                xP=xE*(1+res)-inventory
             if xE*(1+res)-inventory<=0:
                 xP=0 
             self.xProducing=xP
             self.pSelling=pE
          elif x_sold<pastEx and  x_prod+pastInventory<pastEx:
             if x_sold>=x_prod+pastInventory:
                self.xE=self.xE
                xE=self.xE
                pE=p
                if pE<(1+self.minMarkUp)*(w/float(phi)):  
                   pE=(1+self.minMarkUp)*(w/float(phi))  
                if xE*(1+res)-inventory>0:
                   xP=xE*(1+res)-inventory
                if xE*(1+res)-inventory<=0:
                   xP=0
                self.xProducing=xP
                self.pSelling=pE
             if x_sold<x_prod+pastInventory:
                pE=random.uniform(p,p*(1-self.delta))  
                if pE<(1+self.minMarkUp)*(w/float(phi)):  
                   pE=(1+self.minMarkUp)*(w/float(phi))                
                self.xE=random.uniform(self.xE,self.xE*(1-self.deltaX))
                xE=self.xE
                if xE*(1+res)-inventory>0:
                   xP=xE*(1+res)-inventory
                if xE*(1+res)-inventory<=0:
                   xP=0 
                self.xProducing=xP
                self.pSelling=pE
          elif x_sold<pastEx and  x_prod+pastInventory>=pastEx:
             self.xE=random.uniform(self.xE,self.xE*(1-self.deltaX))            
             pE=random.uniform(p,p*(1-self.delta))
             if pE<(1+self.minMarkUp)*(w/float(phi)):  
                pE=(1+self.minMarkUp)*(w/float(phi))   
             xE=self.xE
             if xE*(1+res)-inventory>0:
                xP=xE*(1+res)-inventory
             if xE*(1+res)-inventory<=0:
                xP=0 
             self.xProducing=xP
             self.pSelling=pE 

      def alphaParameterSmooth17(self,phi,w,inventory,pastInventory,price,productionEffective,xSold):
          x_prod=productionEffective
          x_sold=xSold        
          p=price
          xFullSelling='nn'
          pFullSelling='nn' 
          res=self.theta
          previousTargetInv=res*self.xE
          pastEx=self.xE   
          if x_sold>=pastEx:
             self.xE=random.uniform(self.xE,self.xE*(1+self.delta))
             pE=random.uniform(p,p*(1+self.delta))
             if pE<(1+self.minMarkUp)*(w/float(phi)):  
                pE=(1+self.minMarkUp)*(w/float(phi))   
             xE=self.xE
             if xE*(1+res)-inventory>0:
                xP=xE*(1+res)-inventory
             if xE*(1+res)-inventory<=0:
                 xP=0 
             self.xProducing=xP
             self.pSelling=pE
          else:
                pE=random.uniform(p,p*(1-self.delta))  
                if pE<(1+self.minMarkUp)*(w/float(phi)):  
                   pE=(1+self.minMarkUp)*(w/float(phi))                
                self.xE=random.uniform(self.xE,self.xE*(1-self.delta))
                xE=self.xE
                if xE*(1+res)-inventory>0:
                   xP=xE*(1+res)-inventory
                if xE*(1+res)-inventory<=0:
                   xP=0 
                self.xProducing=xP
                self.pSelling=pE

          
