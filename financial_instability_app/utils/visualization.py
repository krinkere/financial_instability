from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN


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
