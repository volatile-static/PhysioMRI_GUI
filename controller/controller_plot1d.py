"""
@author:    José Miguel Algarín
@email:     josalggui@i3m.upv.es
@affiliation:MRILab, i3M, CSIC, Valencia, Spain
"""
import numpy as np

from widgets.widget_plot1d import Plot1DWidget


class Plot1DController(Plot1DWidget):
    def __init__(self,
                 x_data,  # numpy array
                 y_data,  # list of numpy array
                 legend,  # list of strings
                 x_label,  # string
                 y_label,  # string
                 title,  # string
                 ):
        super(Plot1DController, self).__init__()
        self.y_data = y_data
        self.x_data = x_data
        self.x_label = x_label
        self.y_label = y_label
        self.title = title

        # Set text
        self.label2.setText("<span style='font-size: 8pt'>%s=%0.2f, %s=%0.2f</span>" % (x_label, 0, y_label, 0))

        # Add lines to plot_item
        n_lines = len(y_data)
        self.lines = []
        for line in range(n_lines):
            if type(x_data) is list:
                x = x_data[line]
            else:
                x = x_data.copy()
            y = y_data[line]
            self.lines.append(self.plot_item.plot(x, y, pen=self.pen[line], name=legend[line]))
            self.plot_item.setXRange(x[0], x[-1], padding=0)
            if np.min(y) == np.max(y):
                self.plot_item.setYRange(-1, 1, padding=0)

        # Set the plot properties
        self.plot_item.setTitle("%s" % title)
        self.plot_item.setLabel('bottom', x_label)
        self.plot_item.setLabel('left', y_label)

    def mouseMoved(self, evt):
        pos = evt[0]
        if self.plot_item.sceneBoundingRect().contains(pos):
            if type(self.x_data) is not list:
                curves = self.plot_item.listDataItems()
                x, y = curves[0].getData()
                mouse_point = self.plot_item.vb.mapSceneToView(pos)
                index = np.argmin(np.abs(self.x_data - mouse_point.x()))
                self.label2.setText("<span style='font-size: 8pt'>%s=%0.2f, %s=%0.2f</span>" % (self.x_label,
                                                                                                x[index],
                                                                                                self.y_label,
                                                                                                y[index]))
                self.crosshair_v.setPos(x[index])
                self.crosshair_h.setPos(y[index])
            else:
                mouse_point = self.plot_item.vb.mapSceneToView(pos)
                self.label2.setText("x = %0.4f, y = %0.4f" % (mouse_point.x(), mouse_point.y()))
                self.crosshair_v.setPos(mouse_point.x())
                self.crosshair_h.setPos(mouse_point.y())