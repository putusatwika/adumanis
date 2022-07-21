# Import libraries
from fileinput import filename
from pydantic import FilePath
import shapefile as sf
import numpy as np
import sys, os
import geopandas as gpd
import pandas as pd
import adumanis

def adumanis_process(id_file, nibcontrol, tolerance, weight):
    for file in os.listdir(id_file):
        # Check whether file is in text format or not
        if file.endswith(".shp"):
            file_path = f"{id_file}/{file}"
    
    ShapefileDir = file_path
    fileName = ShapefileDir.split("/")[-1][0:-4]
    df = gpd.read_file(ShapefileDir)

    # if weight == "" or weight == 0:
    #     print ("Menggunakan weight")
    
    # READ FILE INPUT
    ShapeFile = sf.Reader(ShapefileDir)
    Fields = ShapeFile.fields
    Shapes = ShapeFile.shapes()
    Records = ShapeFile.records()

    NIBIndex = adumanis.findNIBIndex(Fields)    

    #SETUP First Point to create small coordinate
    # Minimize big value of each point, make it easier to calculate
    # with average of all first shape

    X = Y = 0
    for i in range (1, len(Shapes[0].points)):
        X = Shapes[0].points[i][0]+X
        Y = Shapes[0].points[i][1]+Y
    X = X/i
    Y = Y/i

    # Parse point
    dataPersils = []
    numControl = 0
    numObserve = 0
    persilNonControl = []
    numParcel = len(Shapes)
    for p in range (numParcel):
        controlStatus = 0
        if(Records[p][NIBIndex] in nibcontrol):
            controlStatus = True
        else:
            controlStatus = False
            persilNonControl.append(Records[p][NIBIndex])

        point =adumanis.Points()
        dataPoint = []
        idx = 0
        for q,tempP in enumerate (Shapes[p].points):
            x = tempP[0] - X 
            y = tempP[1] - Y
            dataPoint.append([x,y,idx])
            idx = idx +1
        point.add(Records[p][NIBIndex], controlStatus, dataPoint)
        dataPersils.append(point)
        #menghitung jumlah point control
        if(controlStatus == True):
            numControl = numControl+len(Shapes[p].points)-1
        else:
            numObserve = numObserve+len(Shapes[p].points)-1

    ## TIE POINT CREATOR
    tieGroups = []
    tieGroups.clear()
    for persilI in range (len(dataPersils)):
        lengthI = len(dataPersils[persilI].points) -1
        for pointI in range (lengthI):
            tiePoint = adumanis.TiePoints()
            NIBA = dataPersils[persilI].nib
            # indexA = dataPersils[persilI].ponits[pointI][2]
            indexA = pointI
            controlA = dataPersils[persilI].isControl
            xA = dataPersils[persilI].points[pointI][0]
            yA = dataPersils[persilI].points[pointI][1]

            for persilJ in range (persilI, len(dataPersils)):
                if(persilI != persilJ):    
                    lengthJ = len(dataPersils[persilJ].points) -1
                    for pointJ in range (lengthJ):
                        NIBB = dataPersils[persilJ].nib
                        indexB = pointJ
                        # indexB = dataPersils[persilJ].points[pointJ][2]
                        controlB = dataPersils[persilJ].isControl
                        xB = dataPersils[persilJ].points[pointJ][0]
                        yB = dataPersils[persilJ].points[pointJ][1]

                        a = dataPersils[persilI].points[pointI][:2]
                        b = dataPersils[persilJ].points[pointJ][:2]
                        dist = adumanis.Euclidean(a,b)
                        if(dist <= tolerance):
                            oldGroup = False
                            for (n, eachGroup) in enumerate (tieGroups):
                                if (eachGroup.isGrouped(NIBA, indexA)):
                                    oldGroup = True
                                    if (not eachGroup.isGrouped(NIBB, indexB)):
                                        tieGroups[n].add(NIBB, indexB, controlB, xB, yB)
                                elif (eachGroup.isGrouped(NIBB, indexB)):
                                    oldGroup = True
                                    if (not eachGroup.isGrouped(NIBA, indexA)):
                                        tieGroups[n].add(NIBA, indexA, controlA, xA, yA)

                            if(not oldGroup):
                                if not tiePoint.isGrouped(NIBA, indexA):
                                    tiePoint.add(NIBA, indexA, controlA, xA, yA)
                                tiePoint.add(NIBB, indexB, controlB, xB, yB)
            
            if (tiePoint.length() > 0):
                tieGroups.append(tiePoint)
            
            alone = True
            for (n, eachGroup) in enumerate (tieGroups):
                if (eachGroup.isGrouped(NIBA, indexA)):
                    alone = False
            
            if (alone):
                alonePoint = adumanis.TiePoints()
                alonePoint.add(NIBA, indexA, controlA, xA, yA)
                tieGroups.append(alonePoint)

    ## PARAMTER CHECKING
    numFreeTiePoint = 0
    for (n, eachGroup) in enumerate (tieGroups):
        if (not eachGroup.isContainControl()):
            numFreeTiePoint = numFreeTiePoint+1

    paramFreeTiePoint = numFreeTiePoint*2
    paramPointNonControl = numObserve *2
    paramPersilNonControl = (numParcel-len(nibcontrol)) * 4

    # Cek apakah observer lebih banyak dari parameter
    numParams = paramPersilNonControl + paramFreeTiePoint

    # Its still confuse (please find away to fix it
    numObs = paramPointNonControl
    if numParams > numObs:
        print ("Tidak bisa dilanjutkan, parameter lebih banyak dari titik yang diobservasi")
        return (0)
        sys.exit(0)
    
    ## CREATE MATRIX
    matrixA = np.zeros((numObs,numParams))
    matrixF = np.zeros((numObs,1))

    row = -1
    col = -1
    colPersilStart = paramFreeTiePoint

    for (i, tie) in enumerate (tieGroups):
        tieWithControl = tie.isContainControl()
        if (not tieWithControl):
            col = col+1
        for j in range (tie.length()):
            if(not tie.control[j]):
                row = row + 1
                
                idxPersil = persilNonControl.index(str(tie.nib[j]))
                matrixA[2*row , colPersilStart + 4*idxPersil] = tie.x[j]  
                matrixA[2*row , colPersilStart + 4*idxPersil + 1] = tie.y[j] * -1 
                matrixA[2*row , colPersilStart + 4*idxPersil + 2] = 1
                matrixA[2*row , colPersilStart + 4*idxPersil + 3] = 0 

                matrixA[2*row+1 , colPersilStart + 4*idxPersil] = tie.y[j]  
                matrixA[2*row+1 , colPersilStart + 4*idxPersil + 1] = tie.x[j] 
                matrixA[2*row+1 , colPersilStart + 4*idxPersil + 2] = 0
                matrixA[2*row+1 , colPersilStart + 4*idxPersil + 3] = 1 

                if(tieWithControl):
                    #Bentuk matrixF
                    # [x, y] = tie.controlPoint()
                    [x, y] = tie.closestControl(tie.x[j],tie.y[j])
                    matrixF[2*row,0] = x
                    matrixF[2*row+1,0] = y
                else:
                    # isikan yang -1 dan -1 di awal
                    matrixA[2*row, 2*col] = -1
                    matrixA[2*row+1, 2*col+1]  = -1
    
    #SOLVE THE MATRIX CALCULATION
    At = np.transpose(matrixA)
    AtA = np.mat(At) * np.mat(matrixA)
    AtF = np.mat(At) * np.mat(matrixF)

    sol = np.linalg.solve(AtA, AtF)

    #CREATE THE NEW POINT
    #REVERSE POINT TO NIB
    dtype = [('nib', np.unicode_, 16), ('index', int), ('x', float),('y',float)]
    finalPoint = []
    idx = -1
    for (i, tie) in enumerate (tieGroups):
        tieWithControl = tie.isContainControl()
        if not tieWithControl:
            idx = idx+1
        for j in range (tie.length()):
            if tieWithControl:
                newX, newY= tie.closestControl(tie.x[j], tie.y[j])
                if (tie.control[j]):
                    newPoint = (tie.nib[j], tie.index[j], tie.x[j]+X, tie.y[j]+Y)
                else:
                    newPoint = (tie.nib[j], tie.index[j], newX+X, newY+Y)
                
            else:
                # take the result from solution
                # for coordinate x and y
                newPoint = (tie.nib[j], tie.index[j], sol[2*idx]+X, sol[2*idx+1]+Y)
            
            finalPoint.append(newPoint)
    
    sortPoint = np.array(finalPoint, dtype = dtype) 
    sortPoint = np.sort(sortPoint, order=['nib', 'index'])

    # ## EXPORT PERSIL 
    location = id_file+'/out'
    w = sf.Writer(location, ShapeType = 5)
    w.field('NIB','C', 9)

    lastNIB = 'NULL'
    coordinates = []
    firstIndex = 0
    for i in range (len(sortPoint)):
        currNIB = sortPoint[i][0]
        if (lastNIB != currNIB): 
            if len(coordinates) > 2:
                data = [sortPoint[firstIndex][2], sortPoint[firstIndex][3]]
                coordinates.append(data)
                
                if sortPoint[i][1] ==0:
                    firstIndex = i
                
                
                w.record(NIB = lastNIB)
                w.poly([coordinates])
            lastNIB = currNIB
            coordinates.clear()
        
            data = [sortPoint[i][2], sortPoint[i][3]]
            coordinates.append(data)
            
        else:
            data = [sortPoint[i][2], sortPoint[i][3]]
            coordinates.append(data)

    #append for the last coordinates point (the last parcel)
    data = [sortPoint[firstIndex][2], sortPoint[firstIndex][3]]
    coordinates.append(data)
    w.record(NIB = lastNIB)
    w.poly([coordinates])    
    w.close()
    return {"msg":"Success create the file"}, location



