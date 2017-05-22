from flask import render_template, session, redirect, url_for, flash, request
from . import main
from .forms import TickerForm, CheckMediaForm
from .. import db
from ..models import Ticker, Sector, Portfolio
from ..utils import retrieve_stock_info
from ..utils import visualization
from ..utils import stock_utils
from ..utils import utils
from ..utils import df_utils
from ..utils import ml
import datetime


# Define routes
@main.route('/', methods=['GET', 'POST'])
def index():
    from urllib import urlopen
    from lxml.html import parse

    def get_sector(ticker):
        tree = parse(urlopen('http://www.google.com/finance?&q=NASDAQ%3A' + ticker))
        try:
            # Here I am going to assume that if we can't get sector, then it is invalid ticker
            sect = tree.xpath("//a[@id='sector']")[0].text, tree.xpath("//a[@id='sector']")[0].getnext().text
        except IndexError:
            sect = None, None
        return sect

    form = TickerForm()
    if form.validate_on_submit():
        # ticker_symbol = Ticker.query.filter_by(ticker_symbol=form.ticker_symbol.data)
        if ticker_symbol is None:
            sector_name, industry_name = get_sector(form.ticker_symbol.data)
            if sector_name is None:
                flash("Invalid ticker [ %s ]" % form.ticker_symbol.data, "danger")
                return redirect(url_for('main.index'))
            sector = Sector.query.filter_by(sector=sector_name, industry=industry_name).first()
            if sector is None:
                sector = Sector(sector=sector_name, industry=industry_name)
                db.session.add(sector)
            ticker = Ticker(ticker_symbol=form.ticker_symbol.data, sector=sector)

            db.session.add(ticker)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session["ticker_symbol"] = form.ticker_symbol.data
        session["start_date"] = form.start.data
        session["end_date"] = form.end.data
        flash("Data is being retrieved for %s" % form.ticker_symbol.data, "success")
        return redirect(url_for('main.index'))
    return render_template("index.html", form=form, ticker=session.get("ticker_symbol"),
                           current_time=datetime.datetime.utcnow(), known=session.get('known', False))


