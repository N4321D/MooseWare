"""
Graph plotting widget for kivy

Set graph.xd and graph.yd, then call graph.plot() to draw data

Graph.scale can be used to scale the graph
Y can be 2dim  numpy array in that case, every column will be treated
as new plot in the same graph

Vars needed are:
MO = (r,g,b,a)   # Color of line,
GRAPH_BACKGROUND  # BG Color
GRAPH_AX,       # ax color

[BLUE, GREEN_BRIGHT, YELLOW, WHITE] # standard color palette but can be
changed in graph.settings

kv:
<Graph@RelativeLayout>:

at screen section:
    Graph1:
        id: graf1
        size_hint: 0.6,0.38
        pos_hint: {'x': 0.07, 'top': 0.88}
        skipnan: False
        show_last_value: True
        
"""

# logger
try:
    from subs.log import create_logger
except:

    def create_logger():
        class Logger:
            def __init__(self) -> None:
                f = lambda *x: print(
                    "GRAPH WIDGET: ", *x
                )  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f

        return Logger()


logger = create_logger()


def log(message, level="info"):
    getattr(logger, level)(
        "GRAPH WIDGET: {}".format(message)
    )  # change RECORDER SAVER IN CLASS NAME


# IMPORTS
from kivy.graphics import Line, Color, Rectangle, InstructionGroup
from kivy.uix.label import Label

# from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.lang.builder import Builder


import numpy as np
import time

# import global vars with colors, see description:
try:
    from subs.gui.vars import *

except Exception as e:
    log("Vars import error, loading defaults: {}".format(e), "warning")
    MO = (0, 1, 0.1, 1)  # Color of line,
    GRAPH_BACKGROUND = (0, 0, 0, 1)  # BG Color
    GRAPH_AX = (0, 0.5, 1, 1)  # ax color
    BLUE = (0, 0, 1, 1)
    GREEN_BRIGHT = (0, 1, 0, 1)
    YELLOW = (1, 1, 0, 1)
    WHITE = (1, 1, 1, 1)
    GREY = (0.5, 0.5, 0.5, 0.5)

kv_str = """
# X Label
<GrAx_X_Lbl>:
    color: MO
    font_size: '10sp'
    halign: 'center'
    valign: 'top'

# Y Label
<GrAx_Y_Lbl>:
    color: MO
    font_size: '10sp'
    halign: 'right'
    valign: 'middle'

    
# Last Value
<Last_Val_Label>:
    color: MO
    text_size: self.size
    background_color: GREY
    font_size: '12sp'
    halign: 'right'
    valign: 'top'

"""


class GrAx_X_Lbl(Label):
    pass


class GrAx_Y_Lbl(Label):
    pass

class Last_Val_Label(Label):
    pass

