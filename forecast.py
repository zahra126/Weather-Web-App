from flask import Flask, render_template, redirect, request
import requests
import datetime
import matplotlib.pyplot as plt
import plotly.tools as tls


app = Flask(__name__)


def kelvin_to_fahrenheit(kelvin):
    return kelvin * (9/5) - 459.67


@app.route('/')
def main():
    return redirect('/index')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/display', methods=['POST', 'GET'])
def display():
    if request.method == 'POST':

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Get requested city from user ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        requested_city = request.form['City']
        # requested_country = request.form['Country']

        # Generate urls
        current_url = 'http://api.openweathermap.org/data/2.5/weather?appid=c34f59e9b1c5f3c88aef5bca7d846193&q=%s'\
                      % requested_city

        five_day_url = 'http://api.openweathermap.org/data/2.5/forecast?appid=c34f59e9b1c5f3c88aef5bca7d846193' \
                            '&q=%s' % requested_city

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Get current weather information ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        current_data = requests.get(current_url).json()

        try:
            fahrenheit = round(kelvin_to_fahrenheit(current_data['main']['temp']), 1)
            min_fahrenheit = kelvin_to_fahrenheit(current_data['main']['temp_min'])
            max_fahrenheit = kelvin_to_fahrenheit(current_data['main']['temp_max'])
            main_weather = current_data['weather'][0]['main']
            icon = current_data['weather'][0]['icon']

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Generate Icon Url ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

            icon_url = 'http://openweathermap.org/img/w/%s.png' % icon

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Get 5 day forecast ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
            five_day_data = requests.get(five_day_url).json()
            forecasts = five_day_data['list']

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Get Average Temperatures for 5 day forecast ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
            forecasts_by_day = []
            three_hourly_forecast = []
            average_temperatures = []
            x = []                      # dates for graph
            y = []                      # temperatures for graph
            date_string = forecasts[0]['dt_txt'].split()
            date = date_string[0]
            todays_date = datetime.datetime.today().strftime('%Y-%m-%d')

            # if 5 day forecast api returned only 4 days data
            # then get average of today's weather from current weather api request
            if date != todays_date:
                todays_temp = round((min_fahrenheit + max_fahrenheit) / 2, 1)
                average_temperatures.append(
                    {'date': todays_date, 'temperature': todays_temp})
                x.append(todays_date)
                y.append(todays_temp)

            # group json data by date
            for f in forecasts:
                date_string = f['dt_txt'].split()
                if date == date_string[0]:
                    three_hourly_forecast.append(f)
                else:
                    forecasts_by_day.append(three_hourly_forecast)
                    three_hourly_forecast = []
                    date = date_string[0]
                    three_hourly_forecast.append(f)

            # calculate average for each date
            average_temperature = 0
            for i in forecasts_by_day:
                for f in i:
                    average_temperature += kelvin_to_fahrenheit(f['main']['temp'])
                date_string = i[0]['dt_txt'].split()
                forecast_date = date_string[0]
                average_temperature = round(average_temperature / len(i), 1)
                average_temperatures.append({'date': forecast_date, 'temperature': average_temperature})
                x.append(forecast_date)
                y.append(average_temperature)

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Remove Existing Graph If Exists ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Generate Forecast Graph ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

            mpl_fig = plt.figure()
            ax = mpl_fig.add_subplot(111)

            line, = ax.plot(x, y, lw=2)

            ax.set_title("5 Day Forecast for " + requested_city)
            ax.set_xlabel("Date")
            ax.set_ylabel("Average Temperature in Fahrenheit")

            plotly_fig = tls.mpl_to_plotly(mpl_fig)

            img_path = "static/" + requested_city + ".png"
            img_src = "{{url_for('static', filename=%s)}}" % img_path
            mpl_fig.savefig(img_path)

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Render Template ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

            return render_template('display.html', requested_city=requested_city,
                                   fahrenheit=fahrenheit, main_weather=main_weather, img_src=img_src,
                                   average_temperatures=average_temperatures, icon_url=icon_url, img_path=img_path)
        except:
            return render_template('404.html'), 404


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.debug = True
    app.run(port=33507)
