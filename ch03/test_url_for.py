# -*- coding: utf-8 -*-
__author__ = 'woojin'

from flask import Flask, url_for

# flask application의 모듈명으로 Flask app 객체인 app을 생성
# 이 app으로 모든 플라스크의 기능 사용 가능
app = Flask(__name__)

@app.route('/hello/')
def hello():
	return '안녕, 플라스크!'

@app.route('/profile/<username>')
def get_profile(username):
	return 'profile : ' + username

@app.route('/message/<int:message_id>')
def get_message(message_id):
	return 'message_id : %d' % message_id

if __name__ == '__main__':
	with app.test_request_context():
		print url_for('hello')
		print url_for('get_profile', username='flask')