class Graph(FloatLayout):
    """
    NOTES
    """

    utc = False  #                     # indicate if time should be in utc or localtime

    def __init__(self, **kwargs):
        Builder.load_string(kv_str)
        super(Graph, self).__init__(**kwargs)

        # VARS:
        self.steps = 6  # number of ticks on x and y axis
        self.skipnan = True  # skip nans when plotting
        self.x_lbl = []  # list of x labels
        self.y_lbl = []  # list of y labels
        self.lines = []  # list with lines
        self.yzoom = 0
        self.show_last_value = False

        # update background and axes size with changes in size and pos:
        self.bind(pos=self.update_back)
        self.bind(size=self.update_back)
        self.bind(pos=self.update_ax)
        self.bind(size=self.update_ax)
        self.bind(size=self.drawData)  # redraw when window changes
        self.bind(pos=self.drawData)  # redraw when window changes

        # VARS
        # set scale of x and y axes
        self.scale = {"minx": None, "maxx": None, "miny": None, "maxy": None}
        self.plot_data = (
            None  # np struct array with plot data, first dim is x next are y(s)
        )
        # default settings
        self.settings = {
            "linecolor": MO,  # Color of line,
            "backgroundcolor": GRAPH_BACKGROUND,  # BG Color
            "axcolor": GRAPH_AX,  # ax color
            # color palette:
            "palette": [BLUE, GREEN_BRIGHT, YELLOW, WHITE],
        }
        # actual settings
        self.sett = self.settings.copy()

        # create canvas
        with self.canvas.before:
            Color(*self.sett["backgroundcolor"])
            self.rect = Rectangle(pos=self.pos, size=self.size)
            Color(*self.sett["axcolor"])
            self.ax = Line(points=[1, 1, 1, 1])

        # add widgets
        self.last_y_label = None 


    def plot(self, data, *args, yzoom=0, **kwargs):
        """
        This is called (externally) to plot the prepared data
        This is basically where the plot procedure starts
        - data: np.recarray / np.strucarray with at least x(1st par),
                and y(2nd - nth par) data data to plot
        - zoom: zoom factor, if zoom == 0 data is scaled to min and max
        """
        if self.show_last_value:
            self.toggle_last_y_label()

        self.plot_data = data
        self.yzoom = yzoom
        self.sett = self.settings.copy()
        self.sett.update(kwargs)
        return self.drawData()

    def plot_xy(self, x, y, yzoom=0, *args, **kwargs):
        """
        Plot data from x and y coordinates as line plot.

        Parameters:
        -----------
        x: array_like
            1-dimensional array or list of x coordinates.
        y: array_like
            1-dimensional array or list of y coordinates.
        zoom: float
            zoom factor, if zoom == 0 data is scaled to min and max

        **kwargs: dict
            Variable-length keyword argument list, used to pass optional
            arguments to the underlying plotting function.

        Raises:
        -------
        AssertionError: If length of x and y arrays are not equal.
        """
        assert len(x) == len(y)

        dtype = [("x", type(x[0])), ("y", type(y[0]))]
        self.plot_data = np.empty(len(x), dtype=dtype)
        self.plot_data["x"], self.plot_data["y"] = x, y
        self.plot(self.plot_data, yzoom=yzoom, **kwargs)

    def update_back(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_ax(self, *args):
        self.ax.points = [
            self.pos[0],
            (self.pos[1] + self.size[1]),
            self.pos[0],
            self.pos[1],
            (self.pos[0] + self.size[0]),
            self.pos[1],
        ]

    def prepareData(self, data, dim, min_dat=None, max_dat=None):
        """
        Removes NaNs, prepares the data
        (coverts it to canvas coordinates)
        and returns the scaling for the axis
        """
        # clamp to min or max (if out of plot range):
        if min_dat is None:
            min_dat = np.nanmin(data)
        else:
            # clip
            data[data < min_dat] = min_dat

        if max_dat is None:
            max_dat = np.nanmax(data)
        else:
            # clip:
            data[data > max_dat] = max_dat

        # correct values for canvas size
        if min_dat == max_dat:  # if data is a straight line
            data.fill(dim[0] + 0.5 * dim[1])

        else:
            data = dim[0] + ((data - min_dat) * (dim[1] / abs(max_dat - min_dat)))

        return data, (min_dat, max_dat)

    def combine_xy_data(self, x, y):
        """
        combine x and y data in to list with [x0, y0, x1, y1,.... xn, yn]
        """
        plotdata = np.empty(x.size + y.size)
        plotdata[0::2], plotdata[1::2] = x, y
        return plotdata.tolist()  # kivy only accepts list

    def do_y_zoom(self):
        """
        Zoom y, sets self.scale to updated values

        """
        zoom = self.yzoom
        scale = (None, None)
        if zoom > 0:
            # set scale
            data = self.plot_data[self.plot_data.dtype.names[1]]
            low, mid, high = np.nanpercentile(
                data, (5, 50, 95), method="linear"
            )  # was lower, linear would be better for ourliers but slower
            l_range = (mid - low) / zoom
            h_range = (high - mid) / zoom
            scale = (mid - l_range, mid + h_range)

        self.scale["miny"], self.scale["maxy"] = scale

    def drawData(self, *args):
        """
        draw data in graph when plot is launched

        # TODO: clean up, this method is very hard to understand,
        clean up and remove unnescessary steps
        """

        if not isinstance(self.plot_data, np.ndarray) or self.plot_data.size == 0:
            # No data to plot
            return

        dim = (self.pos[0], self.size[0], self.pos[1], self.size[1])

        pal = [self.sett["linecolor"], *self.sett["palette"]]

        minmax = [None, None, None, None]

        # zoom if needed
        self.do_y_zoom()

        for i, par_name in enumerate(self.plot_data.dtype.names):
            if i == 0:
                # get x data
                x = self.plot_data[par_name]
                x, minmax[:2] = self.prepareData(
                    x, dim[:2], min_dat=self.scale["minx"], max_dat=self.scale["maxx"]
                )

                continue  # only extract x but do not make traces yet

            else:
                # get y data
                y = self.plot_data[par_name].astype("f4")

                # save last value for ploting
                if i == 1 and self.last_y_label:
                    self.last_y_label.text = f"{y[-1]:.3f}"

                y, minmax[2:] = self.prepareData(
                    y, dim[2:], min_dat=self.scale["miny"], max_dat=self.scale["maxy"]
                )
                if i == 1:
                    self.scale = {
                        k: v for k, v in zip(("minx", "maxx", "miny", "maxy"), minmax)
                    }  # save minmax

            # remove NaNs and excess data
            mask = ...
            if self.skipnan:
                if np.isnan(np.dot(x, x) * np.dot(y, y)):
                    mask = np.isfinite(x) & np.isfinite(y)

            # step size to step through data
            step = int(x[mask].size / dim[1]) or 1

            pdat = self.combine_xy_data(x[mask][::step], y[mask][::step])

            # draw line, update if not existent
            if (i - 1) >= len(self.lines):
                plot_obj = InstructionGroup()
                # set color (Reiterate pal if at end):
                plot_obj.add(Color(*pal[i - 1 % len(pal)]))
                plot_obj.add(Line(points=pdat, group="line"))
                self.lines.append(plot_obj)
                self.canvas.add(plot_obj)
            else:
                self.lines[i - 1].get_group("line")[-1].points = pdat

        # del remaining lines:
        while (i - 1) < len(self.lines) - 1:
            self.canvas.remove(self.lines.pop(-1))

        minx, maxx = self.scale["minx"], self.scale["maxx"]
        miny, maxy = self.scale["miny"], self.scale["maxy"]
        for key in self.scale:  # Clear scale:
            self.scale[key] = None

        # create axes labels
        if self.utc is True:
            t_off = 0
        else:
            t_off = time.localtime().tm_gmtoff  # time zone offset

        n_labels = self.steps + 1

        xlist = np.linspace(minx + t_off, maxx + t_off, n_labels, dtype="datetime64[s]")

        y_list = [miny + ((maxy - miny) / self.steps) * i for i in range(n_labels)]

        for i_label in range(n_labels):
            # X LABELS:
            if len(self.x_lbl) <= i_label:
                # create x label
                self.x_lbl.append(
                    GrAx_X_Lbl(
                        size_hint=(1 / self.steps, 0.04),
                        pos_hint={
                            "x": i_label / self.steps - (0.05 * (10 / self.steps)),
                            "y": -0.09,
                        },
                    )
                )
                self.add_widget(self.x_lbl[-1])

            # update x label
            self.x_lbl[i_label].text = str(xlist[i_label])[-8:]
            self.x_lbl[i_label].size = self.x_lbl[i_label].texture_size

            # Y LABELS:
            if len(self.y_lbl) <= i_label:
                # create y label
                self.y_lbl.append(
                    GrAx_Y_Lbl(
                        size_hint=(0.04, 1 / self.steps),
                        pos_hint={
                            "x": -0.07,
                            "y": 0.97 * (i_label / self.steps)
                            - (0.03 * (10 / self.steps)),
                        },
                    )
                )
                self.add_widget(self.y_lbl[-1])

            # update y label
            self.y_lbl[i_label].text = f"{y_list[i_label]:.2f}"
            self.y_lbl[i_label].size = self.y_lbl[i_label].texture_size
    
    def toggle_last_y_label(self, *args):
        if self.last_y_label is None:
            self.last_y_label = Last_Val_Label(text='last Y',
                                                size_hint=(0.1, 0.1),
                                                pos_hint={'x': 0.89, 'y':0.9},
                                                halign='right',
                                                valign='top',
                                                markup=True,
                                                max_lines=1,
                                                )
            self.last_y_label.text_size = self.last_y_label.size
   
            self.add_widget(self.last_y_label)

            


if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.clock import Clock

    Builder.load_string(
        """
<Scr>:
    orientation: 'vertical'
    Label:
        size_hint: (0.3, 0.1)
        text: "plots random new data every 2 seconds or when button is pressed"
        pos_hint: {'right': 0.6, 'top': 0.9}

    Graph:
        id: graf1
        size_hint: 0.7, 0.5
        pos_hint: {'right': 0.9, 'top': 0.8}

    Button:
        text: 'Plot Random New Data'
        size_hint_y: None
        height: '48dp'
        on_press: root.gr_data()
    """
    )

    class Scr(FloatLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            Clock.schedule_interval(self.gr_data, 2)
            self.gr_data()

        def gr_data(self, *args, **kwargs):
            t = time.time()
            n = 100
            data = np.empty(
                n, dtype=[("time", "f8")] + [(str(i), "f4") for i in range(5)]
            )
            f = np.random.choice(
                [
                    lambda i, *x: (1 / i) * np.linspace(*x),
                    lambda i, *x: i * (np.geomspace(*x)),
                    lambda i, *x: np.random.randint(*x) / np.sqrt(i),
                    lambda i, *x: np.cos(np.sin(0.1 * i * np.linspace(*x))),
                ]
            )
            for i, par in enumerate(data.dtype.names):
                if par == "time":
                    data[par][:] = np.linspace(t, t + n, n)
                else:
                    data[par][:] = f(i, 1, 100, n)

            self.ids.graf1.plot_data = data
            self.ids.graf1.plot(data)

    class MyApp(App):
        def build(self):
            return Scr()

    app = MyApp()
    app.run()
