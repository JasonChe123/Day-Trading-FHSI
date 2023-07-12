from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Kline, Grid
from pyecharts.commons.utils import JsCode
import os
import sys
import datetime as dt
import pandas as pd
from pathlib import Path


class CandleStick:
    def __init__(self,
                 project_dir: str,
                 from_: dt.datetime = dt.datetime.strptime('2019-01-01', '%Y-%m-%d'),
                 to_: dt.datetime = dt.datetime.now()):
        """
        Build candlestick
        :param from_: 'yyyy-mm-dd'
        :param to_: 'yyyy-mm-dd'
        """
        # re-define 'from_' and 'to_'
        self.project_dir = project_dir
        from_ = from_.replace(hour=9, minute=15)
        to_ = (to_ + dt.timedelta(days=1)).replace(hour=3, minute=0)

        # read fhsi data
        self.fhsi_data = pd.read_csv(
            os.path.join(self.project_dir, 'database', 'fhsi_m1', 'full_data', 'full_data.csv'),
            index_col=0,
            parse_dates=['Date']
        )

        # build data with 'from_' and 'to_'
        self.fhsi_chart_data = self.fhsi_data[(self.fhsi_data['Date'] >= from_) &
                                              (self.fhsi_data['Date'] <= to_)]
        if self.fhsi_chart_data.empty:
            return

        # start building candlestick
        self.build_candlestick()

    def build_candlestick(self):
        """
        define Grid, Kline and VolumeBar
        :return:
        """
        # remove letter 'T' between 'Date' and 'Time'
        self.fhsi_chart_data = self.fhsi_chart_data.copy()
        self.fhsi_chart_data['Date'] = self.fhsi_chart_data['Date'].apply(lambda value: str(value))

        # declare dataset
        x_axis_data = self.fhsi_chart_data['Date'].tolist()
        candlestick_data = self.fhsi_chart_data[['Open', 'Close', 'Low', "High"]].values.tolist()
        volume_data = self.fhsi_chart_data['Volume'].tolist()

        # declare chart varibels
        title = 'Candlestick - 1 Min'
        self.subcharts = []  # max 3 subcharts suggested

        # grid
        self.chart = Grid(init_opts=opts.InitOpts(width='2500px', height='1200px'))

        # candlestick
        self.kline = Kline()
        xaxis_opts = {
            'xaxis_data': x_axis_data
        }
        yaxis_opts = {
            'series_name': 'Heng Seng Index Futures',
            'y_axis': candlestick_data,
            'itemstyle_opts': opts.ItemStyleOpts(color='green',
                                                 color0='grey',
                                                 border_color='lightgreen',
                                                 border_color0='grey'),
        }
        global_opts = {
            'xaxis_opts': opts.AxisOpts(is_scale=True,
                                        splitline_opts=opts.SplitLineOpts(is_show=True)),
            'yaxis_opts': opts.AxisOpts(is_scale=True,
                                        splitline_opts=opts.SplitLineOpts(is_show=True),),
            'datazoom_opts': [opts.DataZoomOpts(is_show=True,
                                                is_realtime=False,
                                                type_='slider',
                                                xaxis_index=[0, 0],
                                                range_start=0, range_end=0.1),
                              opts.DataZoomOpts(is_show=True,
                                                is_realtime=False,
                                                type_='inside',
                                                xaxis_index=[0, 1],
                                                range_start=0, range_end=0.1),
                              opts.DataZoomOpts(is_show=True,
                                                is_realtime=False,
                                                type_='inside',
                                                xaxis_index=[0, 2],
                                                range_start=0, range_end=0.1),
                              ],
            'title_opts': opts.TitleOpts(title=title,
                                         subtitle='This is a subtitle'),
            'toolbox_opts': opts.ToolboxOpts(is_show=True, orient='horizontal'),
        }
        self.kline.add_xaxis(**xaxis_opts)
        self.kline.add_yaxis(**yaxis_opts)
        self.kline.set_global_opts(**global_opts)
        self.chart.add_js_funcs("var barData = {}".format(candlestick_data))

        # volume bar
        vol_bar = Bar()
        xaxis_opts = {
            'xaxis_data': x_axis_data
        }
        yaxis_opts = {
            'series_name': 'Volume',
            'y_axis': volume_data,
            'label_opts': opts.LabelOpts(is_show=False),
            'itemstyle_opts': opts.ItemStyleOpts(color=JsCode(
                """
                function(params) {
                    var colorList;
                    if (barData[params.dataIndex][1] > barData[params.dataIndex][0]) {
                        colorList = 'green';
                    } else {
                        colorList = 'red';
                    }
                    return colorList;
                }
                """), ),
        }
        global_opts = {
            'xaxis_opts': opts.AxisOpts(grid_index=len(self.subcharts) + 1,
                                        axislabel_opts=opts.LabelOpts(is_show=False)),
        }
        vol_bar.add_xaxis(**xaxis_opts)
        vol_bar.add_yaxis(**yaxis_opts)
        vol_bar.set_global_opts(**global_opts)
        self.subcharts.append(vol_bar)

    def add_trading_line(self, entry: dict | pd.Series, exit_: dict | pd.Series, name: str,
                         comm: int | float, slippage: int | float, point_value: int | float) -> None:
        """
        add connecting line from entry to exit of a trade
        :param entry: position detail: time_key, price, side, qty, remark
        :param exit_: position detail: time_key, price, side, qty, remark
        :param name: strategy name
        :param comm: commission per contract, in point
        :param slippage: slippage per contract in point
        :param point_value: point_value of contract
        :return: None
        """
        # processing data
        xaxis_data = [entry['time_key'], exit_['time_key']]
        yaxis_data = [entry['price'], exit_['price']]
        pnl = (exit_['price'] * min(exit_['qty'], entry['qty']) - entry['price']*entry['qty']) * point_value
        fees_and_comm = (entry['qty'] + exit_['qty'])*comm*slippage*point_value
        pnl -= fees_and_comm
        color = 'red' if pnl <= 0 else 'blue'
        pnl = '(' + '{:+,.0f}'.format(pnl) + ')'  # add parentheses to avoid changing string to int by pyecharts
        markline_data = [{'xAxis': entry['time_key'], 'yAxis': entry['price'], 'value': pnl},
                         {'xAxis': exit_['time_key'], 'yAxis': exit_['price']}, ]

        # setup params
        yaxis_params = {'series_name': name,
                        'is_connect_nones': False,
                        'linestyle_opts': opts.LineStyleOpts(width=2, type_='dashed', color=color),
                        'label_opts': opts.LabelOpts(is_show=True),
                        'markpoint_opts': opts.MarkPointOpts(
                            symbol_size=50,
                            symbol='pin',
                            label_opts=opts.LabelOpts(color='black'),
                            data=[opts.MarkPointItem(coord=[entry['time_key'], entry['price']],
                                                     value=f"{entry['remark']}\n{entry['qty']}",
                                                     name=entry['price'],
                                                     itemstyle_opts=opts.ItemStyleOpts(color='blue', opacity=0.5),
                                                     ),
                                  opts.MarkPointItem(coord=[exit_['time_key'], exit_['price']],
                                                     value=f"{exit_['remark']}\n{exit_['qty']}",
                                                     name=exit_['price'],
                                                     itemstyle_opts=opts.ItemStyleOpts(color='red', opacity=0.5),
                                                     )
                                  ]),
                        'markline_opts': opts.MarkLineOpts(
                            label_opts=opts.LabelOpts(position='middle', color=color, font_size=15),
                            symbol=['circle', 'arrow'],
                            linestyle_opts=opts.LineStyleOpts(width=2, type_='dashed', color=color),
                            data=[markline_data]),
                        }

        # add line
        line_chart = Line()
        line_chart.add_xaxis(xaxis_data=xaxis_data)
        line_chart.add_yaxis(y_axis=yaxis_data, **yaxis_params)
        self.kline.overlap(line_chart)

    def add_ta(self, x_data, y_data, name: str, width: int, type_: str, color: str, is_subchart: bool = False):
        """
        add indicator to the chart
        :param x_data: x-axis data
        :param y_data: y-axis data
        :param name: name of TA
        :param width: line width
        :param type_: line type: solid/ dot/...
        :param color: line color
        :param is_subchart: if True, it shows in separated chart
        :return: None
        """
        # common yaxis_params
        yaxis_params = {'series_name': name,
                        'y_axis': y_data,
                        'is_symbol_show': False,
                        'linestyle_opts': opts.LineStyleOpts(width=width, type_=type_, color=color),
                        'label_opts': opts.LabelOpts(is_show=False),
                        'is_connect_nones': True,
                        }

        # add line
        ta_line = Line()
        ta_line.add_xaxis(xaxis_data=x_data)
        if is_subchart:
            # separated chart
            yaxis_params['symbol_size'] = 2
            global_opts = {'xaxis_opts': opts.AxisOpts(grid_index=len(self.subcharts) + 1,
                                                       axislabel_opts=opts.LabelOpts(is_show=False))}
            ta_line.add_yaxis(**yaxis_params)
            ta_line.set_global_opts(**global_opts)
            self.subcharts.append(ta_line)
        else:
            # overlap kline
            ta_line.add_yaxis(**yaxis_params)
            self.kline.overlap(ta_line)

    def export_chart(self, file_name: str = ''):
        # calculate position and size
        spacing = 5
        legend_height = 5
        subchart_bottom = legend_height
        subchart_height = 15
        kline_bottom = subchart_bottom + len(self.subcharts)*(subchart_height + spacing + legend_height)
        kline_height = 100 - legend_height - kline_bottom

        # add subcharts
        self.chart.add(chart=self.kline, grid_opts=opts.GridOpts(pos_bottom=f'{kline_bottom}%', height=f'{kline_height}%'))
        for subchart in self.subcharts:
            subchart.set_global_opts(legend_opts=opts.LegendOpts(pos_left='center', pos_bottom=f'{subchart_bottom + legend_height*0.5}%'))
            self.chart.add(chart=subchart, grid_opts=opts.GridOpts(pos_bottom=f'{subchart_bottom + legend_height}%', height=f'{subchart_height}%'))
            subchart_bottom += legend_height + subchart_height

        # render
        self.chart.render(os.path.join(self.project_dir, 'backtesting', 'report', file_name))

    def get_chart_data(self):
        return self.fhsi_chart_data.copy()


