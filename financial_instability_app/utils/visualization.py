from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
import matplotlib.pyplot as plt
import stock_utils
from colorsys import hsv_to_rgb
import random


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


def generate_single_line_plot(df, ticker):
    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3
    p.line(df.index, df['AdjClose_'+ticker], line_width=2)

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


def generate_multi_line_plot(df, tickers):
    area_colors = get_colors(len(tickers))
    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha = 0.3
    for (color, ticker) in zip(area_colors, tickers):
        p.line(df.index, df[ticker], line_width=2, legend=ticker, color=color)

    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return generated_script, div_tag, cdn_js, cdn_css


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


