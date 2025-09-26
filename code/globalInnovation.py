# globalInnovation.py
import random

class GlobalInnovation:
      def __init__(self,Lcountry,phi):
          self.DglobalPhi={}
          self.DglobalPhiTradable={}
          self.DglobalPhiNotTradable={} 
          for country in Lcountry:
              self.DglobalPhi[country]=phi
              self.DglobalPhiTradable[country]=phi
              self.DglobalPhiNotTradable[country]=phi

      def spillover(self,McountryFirm,time):
          for country in McountryFirm:
              sumPhi=0 
              LPhi=[]
              sumL=0
              sumPhiTradable=0 
              sumLTradable=0
              sumPhiNotTradable=0 
              sumLNotTradable=0   
              pastPhi=self.DglobalPhi[country] 
              for firm in McountryFirm[country]:
                  sumPhi=sumPhi+McountryFirm[country][firm].phi*McountryFirm[country][firm].A
                  sumL=sumL+McountryFirm[country][firm].A
                  if McountryFirm[country][firm].tradable=='yes':
                     sumPhiTradable=sumPhiTradable+McountryFirm[country][firm].phi*McountryFirm[country][firm].productionEffective
                     sumLTradable=sumLTradable+McountryFirm[country][firm].productionEffective
                  if McountryFirm[country][firm].tradable=='no':
                     sumPhiNotTradable=sumPhiNotTradable+McountryFirm[country][firm].phi*McountryFirm[country][firm].productionEffective
                     sumLNotTradable=sumLNotTradable+McountryFirm[country][firm].productionEffective   
                  LPhi.append(McountryFirm[country][firm].phi) 
              if len(McountryFirm[country])>0:
                 avPhi=0
                 if sumL>0:
                    avPhi=sumPhi/float(sumL)
                 avPhiTradable=0
                 if sumLTradable>0:
                    avPhiTradable=sumPhiTradable/float(sumLTradable)
                 avPhiNotTradable=0
                 if sumLNotTradable>0:
                    avPhiNotTradable=sumPhiNotTradable/float(sumLNotTradable)                 
                 phiCountry=self.DglobalPhi[country]
                 phiCountry=avPhi                 
                 if sumL<0.001:
                    phiCountry=1.0
                 self.DglobalPhi[country]=phiCountry
                 self.DglobalPhiTradable[country]=avPhiTradable
                 self.DglobalPhiNotTradable[country]=avPhiNotTradable  
            

