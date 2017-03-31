from bokeh.plotting import figure
from bokeh.io import vplot
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.charts import Histogram, Bar
from bokeh.models import Span
import matplotlib.pyplot as plt
import stock_utils
from colorsys import hsv_to_rgb
import random
from bokeh.models import LinearColorMapper, ColumnDataSource, HoverTool
from math import pi
from progressbar import ProgressBar
import time


def generate_candlestick_plot(df, ticker):
    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3

    hours_12 = 12 * 60 * 60 * 1000
    p.rect(df.index[df['Status_'+ticker] == 'Increase'], df['Middle_'+ticker][df['Status_'+ticker] == 'Increase'],
           hours_12, df['Height_'+ticker][df['Status_'+ticker] == 'Increase'], fill_color='green', line_color='black')
    p.rect(df.index[df['Status_'+ticker] == 'Decrease'], df['Middle_'+ticker][df['Status_'+ticker] == 'Decrease'],
           hours_12, df['Height_'+ticker][df['Status_'+ticker] == 'Decrease'], fill_color='red', line_color='black')
    p.segment(df.index, df['High_'+ticker], df.index, df['Low_'+ticker], color='Black')

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_volume_bar_plot(df, ticker):
    df /= 1000000
    df = df.resample('M').sum()
    # Bar chart doesn't accept `Timestamp` for x-axis categories.
    # https://github.com/bokeh/bokeh/issues/3847
    df.index.name = 'DATE'
    df = df.reset_index()
    df.DATE = df.DATE.apply(lambda x: str(x).split(' 00:00:00')[0])
    column = "Volume_" + ticker
    p = Bar(df, values=column, label='DATE', xlabel='', ylabel='Volume (in millions)', legend=False)

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_adj_close_histo_plot(df, ticker):
    # little hack here since Bokeh seems to get weird if numbers are too small...
    column = "AdjClose_" + ticker
    df *= 100
    p = Histogram(df, values=column, bins=10)

    mean = df[column].mean()
    std = df[column].std()

    mean_line = Span(location=mean, dimension='height', line_color='black', line_width=3)
    std_line_left = Span(location=-std, dimension='height', line_color='blue', line_dash="dashed", line_width=3)
    std_line_right = Span(location=std, dimension='height', line_color='blue', line_dash="dashed", line_width=3)

    p.renderers.extend([mean_line, std_line_left, std_line_right])

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css, mean/100, std/100


def generate_single_line_plot(df, column, ticker):
    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3
    p.line(df.index, df[column], line_width=2)

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_multi_line_plot(df, tickers, labels):
    area_colors = get_colors(len(tickers))
    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3
    for (color, ticker, label) in zip(area_colors, tickers, labels):
        p.line(df.index, df[ticker], line_width=2, legend=label, color=color)

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_heatline_graph(df_corr, heatmap_tickers, ticker):
    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    mapper = LinearColorMapper(palette=list(reversed(colors)))

    ticker_y_axis = []
    ticker_x_axis = []
    rate = []

    for ticker_x in heatmap_tickers:
        ticker_y = ticker
        ticker_x_axis.append(ticker_x)
        ticker_y_axis.append(ticker_y)
        pearson_corr = df_corr[ticker_y][ticker_x]
        rate.append(pearson_corr)

    source = ColumnDataSource(
        data=dict(ticker_x=ticker_x_axis, ticker_y=ticker_y_axis, rate=rate)
    )

    tools = 'hover'

    # Remove first ticker from the list...
    p = figure(x_range=heatmap_tickers[1:], y_range=[ticker], x_axis_location="above",
               plot_width=1200, plot_height=110, tools=tools)
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "5pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = pi / 3

    p.rect(x="ticker_x", y="ticker_y", width=1, height=1,
           source=source,
           fill_color={'field': 'rate', 'transform': mapper},
           line_color=None)

    p.select_one(HoverTool).tooltips = [
        ('stocks', '@ticker_x'),
        ('corr', '@rate'),
    ]

    return p


