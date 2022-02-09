p9116_linux30_drvsrc为板卡驱动，
需要linux内核头文件：
sudo apt-get install linux-headers-$(uname -r)

#编译
#make -C /lib/modules/`uname -r`/build SUBDIRS=`pwd` modules
make -C /lib/modules/`uname -r`/build M=`pwd` modules


中断的属性设置：

#define IRQF_DISABLED       0x00000020   /*中断禁止*/
#define IRQF_SAMPLE_RANDOM  0x00000040    /*供系统产生随机数使用*/
#define IRQF_SHARED      0x00000080 /*在设备之间可共享*/
#define IRQF_PROBE_SHARED   0x00000100/*探测共享中断*/
#define IRQF_TIMER       0x00000200/*专用于时钟中断*/
#define IRQF_PERCPU      0x00000400/*每CPU周期执行中断*/
#define IRQF_NOBALANCING 0x00000800/*复位中断*/
#define IRQF_IRQPOLL     0x00001000/*共享中断中根据注册时间判断*/
#define IRQF_ONESHOT     0x00002000/*硬件中断处理完后触发*/


#include <linux/slab.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/wait.h>
#include <linux/sched.h>