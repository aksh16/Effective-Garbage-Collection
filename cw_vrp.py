"""Implementation of Clark-Wright to solve VRP
Only constraints apart from distance and time are vehicle capacity.
No split deliveries are allowed."""
from geopy.distance import vincenty
import gmplot
import random

CAPACITY = 13 #Maximum capacity for a vehicle

def CreateDataArray():
#locations is set of points in a 2D plane
        geolocations = [(21.178609,72.85326),(21.16576,72.819162),(21.190458,72.818343),(21.196357,72.8381),(21.199291,72.845539),(21.173657,72.801709),(21.169425,72.793288),(21.165652,72.785903)]
  	#geolocations = [[82, 76], [96, 44], [50, 5], [49, 8], [13, 7], [29, 89]]
  	nodes = [x for x in xrange(1,len(geolocations))]
#demands[i] represents demand at ith point in the plane.
  	demands = [0, 9, 2, 6, 9, 7, 2, 3]
  	data = [nodes,geolocations, demands]
  	return data

def distance(x1, y1, x2, y2):
  	# Manhattan distance
  	dist = abs(x1 - x2) + abs(y1 - y2)
  	return dist

def VincentyDistance(i,j):      #Measures distance between two points on a sphere in km. i and j need to be tuples
                        distance = vincenty(i,j).km
                        return distance
                
class CreateDistanceCallback(object):
        """Create callback to calculate distances between points."""
        def __init__(self, geolocations):
                """Initialize distance array."""
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

        def Savings(self,geolocations):
                """Create sorted savings list and matrix with distance and savings"""
                self.savings = [] #List to store savings
                size = len(geolocations)
                for from_node in xrange(1,size):
                        for to_node in xrange(from_node+1,size):
                                save = self.Distance(0,from_node) + self.Distance(0,to_node) - self.Distance(from_node,to_node)
                                member = (from_node,to_node,save) #(i,j,saving for i to j or j to i)
                                self.savings.append(member)
                self.savings.sort(key=lambda member: member[2],reverse = True)
                return self.savings


class CreateDemandCallback(object):
        """Create callback to get demands at each location."""

  	def __init__(self, demands):
    		self.demandList = demands

  	def Demand(self, from_node):
    		return self.demandList[from_node]

class BuildRoute(CreateDistanceCallback,CreateDemandCallback):
	"""Builds routes iteratively"""
  	def __init__(self,demands,geolocations,nodes):
		CreateDemandCallback.__init__(self,demands)
		CreateDistanceCallback.__init__(self,geolocations)
                self.routes = {} #Maintain set of routes
                routeCounter = 0 #Counts number of routes already created
                for saving in self.Savings(geolocations):
			iNode = saving[0]
			jNode = saving[1]
			iNodeDemand = int(self.Demand(iNode))
			jNodeDemand = int(self.Demand(jNode))
			#Temp = current volume filled + demand at i + demand at j
##                        total = route[marker][0] + int(self.Demand(saving[0])) + int(self.Demand(saving[1]))
##			if total > CAPACITY:
##				continue
			routeOfi = [key for key, value in self.routes.iteritems() if iNode in value] #Searching for i in the existing routes
			
			if routeOfi:
                                routeOfi = routeOfi[0]
##                      else:
##                                routeOfi = None
        
			routeOfj = [key for key, value in self.routes.iteritems() if jNode in value] #Searching for j in the existing routes
##			
			if routeOfj:
                                routeOfj = routeOfj[0]
