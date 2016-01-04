
# MiniTwit
~~~~~~~~~~~
## because writing todo lists is not fun

### What is MiniTwit?

	A SQLite and Flask powered twitter clone
	
### 미니트윗 주요 기능
#### 미니트윗을 사용할 사용자 등록
#### 등록된 사용자의 로그인/로그아웃
#### 등록된 사용자의 트윗글 등록
#### 등록된 사용자를 팔로우(follow)/언팔로우(unfollow)
#### 공용(public)/기본/사용자 타임라인(트윗글 목록) 지원

### How do I use it?

1. edit the configuration in the minitwit.py file or export an MINITWIT_SETTINGS environment variable pointing to a configuration file.

2. fire up a python shell and run this:

    ```from minitwit import init_db; init_db()```

3. now you can run the minitwit.py file with your python interpreter and the application will greet you on http://localhost:5000/

## Is it tested?

You betcha.
Run the
```minitwit_tests.py```
file to see the tests pass.
