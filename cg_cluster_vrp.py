from geopy.distance import vincenty
import numpy as np
from random import shuffle,randint
from math import floor
import gmplot

CAPACITY = 13
def CreateDataArray():
#locations is set of points in a 2D plane
        geolocations = [(21.178609,72.85326),(21.16576,72.819162),(21.190458,72.818343),(21.196357,72.8381),(21.199291,72.845539),(21.173657,72.801709),(21.169425,72.793288),(21.165652,72.785903)]
        locations = [(21.178609,72.85326),(21.16576,72.819162),(21.190458,72.818343),(21.196357,72.8381),(21.199291,72.845539),(21.165652,72.785903),(21.169425,72.793288),(21.173657,72.801709)]
  	#geolocations = [[82, 76], [96, 44], [50, 5], [49, 8], [13, 7], [29, 89]]
  	nodes = [x for x in xrange(1,len(geolocations))]
#demands[i] represents demand at ith point in the plane.
  	demands = [0, 9, 2, 6, 9, 7, 2, 3]
  	data = [nodes,geolocations, demands,locations]
  	return data

def VincentyDistance(i,j):
        #Measures distance between two points on a sphere in km. i and j need to be tuples
        distance = vincenty(i,j).km
        return distance

def centroid(arr):
    length = arr.shape[0]
    sum_x = np.sum(arr[:, 0])
    sum_y = np.sum(arr[:, 1])
    return (sum_x/length, sum_y/length)

class CreateDistanceCallback(object):
        """Create callback to calculate distances between points."""
        def __init__(self, geolocations):
                """Initialize distance array and distance matrix."""
                size = len(geolocations)
                self.distList = []
                from_node = 0
                x1 = geolocations[from_node]
                for to_node in xrange(1,size):
                        x2 = geolocations[to_node]
                        tup = (to_node,VincentyDistance(x1, x2))
                        self.distList.append(tup)
                
                self.sortedList = self.distList[:]
                self.sortedList.sort(key=lambda member: member[1],reverse = False)

        def Distance(self, to_node):
                if to_node != 0:
                        return self.distList[to_node]
                else:
                        return 0

        def GetSortedDistList(self):
                return self.sortedList[:]

class SetOfClusters(CreateDistanceCallback):
        def __init__(self,demands,nodes):
                self.clusters = {}
                self.clusterSet = {}
                self.demands = demands
                self.availNodes = nodes[:]

        def ConstructClusters(self,geolocations):
                CreateDistanceCallback.__init__(self, geolocations)
                distList = self.GetSortedDistList()
                i = 0
                l1 = [(geolocations[0][0],geolocations[0][1])]
                while self.availNodes:
                        node = distList[-1][0]
                        self.clusters[i] = []
                        clusterDemand = 0
                        while clusterDemand + self.demands[node] <= CAPACITY:
                                clusterDemand += self.demands[node]
                                self.clusters[i].append(node)
                                self.availNodes.remove(node)         #Remove node from available nodes
                                nodeDup = [item for item in distList if item[0] == node]       
                                #Search for node in sorted distances list and remove it
                                distList.remove(nodeDup[0])
                                l1.append((geolocations[node][0],geolocations[node][1]))
                                dataMatrix = np.array(l1)
                                cg = centroid(dataMatrix)
                                nearest = float("inf")
                                for vertex in self.availNodes:
                                      currentDist = VincentyDistance(cg,geolocations[node])
                                      if currentDist < nearest:
                                              nearest = currentDist
                                              node = vertex
                        self.clusters[i].append(clusterDemand)
                        i+=1


        
        def AdjustClusters(self,geolocations,nodes):
                self.availNodes = nodes[:]
                for key in self.clusters:
                        cluster = self.clusters[key]
                        clusterDemand = cluster.pop()
                        flag = 0
                        l = [(geolocations[node][0],geolocations[node][1]) for node in cluster]
                        l.append((geolocations[0][0],geolocations[0][1]))
                        dataMatrix = np.array(l)
                        cg1 = centroid(dataMatrix)
                        clusterClone = cluster[:]
                        for node in clusterClone:
                                if flag == 1:
                                        l1 = [(geolocations[node][0],geolocations[node][1]) for n in cluster]
                                        l1.append((geolocations[0][0],geolocations[0][1]))
                                        dataMatrix = np.array(l1)
                                        cg1 = centroid(dataMatrix)
                                        d1 = VincentyDistance(cg1,geolocations[node])
                                else:
                                        d1 = VincentyDistance(cg1,geolocations[node])
                                for k in self.clusters:
                                        if k != key:
                                                cSet = self.clusters[k]
                                                if not cSet:
                                                        continue
                                                cDemand = cSet.pop()
                                                l2 = [(geolocations[node][0],geolocations[node][1]) for n in cSet]
                                                l2.append((geolocations[0][0],geolocations[0][1]))
                                                dataMatrix = np.array(l2)
                                                cg2 = centroid(dataMatrix)
                                                d2 = VincentyDistance(cg2,geolocations[node])
                                                if d2 < d1 and self.demands[node] + cDemand <= CAPACITY:
                                                        cluster.remove(node)
                                                        clusterDemand -= self.demands[node]
                                                        cSet.insert(1,node)
                                                        cDemand += self.demands[node]
                                                        cSet.append(cDemand)
                                                        flag = 1
                                                        break
                                                else:
                                                      cSet.append(cDemand)  
                        cluster.append(clusterDemand)


        def CleanClusters(self):
                i = 0
                for key in self.clusters:
                        if self.clusters[key][0] == 0:
                                continue
                        self.clusterSet[i] = []
                        cluster = self.clusters[key]
                        for node in cluster:
                                self.clusterSet[i].append(node)
                        i += 1
                                
                                

        def GetClusterSet(self):
                return self.clusterSet

