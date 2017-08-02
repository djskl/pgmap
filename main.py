# encoding:utf-8
from mapscript import outputFormatObj, MS_IMAGEMODE_RGBA, MS_ON, mapObj, layerObj, MS_LAYER_RASTER, styleObj, colorObj, \
    classObj
from settings import MAP_PROJ, MAP_EXTENT, MAP_SIZE, MAP_IMG_TYPE, PG_NAME, PG_USER, PG_HOST, PG_PORT, PG_PWD
from osgeo import ogr
import psycopg2


class RasterDB(object):
    conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_NAME, user=PG_USER, password=PG_PWD)
    cursor = conn.cursor()

    @classmethod
    def getDataURL(self, table, column):
        return "PG: dbname={dbname} host={host} user={user} port={port} mode=2 schema=public table={table} column={column}". \
            format(host=PG_HOST, port=PG_PORT, dbname=PG_NAME, user=PG_USER, table=table, column=column)

    @classmethod
    def getExtent(self, rid):
        if not rid:
            return None

        self.cursor.execute("select ST_Astext(ST_Envelope(rast)) from tmean where rid = %s", (rid,))

        dao = self.cursor.fetchone()
        if dao is None:
            return None

        poly_wkt = dao[0]
        poly_geom = ogr.CreateGeometryFromWkt(poly_wkt)
        ext = poly_geom.GetEnvelope()

        return ext[0], ext[2], ext[1], ext[3]

def getStyle():
    style_obj = styleObj()

    style_obj.rangeitem = "pixel"

    style_obj.maxcolor = colorObj(175, 240, 233)
    style_obj.mincolor = colorObj(255, 255, 179)

    style_obj.maxvalue = 1
    style_obj.minvalue = -47

    clz_obj = classObj()
    clz_obj.setExpression("([pixel] >= -47 AND [pixel] <= 1)")
    clz_obj.insertStyle(style_obj)

    return clz_obj


def get_output_fmt():
    output_fmt = outputFormatObj("GD/PNG", MAP_IMG_TYPE)
    output_fmt.mimetype = "image/png"
    output_fmt.extension = MAP_IMG_TYPE
    output_fmt.imagemode = MS_IMAGEMODE_RGBA
    output_fmt.transparent = MS_ON


def render_map(rid):
    minx, miny, maxx, maxy = RasterDB.getExtent(rid)

    print minx, miny, maxx, maxy

    output_fmt = get_output_fmt()

    aMap = mapObj()

    aMap.setProjection(MAP_PROJ)

    aMap.setExtent(*MAP_EXTENT)
    aMap.setSize(*MAP_SIZE)
    aMap.setImageType(MAP_IMG_TYPE)
    aMap.status = MS_ON

    aMap.setOutputFormat(output_fmt)

    PGLayer = layerObj(aMap)
    PGLayer.type = MS_LAYER_RASTER
    PGLayer.status = MS_ON

    PGLayer.data = RasterDB.getDataURL("tmean", "rast")
    PGLayer.setFilter("rid=%s"%rid)

    PGLayer.setExtent(90.0, 57.8666666667, 92.1333333333, 60.0)

    PGLayer.setProjection(MAP_PROJ)

    clz_obj = getStyle()
    PGLayer.insertClass(clz_obj)

    print aMap.convertToString()

    imgobj = aMap.draw()
    imgobj.save("/tmp/1.png")

if __name__ == "__main__":
    render_map(1)
