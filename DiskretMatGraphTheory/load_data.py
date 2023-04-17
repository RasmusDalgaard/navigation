# import osmnx
import osmnx as ox
import networkx as nx
import shapely.geometry as sh
import geopandas as gpd
import matplotlib.pyplot as plt

place_name = "Ballerup Kommune, Region Hovedstaden, Danmark"
# Graph
graph = ox.graph_from_place(place_name, network_type="drive")

# Reprojecting data into UTM
graph_proj = ox.project_graph(graph)
ox.plot_graph(graph_proj)

#NEW
address1 = "Violvænget 14, Ballerup"
address2 = "Hybenvænget 25, Ballerup"
#address1 = str(input())
#address2 = str(input())
points_list = [sh.Point(reversed(ox.geocoder.geocode(address1))), sh.Point(reversed(ox.geocoder.geocode(address2)))]

Gc = ox.consolidate_intersections(graph_proj, rebuild_graph=True, tolerance=20, dead_ends=False)
points = gpd.GeoSeries(points_list, crs='epsg:4326')
points_proj = points.to_crs(graph_proj.graph['crs'])
nearest_nodes = [ox.get_nearest_node(Gc, (pt.y, pt.x), 'euclidean') for pt in points_proj]
#/NEW

# Get nodes and edges
nodes_proj, edges_proj = ox.graph_to_gdfs(Gc)

# Calculate the coverage area (m2) of the street network
convex_hull = edges_proj.unary_union.convex_hull
area = convex_hull.area

# Calculate statistics
stats = ox.basic_stats(graph_proj, area=area)

# Centroid (center of area) 
centroid = convex_hull.centroid

# Get maximum x coordinate of the nodes (the most eastern x_coordinate in the area)
nodes_proj['X'] = nodes_proj.x.astype(float)

max_x = nodes_proj['X'].max()

# Retrieve most eastern node using the max_x
target = nodes_proj.loc[nodes_proj['X']==max_x, 'geometry'].values[0]

# Get origin x and y coordinates
origin_x = centroid.x
origin_y = centroid.y

# Get target x and y coordinates
target_x = target.x
target_y = target.y

# Find ID of closest nodes
source_node = ox.nearest_nodes(graph_proj, origin_x, origin_y)
target_node = ox.nearest_nodes(graph_proj, target_x, target_y)

# Find ID of closest nodes
source_node = ox.nearest_nodes(graph_proj, origin_x, origin_y)
target_node = ox.nearest_nodes(graph_proj, target_x, target_y)

# Find shortest path (Returns a set of node ids)
route = nx.shortest_path(G=Gc, source=nearest_nodes[0], target=nearest_nodes[1], weight='distance')
print(route)
route_edges = set(ox.utils_graph.get_route_edge_attributes(Gc, route, "name"))
print(route_edges)
fig, ax = ox.plot_graph_route(Gc, route)

# Extract info about nodes along shortest path
route_nodes = nodes_proj.loc[route] # This is a geo dataframe with all the nodes along the route
route_line = shapely.geometry.LineString(list(route_nodes.geometry.values)) # This is coordinates of all the nodes along the route

# Create a dataframe from LineString with a geometry column and a osmids column
# geometry is the column for all the coordinates of the nodes along the route
# osmids is the column for all the node ids along the route
# Insert LineString with coordinates into the first row of geometry
route_geom = gpd.GeoDataFrame(
    {
         "geometry": [route_line],
         "osmids": [route]
    },
    crs=edges_proj.crs
)

# Length of route in meters
route_geom['length_m'] = route_geom.length


# Plot the route with buildings and roads
buildings = ox.geometries_from_place(place_name, {'building':True})
buildings = buildings.to_crs(crs=edges_proj.crs)

fig, ax = plt.subplots()
edges_proj.plot(ax=ax, linewidth=0.75, colors='gray')
nodes_proj.plot(ax=ax, markersize=2, color='gray')
buildings.plot(ax=ax, facecolor='khaki', alpha=0.7)
route_geom.plot(ax=ax, linewidth=1, linestyle='-', color='red')