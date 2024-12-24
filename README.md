# 如何使用
1. 安装python环境
2. 安装依赖
```shell
pip install -r requirements.txt
```
3. 配置
accounts.txt格式如下：
邮箱:邀请码
proxies.txt格式如下：
http://username:password@ip:port
4. 注册时，使用统一密码，方便后续登录，具体配置在config.py中，可自行修改
5. 运行
```shell
# 执行初始化，该步骤主要是将账号信息写入数据库进行管理
python app.py init
# 执行注册
python app.py register
# 连接钱包，可选择是否执行，如果不执行，需要手动连接钱包。如果执行的话，会自动生成钱包和私钥，然后进行签名连接
python app.py link_wallet
# 完成任务
python app.py complete_task
# 跑分挖矿
nohup python app.py farm &
# 查看日志
tail -f nohup.out
```

# 注意事项
1. 请妥善保管好生成的openloop.db，里面包含了账号信息，如果泄露，可能会导致账号被盗
2. 导出的openloop.db如何使用，参考如下：sqllite.md
3. 如果账号比较多，执行需要的时间比较长的话，可以执行命令前开始一个screen，然后在screen中执行命令，这样即使断开连接，也不会影响执行
```shell
screen -S openloop
python app.py ***
```
4. 另外，该项目的邀请机制如下：<br/>
    一级 (F1)：赚取你直接推荐的朋友 (F1) 所积累的所有积分的 5%。<br/>
    二级 (F2)：获取你推荐的朋友的朋友所赚取积分的 3%。<br/>
    三级 (F3)：收集你的扩展网络 (F3) 所赚取积分的 1%。<br/>
可是自己思考下，如何设计自己的账号体系，来获取更多的积分。




# 后续更新
1. 作者会关注官方是否有更新，如果有更新，会及时更新代码；更新不及时也请见谅，平时需要搬砖
2. 如果通过本脚本运行，导致账号被封，请自行承担风险，作者不承担任何责任
3. 有问题，欢迎提issue，作者会尽量解答

# 打赏
如果觉得脚本有用，可以请我喝杯咖啡，谢谢！
1. eth地址：0x69d9391e22Ba5a0648A518C3649dB0eA7aD738a2
2. sol地址：DNPqAevobL5mA6SZDU2DY2XJ6MuDs4CVFnPp5PjrGM9j


