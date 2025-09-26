import csv

class PrintParameters:
      def __init__(self,name,folder):
          self.name=name
          self.folder=folder 
 
      def printingPara(self,para,run):
          Dvar=(vars(para))
          #print Dvar
          nameAgg=self.folder+'/'+self.name+'r'+str(run)+'Para.csv'
          C=[['parameter', 'values']]  
          for var in Dvar:
              if var!='LtimeCollecting' and var!='Lrun':
                 xc=[var,Dvar[var]]
                 C.append(xc) 
          c=open(nameAgg,'wb')  
          writer = csv.writer(c)
          writer.writerows(C)
          c.close()