class TSP(object):
        def __init__(self, geolocations,cluster):
                """Initialize distance array."""
                self.population = []
                self.cluster = cluster
                self.clusterLen = len(cluster) - 1
                size = len(geolocations)
                self.distMatrix = {}
                for from_node in xrange(0,size):
                        self.distMatrix[from_node] = {}
                        for to_node in xrange(from_node+1,size):
                                x1 = geolocations[from_node]
                                #y1 = geolocations[from_node][1]
                                x2 = geolocations[to_node]
                                #y2 = geolocations[to_node][1]
                                self.distMatrix[from_node][to_node] = VincentyDistance(x1, x2)

        def Distance(self, from_node, to_node):
                if from_node <= to_node:
                        return self.distMatrix[from_node][to_node]
                else:
                        return self.distMatrix[to_node][from_node]
                
        def CreatePopulation(self):
                """Takes a list of nodes as input and returns a list of lists as output each of which is randomly sorted"""
                n = 2*self.clusterLen
                if n == 2:
                        c = self.cluster[:]
                        demand = c.pop()
                        self.population.append(c)
                        return
                for i in xrange(n):
                        c = self.cluster[:]
                        demand = c.pop()
                        shuffle(c)
                        self.population.append(c)

        def CalcFitness(self):
                """Adds fitness for route in list of each cluster"""
                self.sumOfFitness = 0
                for cluster in self.population:
                        distance = 0
                        n = self.clusterLen - 1
                        for i in xrange(n):
                                distance += self.Distance(cluster[i],cluster[i+1])
                        distance += self.Distance(0,cluster[-1])
                        distance += self.Distance(0,cluster[0])
                        fitness = distance
                        self.sumOfFitness += fitness
                        cluster.append(distance)
                for cluster in self.population:
                        oddsOfSurvival = self.sumOfFitness - cluster.pop()
                        cluster.append(oddsOfSurvival)
                self.population.sort(key=lambda member: member[-1],reverse = True)

        def GenePoolSelect(self):
                """Selects those routes more often that have higher fitness. Routes with lesser fitness are selected less frequently."""
                sumOfFitness = 2*floor(self.sumOfFitness)
                n = len(self.population)
                self.index = []
                for j in xrange(2):
                        randNum = randint(0,sumOfFitness)
                        for i in xrange(0,n):
                                fitness = self.population[i][-1]
                                randNum -=  fitness
                                if randNum < 0:
                                        break
                        self.index.append(i) 

        def Crossover(self):
                parentA = self.population[self.index[0]][0:-1]
                #print parentA
                sizeA = len(parentA)
                n = len(self.population)
                parentB = self.population[self.index[1]][0:-1]
                sizeB = len(parentB)
                if sizeA == 1:
                        for i in xrange(n):
                                discard = self.population[i].pop()

                #print parentB
                elif sizeA == 2:
                        for i in xrange(n):
                                discard = self.population[i].pop()

                else:
                        start = randint(0,sizeA-2)
                        end = randint(start+1,sizeA-1)
                        offspring1 = parentA[start:end]
                        for i in xrange(sizeB):
                                if parentB[i] in offspring1:
                                        continue
                                else:
                                        offspring1.append(parentB[i])
                        start = randint(0,sizeB-2)
                        end = randint(start+1,sizeB-1)
                        offspring2 = parentB[start:end]
                        for i in xrange(sizeA):
                                if parentA[i] in offspring2:
                                        continue
                                else:
                                        offspring2.append(parentA[i])
                                        
                        for i in xrange(n):
                                        discard = self.population[i].pop()
                        self.population.append(offspring1)
                        self.population.append(offspring2)


        def Mutate(self):
                n = len(self.population)
                if n == 1 or n == 2:
                        return
                else:
                        #Swapping elements in offspring1
                        offspring1 = self.population.pop()
                        swapIndex1 = randint(0,self.clusterLen-1)
                        swapIndex2 = randint(0,self.clusterLen-1)
                        ele1 = offspring1[swapIndex1]
                        ele2 = offspring1[swapIndex2]
                        discard = offspring1.pop(swapIndex1)
                        offspring1.insert(swapIndex1,ele2)
                        discard = offspring1.pop(swapIndex2)
                        offspring1.insert(swapIndex2,ele1)


                        #Swapping elements in offspring2
                        offspring2 = self.population.pop()
                        swapIndex1 = randint(0,self.clusterLen-2)
                        swapIndex2 = randint(0,self.clusterLen-2)
                        ele1 = offspring2[swapIndex1]
                        ele2 = offspring2[swapIndex2]
                        discard = offspring2.pop(swapIndex1)
                        offspring2.insert(swapIndex1,ele2)
                        discard = offspring2.pop(swapIndex2)
                        offspring2.insert(swapIndex2,ele1)

                        #Reordering path in offspring1
                        part1 = offspring1[:self.clusterLen/2]
                        part2 = offspring1[self.clusterLen/2:]
                        part2.extend(part1)
                        offspring1 = part2
                        #Reordering path in offspring2
                        part1 = offspring2[:self.clusterLen/2]
                        part2 = offspring2[self.clusterLen/2:]
                        part2.extend(part1)
                        offspring2 = part2

                        self.population.append(offspring1)
                        self.population.append(offspring2)

        def Fittest(self):
                n = len(self.population)
                if n == 1 or n == 2:
                        return
                offspring1 = self.population.pop()
                offspring2 = self.population.pop()
                distance1,distance2 = 0,0
                n = self.clusterLen - 1
                for i in xrange(n):
                        distance1 += self.Distance(offspring1[i],offspring1[i+1])
                distance1 += self.Distance(0,offspring1[-1])
                distance1 += self.Distance(0,offspring1[0])
                for i in xrange(n):
                        distance2 += self.Distance(offspring2[i],offspring2[i+1])
                distance2 += self.Distance(0,offspring2[-1])
                distance2 += self.Distance(0,offspring2[0])
                print offspring1
                print offspring2
                print distance1
                print distance2
                if distance1 < distance2:
                        self.population.append(offspring1)
                else:
                        self.population.append(offspring2)
                
        def GetPopulation(self):
                return self.population


