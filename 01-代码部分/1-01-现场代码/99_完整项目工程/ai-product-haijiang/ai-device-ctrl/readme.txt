用于AI项目中控制各种外部设备的类库

目录结构：
├─cpp（c++动态库代码）
├─others（其他）
├─output（输出目录）
│  ├─linux
│  ├─temp
│  └─win
│      └─x64
│          └─Release （Windows输出dll在此）
├─prj
│  ├─python （vs2017的python工程）
│  └─windows（vs2017的windows dll工程）
└─python（python封装代码）
   ├─test.py（所有的python测试demo代码）
   └─AIDeviceCtrl（外部代码使用本目录作为模块导入）

动态库编译：
windows编译打开工程编译即可
linux编译直接在cpp源码下make

demo：
python使用方法参考test.py




