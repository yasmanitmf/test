from flask import render_template, redirect, url_for, flash, Blueprint

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    return render_template('home.html', title='Home')

@main.route('/about_us')
def about_us():
    return render_template('about_us.html', title='AboutUs')

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', title='Dashboard')
