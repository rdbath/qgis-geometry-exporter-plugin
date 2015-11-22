# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeometryExporter
                                 A QGIS plugin
 Export feature geometry to GML, WKT, GeoJSON...
                              -------------------
        begin                : 2015-11-19
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Juergen Weichand
        email                : juergen@weichand.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QObject, SIGNAL
from PyQt4.QtGui import QAction, QIcon, QMessageBox
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from geometry_exporter_dialog import GeometryExporterDialog
from osgeo import gdal, ogr, osr
import os.path


class GeometryExporter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeometryExporter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = GeometryExporterDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geometry Exporter')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeometryExporter')
        self.toolbar.setObjectName(u'GeometryExporter')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeometryExporter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GeometryExporter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Geometry Exporter'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.add_action(
            None,
            text='About',
            callback=self.about,
            add_to_toolbar=None,
            parent=None)

        QObject.connect(self.dlg.cmbFormat, SIGNAL("currentIndexChanged(int)"), self.populate)
        QObject.connect(self.dlg.cmbConversion, SIGNAL("currentIndexChanged(int)"), self.populate)
        QObject.connect(self.dlg.proj, SIGNAL("crsChanged(QgsCoordinateReferenceSystem)"), self.populate)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Geometry Exporter'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def about(self):
        infoString = "<table><tr><td colspan=\"2\"><b>Geometry Exporter 0.5.1 - beta</b></td></tr><tr><td colspan=\"2\"></td></tr><tr><td>Author:</td><td>J&uuml;rgen Weichand</td></tr><tr><td>Mail:</td><td><a href=\"mailto:juergen@weichand.de\">juergen@weichand.de</a></td></tr><tr><td>Website:</td><td><a href=\"http://www.weichand.de\">http://www.weichand.de</a></td></tr></table>"
        QMessageBox.information(self.iface.mainWindow(), "About Geometry Exporter", infoString)

    def run(self):
        layer = self.iface.activeLayer()

        # layer must be activated
        if not layer:
            QMessageBox.critical(self.dlg, 'Error', u'Please select layer!')
            return


        # >= 1 feature must be selected
        if len(layer.selectedFeatures()) != 1:
            QMessageBox.critical(self.dlg, 'Error', u'Please select exactly one feature!')
            return
        else:
            self.dlg.show()
            self.feature = layer.selectedFeatures()[0]
            self.qgscrs = layer.crs()
            self.populate()


    #  http://gis.stackexchange.com/questions/90205/equivalent-function-to-shapelys-envelope-in-ogr
    def compute_envelope(self, geom):
        (minX, maxX, minY, maxY) = geom.GetEnvelope()

        # Create ring
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint_2D(minX, minY)
        ring.AddPoint_2D(maxX, minY)
        ring.AddPoint_2D(maxX, maxY)
        ring.AddPoint_2D(minX, maxY)
        ring.AddPoint_2D(minX, minY)

        # Create polygon
        poly_envelope = ogr.Geometry(ogr.wkbPolygon)
        poly_envelope.AddGeometry(ring)
        return poly_envelope

    def populate(self):

        if self.feature:

            qgsgeom = self.feature.geometry()
            qgscrs = self.dlg.proj.crs()

            wkt = qgsgeom.exportToWkt()

            geom = ogr.CreateGeometryFromWkt(wkt)

            # transformation
            if qgscrs.postgisSrid() > 0:

                # Transformation using OGR
                # https://pcjericks.github.io/py-gdalogr-cookbook/projection.html#reproject-a-geometry
                source = osr.SpatialReference()
                source.ImportFromEPSG(self.qgscrs.postgisSrid())

                target = osr.SpatialReference()
                target.ImportFromEPSG(qgscrs.postgisSrid())

                transform = osr.CoordinateTransformation(source, target)
                geom.Transform(transform)

            # conversion
            if self.dlg.cmbConversion.currentText() == 'Envelope':
                geom = self.compute_envelope(geom)
            if self.dlg.cmbConversion.currentText() == 'Centroid':
                geom = geom.Centroid()
            if self.dlg.cmbConversion.currentText() == 'Boundary':
                geom = geom.GetBoundary()
            if self.dlg.cmbConversion.currentText() == 'ConvexHull':
                geom = geom.ConvexHull()

            export = ''
            if self.dlg.cmbFormat.currentText() == 'GML 2':
                export = geom.ExportToGML(options = ['FORMAT=GML2'])
            elif self.dlg.cmbFormat.currentText() == 'GML 3':
                export = geom.ExportToGML(options = ['FORMAT=GML3'])
            elif self.dlg.cmbFormat.currentText() == 'KML':
                export = geom.ExportToKML()
            elif self.dlg.cmbFormat.currentText() == 'GeoJSON':
                export = geom.ExportToJson()
            elif self.dlg.cmbFormat.currentText() == 'EWKT':
                export = ''
                if qgscrs.postgisSrid() > 0:
                    export += "EPSG:"
                    export += str(qgscrs.postgisSrid()) + ";"
                export += geom.ExportToWkt()
            else:
                export = geom.ExportToWkt()
            self.dlg.txtGeometryExport.setText(export)