def generate_heatline(df_corr, heatmap_tickers, ticker):
    # this assumes that we are using it for S&P 500 that has around 500 tickers
    print heatmap_tickers
    p0_50 = generate_heatline_graph(df_corr, heatmap_tickers[0:50], ticker)
    p50_100 = generate_heatline_graph(df_corr, heatmap_tickers[50:100], ticker)
    p100_150 = generate_heatline_graph(df_corr, heatmap_tickers[100:150], ticker)
    p150_200 = generate_heatline_graph(df_corr, heatmap_tickers[150:200], ticker)
    p200_250 = generate_heatline_graph(df_corr, heatmap_tickers[200:250], ticker)
    p250_300 = generate_heatline_graph(df_corr, heatmap_tickers[250:300], ticker)
    p300_350 = generate_heatline_graph(df_corr, heatmap_tickers[300:350], ticker)
    p350_400 = generate_heatline_graph(df_corr, heatmap_tickers[350:400], ticker)
    p400_450 = generate_heatline_graph(df_corr, heatmap_tickers[400:450], ticker)
    p450 = generate_heatline_graph(df_corr, heatmap_tickers[450:], ticker)

    megaplot = vplot(p0_50, p50_100, p100_150, p150_200, p200_250, p250_300, p300_350, p350_400, p400_450, p450)

    generated_script, div_tag = components(megaplot)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_heatmap(df_corr, heatmap_tickers):
    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    mapper = LinearColorMapper(palette=list(reversed(colors)))

    ticker_y_axis = []
    ticker_x_axis = []
    rate = []

    pb = ProgressBar()

    start_time = time.time()
    for ticker_y in pb(heatmap_tickers):
        for ticker_x in heatmap_tickers:
            ticker_y_axis.append(ticker_y)
            ticker_x_axis.append(ticker_x)
            pearson_corr = df_corr[ticker_x][ticker_y]
            rate.append(pearson_corr)
    print("--- ran in %s seconds ---" % (time.time() - start_time))

    source = ColumnDataSource(
        data=dict(ticker_x=ticker_x_axis, ticker_y=ticker_y_axis, rate=rate)
    )

    tools = "hover,save,wheel_zoom,box_zoom,reset"

    p = figure(x_range=heatmap_tickers, y_range=list(reversed(heatmap_tickers)), x_axis_location="above",
               plot_width=1200, plot_height=600, tools=tools)
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "5pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = pi / 3

    p.rect(x="ticker_x", y="ticker_y", width=1, height=1,
           source=source,
           fill_color={'field': 'rate', 'transform': mapper},
           line_color=None)

    p.select_one(HoverTool).tooltips = [
        ('stocks', '@ticker_x - @ticker_y'),
        ('corr', '@rate'),
    ]

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_corr_plot(df, tickers):
    ticker1 = tickers[0]
    ticker2 = tickers[1]
    p = figure(x_axis_label=ticker1, y_axis_label=ticker2, width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3
    p.circle(df[ticker1], df[ticker2], size=5, alpha=0.5)

    beta, alpha = stock_utils.find_beta_alpha(df, ticker1, ticker2)
    pearson_corr = stock_utils.calculate_correlation(df, ticker1, ticker2)

    p.line(df[ticker1], beta*df[ticker1]+alpha, line_width=2, color='red')

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css, pearson_corr, ticker2


def generate_bollinger_plot(df, ticker):
    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3
    # draw adj close price plot
    p.line(df.index, df["AdjClose_"+ticker], line_width=2, legend=ticker, color='black')
    # draw rolling mean plot
    p.line(df.index, df["rolling_mean"], line_width=2, legend='Rolling Mean', color='blue')
    # draw upper bollinger plot
    p.line(df.index, df["upper_band"], line_width=2, legend='Upper Band', color='red')
    # draw lowe bollinger plot
    p.line(df.index, df["lower_band"], line_width=2, legend='Lower Band', color='red')

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def plot_stock_analysis(adj_close_data):
    normalized_data = stock_utils.normalize_data(adj_close_data)
    daily_returns = stock_utils.calculate_daily_returns(adj_close_data)
    cum_returns = stock_utils.calculate_cumulative_returns_from_daily(daily_returns)

    fig, axes = plt.subplots(nrows=4, ncols=1)
    fig.subplots_adjust(hspace=2)
    adj_close_data.plot(ax=axes[0], title="Adjusted Close", grid=True)
    normalized_data.plot(ax=axes[1], title="Normalized Stock Information", grid=True)
    daily_returns.plot(ax=axes[2], title="Daily Returns", grid=True)
    cum_returns.plot(ax=axes[3], title="Cumulative Returns", grid=True)
    # plt.show()

    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)  # rewind to beginning of file
    figdata_png = figfile.getvalue()  # extract string (stream of bytes)

    import base64
    figdata_png = base64.b64encode(figdata_png)
    return figdata_png


def get_colors(size):
    if size > 15:
        area_colors = [gen_color(random.random()) for i in range(size)]
        return area_colors
    else:
        basic_colors = ['black', 'blue', 'red', 'green', 'yellow', 'fuchsia', 'gray', 'maroon', 'teal', 'navy', 'lime',
                        'silver', 'olive', 'aqua', 'purple']
        return basic_colors[:size]


def gen_color(h):
    # Reference: https://www.continuum.io/blog/developer-blog/drawing-brain-bokeh
    golden_ratio = (1 + 5 ** 0.5) / 2
    h += golden_ratio
    h %= 1
    return '#%02x%02x%02x' % tuple(int(a*100) for a in hsv_to_rgb(h, 0.55, 2.3))


