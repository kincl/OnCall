from flask import Blueprint, current_app, flash, render_template, get_flashed_messages, request, redirect
from flask_login import login_required, login_user, logout_user

from api.models import User

from cal.forms import LoginForm

calendar_app = Blueprint('cal', __name__,
                         url_prefix='',
                         static_folder='static',
                         static_url_path='/static/cal',
                         template_folder='templates')

@calendar_app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        from oncall.ldap_helper import bind

        password_bind = None
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            if current_app.config['DEBUG']:
                password_bind = True
            else:
                password_bind = bind(request.form.get('username'), request.form.get('password'))
        if password_bind:
            login_user(user)
            return redirect(request.args.get('next') or '/')
        else:
            flash('Invalid login', 'danger')
    else:
        if current_app.debug:
            flash('Debug mode')
    return render_template('login.html', form=form, flashes=get_flashed_messages())


@calendar_app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')
