# //ADUMANIS LIBRARY
import numpy as np

class TiePoints:
    def __init__(self):
        self.nib = []        
        self.index = []
        self.control = []
        self.x = []
        self.y = []
    
    def destroy(self):
        self.nib.clear()
        self.index.clear()
        self.control.clear()
        self.x.clear()
        self.y.clear()
        
    def add(self, NIB, index, control, x, y):
        self.nib.append(NIB)
        self.index.append(index)
        self.control.append(control)
        self.x.append(x)
        self.y.append(y)
        
    def isContainControl(self):
        if True in self.control: return True 
        else: return False
    
    def isGrouped(self, nib, index):
        try:
            loc = self.nib.index(nib)
            if self.index[loc] == index :
                return True
            else:
                return False
        except:
            return False
    
#     def controlPoint(self):
#         #find control point in group
#         #if there are more than 1 control
#         #then you can return the average
#         x = 0
#         y = 0
#         count = 0
#         for i in range (len(self.control)):
#             if(self.control[i]):
#                 x = x+ self.x[i]
#                 y = y+ self.y[i]
#                 count = count +1
        
#         x = x/count
#         y = y/count
#         return x, y
    
    def closestControl(self, x, y):
        point = [x,y]
        closest = -1
        closestControl = []
        for i in range (len(self.control)):
            if (self.control[i]):
                control = [self.x[i] , self.y[i]]
                temp = Euclidean(point, control)
                if (closest == -1 or closest > temp):
                    closest = temp
                    closestControl = control
        
        return closestControl
    
    def show(self):
        print ("NIB\t","index\t","control\t","x\t\t","y")
        for i in range (len(self.nib)):
            print (self.nib[i],end ="\t")
            print (self.index[i],end ="\t")
            print (self.control[i],end ="\t")
            print (self.x[i],end ="\t")
            print (self.y[i])
            
    def length(self):
        return len(self.nib)
    

class Points:
    def __init__(self):
        self.nib = 0
        self.isControl = False
        self.points = []
    
    def add(self, persil, isControl, points):
        self.nib = persil
        self.isControl = isControl
        self.points = points
    
    def addPoint(self, point):
        self.points.append(point)

        

# Mendefinisikan fungsi pencarian jarak terdekat (Euclidean Distance)
def Euclidean(a, b):
    Distance = np.linalg.norm(np.array(a) - np.array(b))
    return Distance

def findNIBIndex(Fields):
    NIBIndex = 0
    ALATIndex = 0
    for i in range(len(Fields)):
        if Fields[i][0] == "NIB":
            NIBIndex = i - 1
        elif Fields[i][0] == "ALATUKUR":
            ALATIndex = i-1
    return NIBIndex