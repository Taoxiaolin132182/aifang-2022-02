本目录为我们自己的框架代码，提供一些基础的抽象和工具

每个文件中有详细的注释说明，这里给出简要说明如下：
│  README.md                本说明文件
│  util.py                  常用的一些工具类方法
│  log.py                   日志相关的封装
│  count_down_latch.py      类似java的CountDownLatch
│  db_mgr.py                访问mysql相关的方法
│  fork_service.py          全局服务类，详见文件注释
│  auto_queue.py            用于处理流水线数据的队列
│  data_filter.py           能并行处理数据的流水线基类
│  db_filter.py             用于处理数据库的流水线模块（派生自data_filter）
│  db_filter_task.py        通过db_filter构建的db异步处理任务，给那些不使用我们框架的服务使用
│  nop_filter.py            一个什么都不处理的流水线模块，作为数据驱动入口
│  thread_group.py          多个运行线程的组合管理类，只提供基础的启动停止方法，不同于线程池，切勿混淆
│  timer_thread.py          定时任务的线程，另外本模块中simple_task_thread还实现了一些常规定时任务，如删除日志，删除存储图片，删除过时数据库记录
│  video_capture.py         视频采集，只支持文件或者标准协议的视频流
│  video_capture_group.py   多个video_capture组成的视频采集组