def RoutePlot(individuals,geolocations):
        table = {}
        i = 0
        xDepot = geolocations[0][0]
        yDepot = geolocations[0][1]
        for cluster in individuals:
                table[i] = [[],[]]
                table[i][0].append(xDepot)
                table[i][1].append(yDepot)
                for node in cluster:
                        table[i][0].append(geolocations[node][0])
                        table[i][1].append(geolocations[node][1])
                table[i][0].append(xDepot)
                table[i][1].append(yDepot)
                i+=1
        gmap = gmplot.GoogleMapPlotter(xDepot, yDepot, 15)
        for key in table:
                latitudes = table[key][0]
                longitudes = table[key][1]
                r = lambda: randint(0,255)
                a1,a2,a3 = hex(r()),hex(r()),hex(r())
                randomColor = '#' + a1[2] + a1[3] + a2[2] + a2[3] + a3[2] + a3[3]
                gmap.plot(latitudes, longitudes, randomColor, edge_width=4)
                gmap.scatter(latitudes,longitudes,'k',marker = True)
        gmap.draw("myclustermap.html")

        

def main():
  	data = CreateDataArray()
  	nodes = data[0]
  	geolocations = data[1]
  	demands = data[2]
        locations = data[3]
  	DistBetweenLocations = CreateDistanceCallback(geolocations)
  	#print DistBetweenLocations.GetSortedDistList()
        c = SetOfClusters(demands,nodes)
        c.ConstructClusters(geolocations)
        c.AdjustClusters(geolocations,nodes)
        c.CleanClusters()
        s = c.GetClusterSet()
        individuals = []
        for key in s:
                tsp = TSP(geolocations,s[key])
                tsp.CreatePopulation()
                f = tsp.CalcFitness()
                tsp.GenePoolSelect()
                tsp.Crossover()
                tsp.Mutate()
                tsp.Fittest()
                p = tsp.GetPopulation()
                individuals.append(p.pop())
        print individuals
        RoutePlot(individuals,geolocations)


if __name__ == '__main__':
        main()

