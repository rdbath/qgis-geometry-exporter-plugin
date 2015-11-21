# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryExporter
                                 A QGIS plugin
 Export feature geometry to GML, WKT, GeoJSON...
                             -------------------
        begin                : 2015-11-19
        copyright            : (C) 2015 by Juergen Weichand
        email                : juergen@weichand.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeometryExporter class from file GeometryExporter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geometry_exporter import GeometryExporter
    return GeometryExporter(iface)
