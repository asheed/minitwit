# -*- coding: utf-8 -*-
__author__ = 'woojin'

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_flask():
	return '안녕 파이썬 플라스크!'

if __name__ == '__main__':
	app.run()