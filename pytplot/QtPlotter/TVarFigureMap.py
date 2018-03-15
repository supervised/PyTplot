import pyqtgraph as pg
import numpy as np
from .. import tplot_utilities 
from pytplot import tplot_opt_glob
import pytplot
from pyqtgraph.Qt import QtCore
from .CustomAxis.BlankAxis import BlankAxis

class TVarFigureMap(pg.GraphicsLayout):
    def __init__(self, tvar, show_xaxis=False, mouse_function=None):
        
        self.tvar=tvar
        self.show_xaxis = show_xaxis
        
        #Sets up the layout of the Tplot Object
        pg.GraphicsLayout.__init__(self)
        self.layout.setHorizontalSpacing(50)
        self.layout.setContentsMargins(0,0,0,0)
        #Set up the x axis
        self.xaxis = pg.AxisItem(orientation='bottom')
        self.xaxis.setHeight(35)
        self.xaxis.enableAutoSIPrefix(enable=False)
        #Set up the y axis
        self.yaxis = pg.AxisItem("left")
        self.yaxis.setWidth(100)
        
        
        self.plotwindow = self.addPlot(row=0, col=0, axisItems={'bottom': self.xaxis, 'left': self.yaxis})
        self.plotwindow.vb.setLimits(xMin=0, xMax=360, yMin=-90, yMax=90)
        
        #Set up the view box needed for the legends
        self.legendvb = pg.ViewBox(enableMouse=False)
        self.legendvb.setMaximumWidth(100)
        self.legendvb.setXRange(0,1, padding=0)
        self.legendvb.setYRange(0,1, padding=0)
        self.addItem(self.legendvb,0,1)       
        
        
        self.curves = []
        self.colors = self._setcolors()
        self.colormap = self._setcolormap()

        if show_xaxis:
            self.plotwindow.showAxis('bottom')
        else:
            self.plotwindow.hideAxis('bottom')
        
        self._mouseMovedFunction = mouse_function


    def buildfigure(self):
        self._setxrange()
        self._setyrange()
        self._setyaxistype()
        self._setzaxistype()
        self._setzrange()
        self._addtimebars()
        self._visdata()
        self._setyaxislabel()
        self._setxaxislabel()
        self._addmouseevents()
        self._addlegend()
    
    def _setyaxislabel(self):
        self.yaxis.setLabel(self.tvar.yaxis_opt['axis_label'])
    
    def _setxaxislabel(self):
        self.xaxis.setLabel("Latitude")
    
    def getfig(self):
        return self
    
    def _visdata(self):    
        datasets = []
        if isinstance(self.tvar.data, list):
            for oplot_name in self.tvar.data:
                datasets.append(pytplot.data_quants[oplot_name])
        else:
            datasets.append(self.tvar)
        
        for dataset in datasets: 
            _, lat = pytplot.get_data(self.tvar.links['lat']) 
            lat = lat.transpose()[0]
            _, lon = pytplot.get_data(self.tvar.links['lon']) 
            lon = lon.transpose()[0]    
            for column_name in dataset.data.columns:
                values = dataset.data[column_name].tolist()
                colors = pytplot.tplot_utilities.get_heatmap_color(color_map=self.colormap, 
                                                                        min_val=self.zmin, 
                                                                        max_val=self.zmax, 
                                                                        values=values, 
                                                                        zscale=self.zscale)
                brushes = []
                for color in colors:
                    brushes.append(pg.mkBrush(color))
                self.curves.append(self.plotwindow.scatterPlot(lon.tolist(), lat.tolist(), 
                                                               pen=pg.mkPen(None), brush=brushes))
        
    def _setyaxistype(self):
        if self._getyaxistype() == 'log':
            self.plotwindow.setLogMode(y=True)
        else:
            self.plotwindow.setLogMode(y=False)
        return
        
    def _addlegend(self):
        zaxis=pg.AxisItem('right')
        
        if 'axis_label' in self.tvar.zaxis_opt:
            zaxis.setLabel(self.tvar.zaxis_opt['axis_label'])
        else:
            zaxis.setLabel(' ')
        
        if self.show_xaxis:
            emptyAxis=BlankAxis('bottom')
            emptyAxis.setHeight(35)
            p2 = self.addPlot(row=0, col=1, axisItems={'right':zaxis, 'bottom':emptyAxis}, enableMenu=False, viewBox=self.legendvb)
        else:
            p2 = self.addPlot(row=0, col=1, axisItems={'right':zaxis}, enableMenu=False, viewBox=self.legendvb)
            p2.hideAxis('bottom')
            
        p2.buttonsHidden=True
        p2.setMaximumWidth(100)
        p2.showAxis('right')
        p2.hideAxis('left')
        colorbar = pg.ImageItem()
        colorbar.setImage(np.array([np.linspace(1,2,200)]).T)
        
        p2.addItem(colorbar)
        p2.setLogMode(y=(self.zscale=='log'))
        p2.setXRange(0,1, padding=0)
        if self.zscale=='log':
            colorbar.setRect(QtCore.QRectF(0,np.log10(self.zmin),1,np.log10(self.zmax)-np.log10(self.zmin)))
            p2.setYRange(np.log10(self.zmin),np.log10(self.zmax), padding=0)
        else:
            colorbar.setRect(QtCore.QRectF(0,self.zmin,1,self.zmax-self.zmin))
            p2.setYRange(self.zmin,self.zmax, padding=0)
        colorbar.setLookupTable(self.colormap)
    
    def _addmouseevents(self):
        return
    
    def _getyaxistype(self):
        return 'linear'
    
    def _setzaxistype(self):
        if self._getzaxistype() == 'log':
            self.zscale = 'log'
        else:
            self.zscale = 'linear'
    
    def _getzaxistype(self):
        if 'z_axis_type' in self.tvar.zaxis_opt:
            return  self.tvar.zaxis_opt['z_axis_type']
        else:
            return 'linear'
            
    def _setcolors(self):
        if 'line_color' in self.tvar.extras:
            return self.tvar.extras['line_color']
        else: 
            return ['k', 'r', 'g', 'c', 'y', 'm', 'b']
    
    def _setcolormap(self):          
        if 'colormap' in self.tvar.extras:
            for cm in self.tvar.extras['colormap']:
                return tplot_utilities.return_lut(cm)
        else:
            return pytplot.tplot_utilities.return_lut("inferno")
    
    def getaxistype(self):
        axis_type = 'lat'
        link_y_axis = True
        return axis_type, link_y_axis
    
    def _setxrange(self):
        #Check if x range is set.  Otherwise, x range is automatic 
        self.plotwindow.setXRange(0,360)
    
    def _setyrange(self):
        self.plotwindow.vb.setYRange(-90, 90)
    
    def _setzrange(self):
        #Get Z Range
        if 'z_range' in self.tvar.zaxis_opt:
            self.zmin = self.tvar.zaxis_opt['z_range'][0]
            self.zmax = self.tvar.zaxis_opt['z_range'][1]
        else:
            dataset_temp = self.tvar.data.replace([np.inf, -np.inf], np.nan)
            self.zmax = dataset_temp.max().max()
            self.zmin = dataset_temp.min().min()
            
            #Cannot have a 0 minimum in a log scale
            if self.zscale=='log':
                zmin_list = []
                for column in self.tvar.data.columns:
                    series = self.tvar.data[column]
                    zmin_list.append(series.iloc[series.nonzero()[0]].min())
                self.zmin = min(zmin_list)
    
    def _addtimebars(self):
        #Not yet implemented
        return