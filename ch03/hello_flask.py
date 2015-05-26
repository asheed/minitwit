# -*- coding: utf-8 -*-
__author__ = 'woojin'

# flask 모듈의 Flask 클래스 임포트
from flask import Flask
# flask application의 모듈명으로 Flask app 객체인 app을 생성
# 이 app으로 모든 플라스크의 기능 사용 가능
app = Flask(__name__)

# 뷰함수 정의
@app.route('/')
def hello_flask():
	return '안녕 파이썬 플라스크!'

@app.route('/hello')
def hello():
	return '/hello 경로를 통해 접근했군요!'

if __name__ == '__main__':
	app.run()