##                        else:
##                                routeOfj = None
                        
			
			if iNode in nodes and jNode in nodes: # i and j are not in any route
                                total = iNodeDemand + jNodeDemand
                                if total > CAPACITY:
                                        continue
                                #If total is less than capacity then new route with i and j
                                self.routes[routeCounter] = [total,iNode,jNode]
                                routeCounter += 1
                                nodes.remove(iNode)
                                nodes.remove(jNode)

                        elif (iNode not in nodes and jNode in nodes) and (self.routes[routeOfi][0] + jNodeDemand <= CAPACITY): #There is a route with i and no route containing j
                                if self.routes[routeOfi][1] == iNode:
                                        self.routes[routeOfi].insert(1,jNode)
                                        self.routes[routeOfi][0] = self.routes[routeOfi][0] + jNodeDemand
                                        nodes.remove(jNode)
                                elif self.routes[routeOfi][-1] == iNode:
                                        self.routes[routeOfi].append(jNode)
                                        self.routes[routeOfi][0] = self.routes[routeOfi][0] + jNodeDemand
                                        nodes.remove(jNode)

                                        
                        elif (iNode in nodes and jNode not in nodes) and (self.routes[routeOfj][0] + iNodeDemand <= CAPACITY): #There is a route with j and no route containing i
                                if self.routes[routeOfj][1] == jNode:
                                        self.routes[routeOfj].insert(1,iNode)
                                        self.routes[routeOfj][0] = self.routes[routeOfj][0] + iNodeDemand
                                        nodes.remove(iNode)
                                elif self.routes[routeOfj][-1] == jNode:
                                        self.routes[routeOfj].append(iNode)
                                        self.routes[routeOfj][0] = self.routes[routeOfj][0] + iNodeDemand
                                        nodes.remove(iNode)

                        elif iNode not in nodes and jNode not in nodes:
                                if (self.routes[routeOfi][1] == iNode and self.routes[routeOfj][-1] == jNode) and (self.routes[routeOfi][0] + self.routes[routeOfj][0] <= CAPACITY):
                                        total = self.routes[routeOfi][0] + self.routes[routeOfj][0]
                                        discard = self.routes[routeOfj].pop(0)
                                        self.routes[routeOfi].extend(self.routes[routeOfj])

                                elif (self.routes[routeOfj][1] == jNode and self.routes[routeOfi][-1] == iNode) and (self.routes[routeOfi][0] + self.routes[routeOfj][0] <= CAPACITY):
                                        total = self.routes[routeOfi][0] + self.routes[routeOfj][0]
                                        discard = self.routes[routeOfi].pop(0)
                                        self.routes[routeOfj].extend(self.routes[routeOfi])

                nodedup = nodes[:]
                for node in nodedup:
                        self.routes[routeCounter] = [int(self.Demand(node)),node]
                        nodes.remove(node)
                        routeCounter += 1


        def RoutePlot(self,geolocations):
                self.routePlot = {}
                for key in self.routes:
                        self.routePlot[key] = [[],[]]
                        n = len(self.routes[key])
                        self.routePlot[key][0].append(geolocations[0][0])
                        self.routePlot[key][1].append(geolocations[0][1])
                        for element in xrange(1,n):
                                self.routePlot[key][0].append(geolocations[self.routes[key][element]][0])
                                self.routePlot[key][1].append(geolocations[self.routes[key][element]][1])
                        self.routePlot[key][0].append(geolocations[0][0])
                        self.routePlot[key][1].append(geolocations[0][1])
                        
                return self.routePlot                   


def MapPlot(table,xDepot,yDepot):
        gmap = gmplot.GoogleMapPlotter(xDepot, yDepot, 15)
        for key in table:
                latitudes = table[key][0]
                longitudes = table[key][1]
                r = lambda: random.randint(0,255)
                a1,a2,a3 = hex(r()),hex(r()),hex(r())
                randomColor = '#' + a1[2] + a1[3] + a2[2] + a2[3] + a3[2] + a3[3]
                gmap.plot(latitudes, longitudes, randomColor, edge_width=4)
                gmap.scatter(latitudes,longitudes,'k',marker = True)
        gmap.draw("mymap.html")
                                

def main():
  	data = CreateDataArray()
  	nodes = data[0]
  	geolocations = data[1]
  	demands = data[2]

  	DistBetweenLocations = CreateDistanceCallback(geolocations)
  #DistCallback = DistBetweenLocations.Distance
  #save = DistBetweenLocations.Savings(locations)
  	DemandsAtLocations = CreateDemandCallback(demands)
  	#print DistBetweenLocations.Savings(locations)
  	Routes = BuildRoute(demands,geolocations,nodes)
  	RoutesPlot = Routes.RoutePlot(geolocations)
  	MapPlot(RoutesPlot,geolocations[0][0],geolocations[0][1])
  	DemandCallback = DemandsAtLocations.Demand
  	print Routes.routes
  	print RoutesPlot
#save = CreateSavingsCallback(locations)

if __name__ == '__main__':
	main()
