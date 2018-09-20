import math
from neo4j.v1 import GraphDatabase

def haversine(coord1, coord2):
    """
    Haversine function used to calculate geodesic.
    """
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    R = 6371000 # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * 	math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_in_meters = R * c # output distance in meters
    # km = distance_in_meters / 1000.0 # output distance in kilometers
    # meters = round(distance_in_meters, 3)
    # km = round(km, 3)
    return distance_in_meters

def edges_from_line(geom, attrs, simplify=True, geom_attrs=True):
    """
    Forked from networkx's edges_from_line function

    Generate edges for each line in geom
    Written as a helper for read_shp
    Parameters
    ----------
    geom:  ogr line geometry
        To be converted into an edge or edges
    attrs:  dict
        Attributes to be associated with all geoms
    simplify:  bool
        If True, simplify the line as in read_shp
    geom_attrs:  bool
        If True, add geom attributes to edge as in read_shp
    Returns
    -------
     edges:  generator of edges
        each edge is a tuple of form
        (node1_coord, node2_coord, attribute_dict)
        suitable for expanding into a networkx Graph add_edge call
    """
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("edges_from_line requires OGR: http://www.gdal.org/")

    if geom.GetGeometryType() == ogr.wkbLineString:
        if simplify:
            edge_attrs = attrs.copy()
            last = geom.GetPointCount() - 1
            yield (geom.GetPoint_2D(0), geom.GetPoint_2D(last), edge_attrs)
        else:
            for i in range(0, geom.GetPointCount() - 1):
                pt1 = geom.GetPoint_2D(i)
                pt2 = geom.GetPoint_2D(i + 1)
                edge_attrs = attrs.copy()
                yield (pt1, pt2, edge_attrs)
    elif geom.GetGeometryType() == ogr.wkbMultiLineString:
        for i in range(geom.GetGeometryCount()):
            geom_i = geom.GetGeometryRef(i)
            for edge in edges_from_line(geom_i, attrs, simplify, geom_attrs):
                yield edge

class GraphGenerator(object):
    """
    class has utility functions that can be used to load
    data read from a .shp file and convert it to a directed graph
    using neo4j.
    """
    
    def __init__(self):
        uri = "bolt://localhost:7687"
        user = 'neo4j'
        password = 'neopass'
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    @staticmethod
    def _is_node(tx, node):
        result = tx.run("MATCH (n:Node) WHERE n.name = $name RETURN count(n);", name=node)
        for record in result:
            if record[0] > 0:
                return True
        return False
    
    @staticmethod
    def already_has_edge(tx, node1, node2):
        result = tx.run(
            "RETURN EXISTS((:Node {name: $node1 })-[:connected_to]-(:Node {name: $node2}))", node1=node1, node2=node2
        )
        return result.single()[0]

    @staticmethod
    def are_nodes(tx, node1, node2):
        result = tx.run(
            "MATCH (n:Node) WHERE n.name in [$node1, $node2] return count(n);",
            node1=node1, node2=node2
        )
        if result.single()[0] == 2:
            return True
        return False


    def create_graph_from_shp(self, path, simplify=True, geom_attrs=True, strict=True):
        """
        Fork of networkx's read_shp function updated for use with neo4j.

        Generates a Neo4j graph from point and line shapefiles.
        The Esri Shapefile or simply a shapefile is a popular geospatial vector
        data format for geographic information systems software. It is developed
        and regulated by Esri as a (mostly) open specification for data
        interoperability among Esri and other software products.
        See https://en.wikipedia.org/wiki/Shapefile for additional information.
        """
        try:
            from osgeo import ogr
        except ImportError:
            raise ImportError("read_shp requires OGR: http://www.gdal.org/")

        if not isinstance(path, str):
            return
            
        shp = ogr.Open(path)
        if shp is None:
            raise RuntimeError("Unable to open {}".format(path))
        for lyr in shp:
            fields = [x.GetName() for x in lyr.schema]
            for f in lyr:
                g = f.geometry()
                if g is None:
                    if strict:
                        raise Exception("Bad data: feature missing geometry")
                    else:
                        continue
                flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
                attributes = dict(zip(fields, flddata))
                attributes["ShpName"] = lyr.GetName()
                # Note:  Using layer level geometry type
                # if g.GetGeometryType() == ogr.wkbPoint:
                #     net.add_node((g.GetPoint_2D(0)), **attributes)
                if g.GetGeometryType() in (ogr.wkbLineString,
                                            ogr.wkbMultiLineString):
                    for edge in edges_from_line(g, attributes, simplify,
                                                geom_attrs):
                        e1, e2, attr = edge
                        node1 = str(e1[1]) +','+str(e1[0])
                        node2 = str(e2[1]) +','+str(e2[0])
                        try:
                            attr.update(
                                {
                                    'weight': haversine(e1, e2),
                                    'node_1_lon': e1[0],
                                    'node_1_lat': e1[1],
                                    'node_2_lon': e2[0],
                                    'node_2_lat': e2[1]
                                }
                            )
                            self.add_node(node1, node2, **attr)
                        except Exception as e:
                            print(e)
                else:
                    if strict:
                        raise Exception("GeometryType {} not supported".
                                            format(g.GetGeometryType()))
        
    def add_node(self, node1, node2, **kwargs):
        weight = kwargs.get('weight')
        with self._driver.session() as session:
            if session.write_transaction(self.are_nodes, node1, node2):
                try:
                    if not session.write_transaction(self.already_has_edge, node1, node2):
                        session.run(
                            "MATCH (d:Node {name: $node1}), (o:Node {name: $node2}) "
                            "CREATE (d)-[:connected_to {weight: $weight}]->(o);",
                            node2=node2, node1=node1, weight=weight
                        )
                except Exception as e:
                    print(e)
            elif session.write_transaction(self._is_node, node1):
                try:
                    session.run("MATCH (d:Node) WHERE d.name = $name "
                    "CREATE (:Node {name: $node2, lat: $lat, lon: $lon})-[:connected_to {weight: $weight}]->(d);",
                     name=node1, node2=node2, weight=weight,
                     lat=kwargs.get('node_2_lat'), lon=kwargs.get('node_2_lon'))
                except Exception as e:
                   print(e)
            elif session.write_transaction(self._is_node, node2):
                try:
                    session.run("MATCH (d:Node) WHERE d.name = $name "
                    "CREATE (:Node {name: $node1, lat: $lat, lon: $lon})-[:connected_to {weight: $weight}]->(d);",
                    name=node2, node1=node1, weight=weight,
                    lat=kwargs.get('node_1_lat'), lon=kwargs.get('node_1_lon'))
                except Exception as e:
                   print(e)
            else:
                try:
                    session.run(
                        "CREATE (:Node {name: $node1, lat: $node_1_lat, lon: $node_1_lon})-[:connected_to {weight: $weight}]->(:Node {name: $node2, lat: $node_2_lat, lon: $node_2_lon});",
                    node2=node2, node1=node1, weight=weight,
                    node_1_lon=kwargs.get('node_1_lon'), node_1_lat=kwargs.get('node_1_lat'),
                    node_2_lon=kwargs.get('node_2_lon'), node_2_lat=kwargs.get('node_2_lat'))
                except Exception as e:
                    print(e)
