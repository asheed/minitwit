# -*- coding: utf-8 -*-
"""
    MiniTwit
    ~~~~~~~~

    A microblogging application written with Flask and sqlite3.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash
from werkzeug.security import check_password_hash, generate_password_hash


# configuration for database (Must be Upper String)
DATABASE = 'C:/tmp/minitwit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)


def connect_db():
    """Returns a new connection to the database."""
    # DB연결
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    """
    :param query: 실행할 질의문
    :param args: 바인딩 변수(튜플)
    :param one: one == True 인 경우 모든 값, False 인 경우 첫번째 요소만 리턴
    :return: 결과값
    """
    """Queries the database and returns a list of dictionaries."""
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = g.db.execute('select user_id from user where username = ?',
                       [username]).fetchone()
    return rv[0] if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), 
         size)


@app.before_request
def before_request():
    """Make sure we are connected to the database each request and look
    up the current user so that we know he's there.
    g객체는 전역 객체로, 한번의 요청에 대해서만 같은 값을 유지하고, 스레드에 안전하다.
    각 요청이 생성되기 바로 전에 g 객체의 db와 user 속성에 각 데이터베이스 연결과 사용자 정보를 저장하고,
    오류가 발생하더라도, g객체에 데이터베이스 연결 속성인 'db'가 있는지 확인하고 데이터베이스 연결을 닫는다.
    """
    g.db = connect_db()
    g.user = None
    if 'user_id' in session:    # 세션에 사용자 id가 있으면
        g.user = query_db('select * from user where user_id = ?',   # db에 질의하여 사용자 정보를 가져온다.
                          [session['user_id']], one=True)


@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):    # 전역객체 g에 'db'속성이 있으면, db를 닫는다.
        g.db.close()


@app.route('/')
def timeline():
    """Shows a users timeline or if no user is logged in it will
    redirect to the public timeline.  This timeline shows the user's
    messages as well as all the messages of followed users.
    """
    if not g.user:
        return redirect(url_for('public_timeline'))
    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id and (
            user.user_id = ? or
            user.user_id in (select whom_id from follower
                                    where who_id = ?))
        order by message.pub_date desc limit ?''',
        [session['user_id'], session['user_id'], PER_PAGE]))


@app.route('/public')
def public_timeline():
    """Displays the latest messages of all users."""
    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id
        order by message.pub_date desc limit ?''', [PER_PAGE]))


@app.route('/<username>')
def user_timeline(username):
    """Display's a users tweets."""
    profile_user = query_db('select * from user where username = ?',
                            [username], one=True)
    if profile_user is None:
        abort(404)
    followed = False
    if g.user:
        followed = query_db('''select 1 from follower where
            follower.who_id = ? and follower.whom_id = ?''',
            [session['user_id'], profile_user['user_id']],
            one=True) is not None
    return render_template('timeline.html', messages=query_db('''
            select message.*, user.* from message, user where
            user.user_id = message.author_id and user.user_id = ?
            order by message.pub_date desc limit ?''',
            [profile_user['user_id'], PER_PAGE]), followed=followed,
            profile_user=profile_user)


@app.route('/<username>/follow')
def follow_user(username):
    """Adds the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    g.db.execute('insert into follower (who_id, whom_id) values (?, ?)',
                [session['user_id'], whom_id])
    g.db.commit()
    flash(u'당신은 지금부터 "%s"를 following 합니다.' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/<username>/unfollow')
def unfollow_user(username):
    """Removes the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    g.db.execute('delete from follower where who_id=? and whom_id=?',
                [session['user_id'], whom_id])
    g.db.commit()
    flash(u'당신은 더이상 "%s"를 following 하지 않습니다.' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/add_message', methods=['POST'])
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        g.db.execute('''insert into 
            message (author_id, text, pub_date)
            values (?, ?, ?)''', (session['user_id'], 
                                  request.form['text'],
                                  int(time.time())))
        g.db.commit()
        flash(u'게시물이 등록되었습니다.')
    return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = u'username이 존재하지 않습니다.'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = u'비밀번호가 맞지 않습니다.'
        else:
            flash(u'정상적으로 로그인 되었습니다.')
            session['user_id'] = user['user_id']
            return redirect(url_for('timeline'))
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:          # 로그인을 했다면, timeline으로 리다이렉션, 아니면 HTTP 메서드에 따라, 사용자를 등록
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':            # POST인 경우, form을 통해 등록을 했다는 의미이므로, 등록을 처리
        # 유효성 검사
        if not request.form['username']:
            error = u'Username은 반드시 입력하여야 합니다.'
        elif not request.form['email'] or \
                 '@' not in request.form['email']:
            error = u'올바르지 않은 형식의 이메일 주소입니다.'
        elif not request.form['password']:
            error = u'비밀번호는 반드시 입력하여야 합니다.'
        elif request.form['password'] != request.form['password2']:
            error = u'비밀번호가 일치하지 않습니다.'
        elif get_user_id(request.form['username']) is not None:
            error = u'Username이 이미 존재합니다.'
        else:   # 유효성 검사가 통과했다면, db에 저장
            g.db.execute('''insert into user (
                username, email, pw_hash) values (?, ?, ?)''',
                [request.form['username'], request.form['email'],
                 generate_password_hash(request.form['password'])])     # one-way hashing for password
            g.db.commit()   # 커밋
            flash(u'당신은 성공적으로 등록되었으며, 지금부터 로그인 가능합니다.')
            # 성공 메시지 설정, 템플릿에서 get_flashed_messages()를 사용하여 얻을 수 있다.
            return redirect(url_for('login'))
    return render_template('register.html', error=error)            # GET이라면 등록이 필요하므로 등록화면으로 이동


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash(u'정상적으로 로그아웃 되었습니다.')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=20000 , threaded=True, debug=True)