@main.route('/corr', methods=['GET'])
@utils.log_time("corr")
def corr():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df, tickers = retrieve_stock_info.get_us_comparison_data(ticker, start, end)
    daily_returns = stock_utils.calculate_daily_returns(df)

    generated_script, div_tag, cdn_js, cdn_css, pearson_corr, comp_ticket \
        = visualization.generate_corr_plot(daily_returns, tickers)

    return render_template("corr.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css, pearson_corr=pearson_corr, comp_ticket=comp_ticket)


@main.route('/heatmap', methods=['GET'])
def heatmap():
    heatmap_tickers = retrieve_stock_info.retrieve_sp500_tickers()
    ticker, start, end = utils.get_ticker_start_date_end_date(session)

    df, valid_tickers = retrieve_stock_info.get_sp500_data(tickers=heatmap_tickers, start=start, end=end)

    if ticker not in valid_tickers:
        print "%s is not present. adding..." % ticker
        df_ticker = retrieve_stock_info.get_adj_close_data(ticker=ticker, start=start, end=end)
        df = df_utils.join_dataframes(df, df_ticker)
        valid_tickers.insert(0, ticker)
    else:
        print "%s is present. move it to front..." % ticker
        valid_tickers.remove(ticker)
        valid_tickers = list(valid_tickers)
        valid_tickers.insert(0, ticker)
        valid_tickers = list(valid_tickers)

    df_corr = stock_utils.generate_correlation_dataframe(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_heatmap(df_corr, valid_tickers)

    return render_template("heatmap.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/temp', methods=['GET'])
def temp():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    heatmap_tickers = retrieve_stock_info.retrieve_sp500_tickers()

    df, valid_tickers = retrieve_stock_info.get_sp500_data(tickers=heatmap_tickers, start=start, end=end)

    if ticker not in valid_tickers:
        print "%s is not present. adding..." % ticker
        df_ticker = retrieve_stock_info.get_adj_close_data(ticker=ticker, start=start, end=end)
        df = df_utils.join_dataframes(df, df_ticker)

    confidence, predictions, data_spread = ml.run_trading_strategy_1(df, ticker)

    return render_template("temp.html", ticker=ticker, confidence=confidence, predictions=predictions,
                           data_spread=data_spread)


@main.route('/macs_stock', methods=['GET'])
def macs_stock():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.adj_close_data(ticker, start, end)
    df_market = retrieve_stock_info.adj_close_data("SPY", start, end)
    generated_script, div_tag, cdn_js, cdn_css, portfolio_value, spy_portfolio_value = \
        ml.run_trading_strategy_2(df, ticker, df_market)

    cash = 1000000

    return render_template("macs_stock.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css, portfolio_value='${:,.2f}'.format(portfolio_value),
                           spy_portfolio_value='${:,.2f}'.format(spy_portfolio_value), cash='${:,.2f}'.format(cash))


@main.route('/macs_portfolio', methods=['GET'])
def macs_portfolio():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    # df = retrieve_stock_info.adj_close_data(ticker, start, end)
    # Get more stocks
    df_apple = retrieve_stock_info.adj_close_data("AAPL", start, end)
    df_microsoft = retrieve_stock_info.adj_close_data("MSFT", start, end)
    df_google = retrieve_stock_info.adj_close_data("GOOG", start, end)
    df_facebook = retrieve_stock_info.adj_close_data("FB", start, end)
    df_twitter = retrieve_stock_info.adj_close_data("TWTR", start, end)
    df_netflix = retrieve_stock_info.adj_close_data("NFLX", start, end)
    df_amazon = retrieve_stock_info.adj_close_data("AMZN", start, end)
    df_yahoo = retrieve_stock_info.adj_close_data("YHOO", start, end)
    df_sony = retrieve_stock_info.adj_close_data("SNY", start, end)
    df_nintendo = retrieve_stock_info.adj_close_data("NTDOY", start, end)
    df_ibm = retrieve_stock_info.adj_close_data("IBM", start, end)
    df_hp = retrieve_stock_info.adj_close_data("HPQ", start, end)

    df_market = retrieve_stock_info.adj_close_data("SPY", start, end)

    stocks = [("AAPL", df_apple), ("MSFT", df_microsoft), ("GOOG", df_google), ("FB", df_facebook),
              ("TWTR", df_twitter), ("NFLX", df_netflix), ("AMZN", df_amazon), ("YHOO", df_yahoo), ("SNY", df_sony),
              ("NTDOY", df_nintendo), ("IBM", df_ibm), ("HPQ", df_hp)]

    cash = 1000000
    generated_script, div_tag, cdn_js, cdn_css, portfolio_value, spy_portfolio_value = \
        ml.run_trading_strategy_3(stocks, df_market, cash=cash)

    return render_template("macs_portfolio.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css, portfolio_value='${:,.2f}'.format(portfolio_value),
                           spy_portfolio_value='${:,.2f}'.format(spy_portfolio_value), cash='${:,.2f}'.format(cash))


@main.route('/analysis_help')
def analysis_help():
    return render_template("analysis_help.html")


@main.route('/corr_table', methods=['GET'])
def corr_table():
    heatmap_tickers = retrieve_stock_info.retrieve_sp500_tickers()
    ticker, start, end = utils.get_ticker_start_date_end_date(session)

    df, valid_tickers = retrieve_stock_info.get_sp500_data(tickers=heatmap_tickers, start=start, end=end)

    if ticker not in valid_tickers:
        print "%s is not present. adding..." % ticker
        df_ticker = retrieve_stock_info.get_adj_close_data(ticker=ticker, start=start, end=end)
        df_ticker.rename(ticker, inplace=True)
        df = df_utils.join_dataframes(df, df_ticker)

    df_corr = stock_utils.generate_correlation_dataframe(df)
    df_corr = df_corr.dropna()

    # Remove ticker that is being analyzed
    df_corr_results = df_corr[df_corr.index != ticker]
    # Find negatively correlated tickers
    df_corr_results = df_corr_results.sort_values(ticker, ascending=True)
    neg_corr_df = df_corr_results[ticker]

    return render_template("corr_table.html", ticker=ticker, neg_corr_df=neg_corr_df)


@main.route('/heatline', methods=['GET'])
def heatline():
    heatmap_tickers = retrieve_stock_info.retrieve_sp500_tickers()
    ticker, start, end = utils.get_ticker_start_date_end_date(session)

    df, valid_tickers = retrieve_stock_info.get_sp500_data(tickers=heatmap_tickers, start=start, end=end)

    if ticker not in valid_tickers:
        print "%s is not present. adding..." % ticker
        df_ticker = retrieve_stock_info.get_adj_close_data(ticker=ticker, start=start, end=end)
        df_ticker.rename(ticker, inplace=True)
        df = df_utils.join_dataframes(df, df_ticker)
        valid_tickers.insert(0, ticker)
    else:
        print "%s is present. move it to front..." % ticker
        valid_tickers.remove(ticker)
        valid_tickers = list(valid_tickers)
        valid_tickers.insert(0, ticker)
        valid_tickers = list(valid_tickers)

    df_corr = stock_utils.generate_correlation_dataframe(df)
    df_corr = df_corr.dropna()

    # Remove ticker that is being analyzed
    df_corr_results = df_corr[df_corr.index != ticker]
    # Find negatively correlated tickers
    df_corr_results = df_corr_results.sort_values(ticker, ascending=True)
    neg_corr_df = df_corr_results[ticker][:5]
    # Find positively correlated tickers
    df_corr_results = df_corr_results.sort_values(ticker, ascending=False)
    pos_corr_df = df_corr_results[ticker][:5]

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_heatline(df_corr, valid_tickers, ticker)

    return render_template("heatline.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css, neg_corr_df=neg_corr_df, pos_corr_df=pos_corr_df)


@main.route('/candle_plot', methods=['GET'])
@utils.log_time("candle_plot")
def candle_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_candlestick_plot(df, ticker)

    return render_template("candle_stick.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/bollinger_bands_plot', methods=['GET'])
@utils.log_time("bollinger_bands_plot")
def bollinger_bands_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)
    df = stock_utils.calculate_rolling_mean(df, column_name="AdjClose_"+ticker)
    df = stock_utils.calculate_bollinger_bands(df, column_name="AdjClose_"+ticker)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_bollinger_plot(df, ticker)

    return render_template("bollinger_bands_plot.html", ticker=ticker, generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/trade_volume_plot')
@utils.log_time("trade_volume_plot")
def trade_volume_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_volume_data(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_volume_bar_plot(df, ticker)

    return render_template("volume_histo_plot.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/mov_av_20day_plot')
@utils.log_time("mov_av_20day_plot")
def mov_av_20day_plot():
    return mov_av_plot(20)


@main.route('/mov_av_50day_plot')
@utils.log_time("mov_av_50day_plot")
def mov_av_50day_plot():
    return mov_av_plot(50)


@main.route('/mov_av_200day_plot')
@utils.log_time("mov_av_200day_plot")
def mov_av_200day_plot():
    return mov_av_plot(200)


def mov_av_plot(num_days):
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)
    column_name = "AdjClose_" + ticker
    df = stock_utils.calculate_rolling_mean(df, window=num_days, column_name=column_name)

    tickers = ["rolling_mean", column_name]
    generated_script, div_tag, cdn_js, cdn_css = \
        visualization.generate_multi_line_plot(df, tickers=tickers, labels=[str(num_days) + "day rolling mean", ticker])

    return render_template("mov_av_plot.html", num_days=num_days, ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/adj_close_plot', methods=['GET'])
@utils.log_time("adj_close_plot")
def adj_close_plot():
    form = CheckMediaForm()
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.adj_close_data(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = \
        visualization.generate_single_line_plot(df, column='AdjClose_' + ticker)
    return render_template("adj_close_plot.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css, form=form, start=start, end=end)


@main.route('/check_social_media', methods=['GET', 'POST'])
def check_social_media():
    from urllib import urlopen
    from lxml.html import parse

    def get_google_news(ticker, start, end):
        url = 'http://www.google.com/finance/company_news?q=NASDAQ%3A' + ticker + '&startdate=' + start + '&enddate=' + end + '&num=100'
        tree = parse(urlopen(url))

        print url

        try:
            news = tree.xpath("//div[@id='news-main']//div/span/a")
            urls = []
            titles = []
            for b in news:
                # url
                url = b.attrib['href']
                urls.append(url)
                # print(url)
                # article title
                title = b.text_content()
                # print(title)
                titles.append(title)

            metas = []
            news = tree.xpath("//div[@id='news-main']//div/div[@class='byline']")
            for b in news:
                # meta
                meta = b.text_content()
                # print(meta)
                metas.append(meta)

            abstracts = []
            news = tree.xpath("//div[@id='news-main']//div/div[starts-with(@id,'Article')]/div")
            for b in news:
                # abstract
                abstract = b.text_content()
                # print(abstract)
                abstracts.append(abstract)

        except IndexError:
            urls, titles, metas, abstracts = [], [], [], []
        return urls, titles, metas, abstracts

    form = request.form
    ticker = form['ticker_symbol']
    start = form['start']
    end = form['end']
    urls, titles, metas, abstracts = get_google_news(ticker, start, end)
    return render_template("check_social_media.html", ticker=ticker, start=start, end=end, urls=urls, titles=titles,
                           metas=metas, abstracts=abstracts)


@main.route('/adj_close_histo_plot')
@utils.log_time("adj_close_histo_plot")
def adj_close_histo_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)
    daily_returns = stock_utils.calculate_daily_returns(df)

    generated_script, div_tag, cdn_js, cdn_css, mean, std = \
        visualization.generate_adj_close_histo_plot(daily_returns, ticker)

    return render_template("adj_close_histo_plot.html", ticker=ticker, generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css, mean=mean, std=std)


@main.route('/us_comparison_plot_adjclose', methods=['GET'])
@utils.log_time("us_comparison_plot_adjclose")
def us_comparison_plot_adjclose():
    return comparison_plot(economy_type="U.S.", plot_type="adjclose")


@main.route('/us_comparison_plot_norm', methods=['GET'])
@utils.log_time("us_comparison_plot_norm")
def us_comparison_plot_norm():
    return comparison_plot(economy_type="U.S.", plot_type="norm")


@main.route('/us_comparison_plot_daily', methods=['GET'])
@utils.log_time("us_comparison_plot_daily")
def us_comparison_plot_daily():
    return comparison_plot(economy_type="U.S.", plot_type="daily")


@main.route('/us_comparison_plot_cum', methods=['GET'])
@utils.log_time("us_comparison_plot_cum")
def us_comparison_plot_cum():
    return comparison_plot(economy_type="U.S.", plot_type="cum")


@main.route('/global_comparison_plot_adjclose', methods=['GET'])
@utils.log_time("global_comparison_plot_adjclose")
def global_comparison_plot_adjclose():
    return comparison_plot(economy_type="Global", plot_type="adjclose")


@main.route('/global_comparison_plot_norm', methods=['GET'])
@utils.log_time("global_comparison_plot_norm")
def global_comparison_plot_norm():
    return comparison_plot(economy_type="Global", plot_type="norm")


@main.route('/global_comparison_plot_daily', methods=['GET'])
@utils.log_time("global_comparison_plot_daily")
def global_comparison_plot_daily():
    return comparison_plot(economy_type="Global", plot_type="daily")


@main.route('/global_comparison_plot_cum', methods=['GET'])
@utils.log_time("global_comparison_plot_cum")
def global_comparison_plot_cum():
    return comparison_plot(economy_type="Global", plot_type="cum")


def comparison_plot(economy_type, plot_type):
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    if economy_type == "U.S.":
        df, tickers = retrieve_stock_info.get_us_comparison_data(ticker, start, end)
    else:
        df, tickers = retrieve_stock_info.get_global_comparison_data(ticker, start, end)

    if plot_type == "cum":
        comparator_type = "cumulative changes"
        df = stock_utils.calculate_cumulative_returns(df)
    elif plot_type == "daily":
        comparator_type = "daily changes"
        df = stock_utils.calculate_daily_returns(df)
    elif plot_type == "norm":
        comparator_type = "normalized prices"
        df = stock_utils.normalize_data(df)
    elif plot_type == "adjclose":
        comparator_type = "close prices"

    generated_script, div_tag, cdn_js, cdn_css = \
        visualization.generate_multi_line_plot(df, tickers=tickers, labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type=comparator_type,
                           economy_type=economy_type, generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js,
                           cdn_css=cdn_css)

@main.route('/available_stocks', methods=['GET'])
@utils.log_time("available_stocks")
def available_stocks():
    return render_template("available_stocks.html")