class LineChart:
    def __init__(self, x_data: list, y_data: list, title: str, sub_title: str):
        # self.line = Line(init_opts=opts.InitOpts(width='2500px', height='1200px'))
        self.line = Line()
        self.line.add_xaxis(xaxis_data=x_data)
        self.title = title
        self.sub_title = sub_title
        new_high_dots_otps = self.get_new_high_dot(x_data, y_data)
        self.line.add_yaxis(series_name='MAL', y_axis=y_data, is_connect_nones=True,
                            linestyle_opts=opts.LineStyleOpts(width=2), **new_high_dots_otps)

    def add_drawdown(self, x_data: list, y_data: list, name: str):
        dd_line = Line()
        dd_line.add_xaxis(xaxis_data=x_data)
        dd_line.add_yaxis(series_name=name, y_axis=y_data, is_connect_nones=True,
                          linestyle_opts=opts.LineStyleOpts(width=2, color='red'))
        dd_line.set_series_opts(areastyle_opts=opts.AreaStyleOpts(opacity=0.5, color='red'))
        self.line.overlap(dd_line)

    def get_new_high_dot(self, x_data: list, y_data: list) -> dict:
        # plot dot at new high on equity curve
        all_time_high_data = []
        recovery = []
        recovery_time = []
        new_high = 0
        options = opts.ItemStyleOpts(color='lightgreen', opacity=1)
        for x, y in zip(x_data, y_data):
            if y > new_high:
                all_time_high_data.append(opts.MarkPointItem(coord=[x, y], itemstyle_opts=options))
                recovery.append(x)
                if len(recovery) > 1:
                    new_time = dt.datetime.strptime(recovery[-1], '%Y-%m-%d %H:%M:%S')
                    last_time = dt.datetime.strptime(recovery[-2], '%Y-%m-%d %H:%M:%S')
                    recovery_time.append([new_time - last_time, last_time, new_time])
                new_high = y

        new_high_dots = {'markpoint_opts': opts.MarkPointOpts(
            symbol_size=10,
            symbol='circle',
            data=all_time_high_data,
            label_opts=opts.LabelOpts(is_show=False)
        )}
        if len(recovery_time) > 1:
            self.recovery_time = max(recovery_time)[0].days
            self.recovery_from = max(recovery_time)[1]
            self.recovery_to = max(recovery_time)[2]
        elif len(recovery_time) == 1:
            self.recovery_time = recovery_time[0][0].days
            self.recovery_from = recovery_time[0][1]
            self.recovery_to = recovery_time[0][2]
        else:
            self.recovery_time = 0
            self.recovery_from = 0
            self.recovery_to = 0

        return new_high_dots

    def add_monthly_report(self, monthly_df: pd.DataFrame):
        self.sub_title += f"\n{'-'*60}\n{monthly_df.to_string()}"
        # self.sub_title += '\n\n' + '-'*60 + monthly_df.to_string()

    def add_yearly_report(self, yearly_df: pd.DataFrame):
        self.sub_title += f"\n{'-' * 60}\n{yearly_df.to_string()}"

    def add_overview_text(self, overview_df: pd.DataFrame):
        self.sub_title += f"\n{'-' * 60}\n{overview_df.to_string()}"

    def export_chart(self, path: os.path):
        global_opts = {
            'xaxis_opts': opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=False)),
            'yaxis_opts': opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True)),
            'datazoom_opts': [opts.DataZoomOpts(type_='slider', range_start=0, range_end=100),
                              opts.DataZoomOpts(type_='inside', range_start=0, range_end=100)],
            'toolbox_opts': opts.ToolboxOpts(is_show=True, orient='horizontal'),
            'title_opts': opts.TitleOpts(title=self.title, subtitle=self.sub_title,
                                         subtitle_textstyle_opts=opts.TextStyleOpts(font_family='Ubuntu Mono',
                                                                                    font_size=14)),
        }
        self.line.set_global_opts(**global_opts)
        grid = Grid(init_opts=opts.InitOpts(width='2500px', height='1200px'))
        grid.add(self.line, grid_opts=opts.GridOpts(pos_left='20%'))
        grid.render(path)
