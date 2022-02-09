/*
SQLyog Ultimate v10.51 
MySQL - 5.7.30-0ubuntu0.18.04.1 : Database - db_cotton_local
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`db_cotton_local` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `db_cotton_local`;

/*Table structure for table `tUploadConfig` */

DROP TABLE IF EXISTS `tUploadConfig`;

CREATE TABLE `tUploadConfig` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '序号',
  `upload_batch` varchar(32) NOT NULL DEFAULT 'all' COMMENT '上传批次',
  `upload_operate_status` int(11) NOT NULL DEFAULT '0' COMMENT '上传操作批次状态[0:全部;1:合格;2:不合格]',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*Table structure for table `t_batch` */

DROP TABLE IF EXISTS `t_batch`;

CREATE TABLE `t_batch` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `primary_batch` varchar(30) NOT NULL DEFAULT '' COMMENT '大批次',
  `secondary_batch` varchar(30) NOT NULL DEFAULT '' COMMENT '小批次',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

/*Table structure for table `t_err_record` */

DROP TABLE IF EXISTS `t_err_record`;

CREATE TABLE `t_err_record` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `err_code` int(11) NOT NULL DEFAULT '0' COMMENT '异常代码',
  `err_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '异常时间',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  `err_instructions` varchar(64) NOT NULL COMMENT '代码说明',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8;

/*Table structure for table `t_file_tracker` */

DROP TABLE IF EXISTS `t_file_tracker`;

CREATE TABLE `t_file_tracker` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '序号',
  `image_path` varchar(255) NOT NULL DEFAULT '' COMMENT '文件路径',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '上传状态[0:未上传;1:上传中;2:上传成功;3:上传失败]',
  `try_times` int(11) NOT NULL DEFAULT '0' COMMENT '尝试次数',
  `create_time` timestamp NOT NULL DEFAULT '2000-01-01 00:00:00' COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT '2000-01-01 00:00:00' COMMENT '更新时间',
  `image_file_update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '图片更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_image_path` (`image_path`),
  KEY `idx_image_file_update_time` (`image_file_update_time`),
  KEY `idx_status` (`status`),
  KEY `idx_try_times` (`try_times`)
) ENGINE=InnoDB AUTO_INCREMENT=315181 DEFAULT CHARSET=utf8 COMMENT='通用上传任务图片状态中间表';

/*Table structure for table `t_image_record` */

DROP TABLE IF EXISTS `t_image_record`;

CREATE TABLE `t_image_record` (
  `image_id` bigint(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '图片编号',
  `take_photo_id` bigint(20) unsigned NOT NULL COMMENT '拍照编号',
  `batch_no` varchar(32) NOT NULL DEFAULT '""' COMMENT '批次号',
  `image_path` varchar(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '' COMMENT '图片地址',
  `photo_begin_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '拍照开始时间',
  `photo_end_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '拍照结束时间',
  `call_ai_begin_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '调用AI开始时间',
  `call_ai_end_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '调用AI结束时间',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  `state` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态[0:无效;1:有效]',
  PRIMARY KEY (`image_id`),
  KEY `idx_take_photo_id` (`take_photo_id`),
  KEY `idx_photo_begin_time` (`photo_begin_time`),
  KEY `idx_call_ai_begin_time` (`call_ai_begin_time`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8 COMMENT='图片表';

/*Table structure for table `t_point_record` */

DROP TABLE IF EXISTS `t_point_record`;

CREATE TABLE `t_point_record` (
  `point_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `take_photo_id` bigint(20) unsigned NOT NULL COMMENT '拍照编号',
  `image_id` bigint(20) unsigned NOT NULL COMMENT '图片编号',
  `type` varchar(32) NOT NULL COMMENT '分类',
  `ff_color` varchar(32) NOT NULL DEFAULT '""' COMMENT '异纤颜色',
  `ff_type` varchar(32) NOT NULL DEFAULT '""' COMMENT '异纤种类',
  `batch_no` varchar(32) NOT NULL DEFAULT '""' COMMENT '批次号',
  `threshold` decimal(5,2) NOT NULL COMMENT '阈值',
  `level` int(11) NOT NULL COMMENT '等级',
  `speed` decimal(5,2) NOT NULL COMMENT '传送带速度',
  `point_xmax` int(11) NOT NULL DEFAULT '0' COMMENT '点的最大x坐标',
  `point_ymax` int(11) NOT NULL DEFAULT '0' COMMENT '点的最大y坐标',
  `point_xmin` int(11) NOT NULL DEFAULT '0' COMMENT '点的最小x坐标',
  `point_ymin` int(11) NOT NULL DEFAULT '0' COMMENT '点的最小y坐标',
  `point_xcenter` int(11) NOT NULL DEFAULT '0' COMMENT '点的中心x坐标',
  `point_ycenter` int(11) NOT NULL DEFAULT '0' COMMENT '点的中心y坐标',
  `state` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态[1:新增;2;超出边缘;3:重复;4:成功抓取;5:来不及抓取]',
  `is_del` tinyint(4) NOT NULL DEFAULT '1' COMMENT '是否删除[0:是;1:否]',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  PRIMARY KEY (`point_id`),
  KEY `idx_take_photo_id` (`take_photo_id`),
  KEY `idx_image_id` (`image_id`),
  KEY `idx_state` (`state`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8 COMMENT='点位表';

/*Table structure for table `t_supplier` */

DROP TABLE IF EXISTS `t_supplier`;

CREATE TABLE `t_supplier` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `number` bigint(11) unsigned NOT NULL DEFAULT '1' COMMENT '编号',
  `Chinese_name` varchar(30) NOT NULL DEFAULT '' COMMENT '中文名称',
  `for_short` varchar(30) NOT NULL DEFAULT '' COMMENT '英文简称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=336 DEFAULT CHARSET=utf8;

/*Table structure for table `t_take_photo_record` */

DROP TABLE IF EXISTS `t_take_photo_record`;

CREATE TABLE `t_take_photo_record` (
  `take_photo_id` bigint(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '拍照编号',
  `batch_no` varchar(32) CHARACTER SET utf8mb4 NOT NULL DEFAULT '' COMMENT '批次',
  `photo_begin_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '拍照开始时间',
  `photo_end_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '拍照结束时间',
  `call_ai_begin_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '调用AI开始时间',
  `call_ai_end_time` timestamp(3) NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '调用AI结束时间',
  `create_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '添加时间',
  `update_time` timestamp(3) NOT NULL DEFAULT '2000-01-01 00:00:00.000' COMMENT '更新时间',
  `state` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态[0:无效;1:有效]',
  PRIMARY KEY (`take_photo_id`),
  KEY `idx_batch_no` (`batch_no`) USING BTREE,
  KEY `idx_photo_begin_time` (`photo_begin_time`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_call_ai_begin_time` (`call_ai_begin_time`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8 COMMENT='拍照表';

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
