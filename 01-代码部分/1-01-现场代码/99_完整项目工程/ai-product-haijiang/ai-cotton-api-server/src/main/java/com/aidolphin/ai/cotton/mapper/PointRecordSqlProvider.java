package com.aidolphin.ai.cotton.mapper;

import java.util.Map;

import org.apache.ibatis.jdbc.SQL;

import com.gmm.common.StringUtil;

public class PointRecordSqlProvider {
	public String getSelectRecordSql(Map<String, Object> parameter) {

        return new SQL() {
			{
				SELECT("*");
				FROM("t_point_record");
                
                if (parameter.get("pointId") != null) {
                    WHERE("point_id=#{pointId}");
                }
                if (parameter.get("takePhotoId") != null) {
                    WHERE("take_photo_id=#{takePhotoId}");
                }
                if (parameter.get("imageId") != null) {
                    WHERE("image_id=#{imageId}");
                }
                if (parameter.get("state") != null) {
                    WHERE("state=#{state}");
                }
                if (parameter.get("beginCreateTime") != null) {
                    WHERE("create_time>=#{beginCreateTime}");
                }
                if (parameter.get("endCreateTime") != null) {
                    WHERE("create_time<=#{endCreateTime}");
                }
                ORDER_BY("point_id desc");
                        
			}
		}.toString() + " limit #{beginIndex}, #{maxCount}";

	}

	public String getSelectCountSql(Map<String, Object> parameter) {

        return new SQL() {
			{
				SELECT("count(*)");
				FROM("t_point_record");
                
                if (parameter.get("pointId") != null) {
                    WHERE("point_id=#{pointId}");
                }
                if (parameter.get("takePhotoId") != null) {
                    WHERE("take_photo_id=#{takePhotoId}");
                }
                if (parameter.get("imageId") != null) {
                    WHERE("image_id=#{imageId}");
                }
                if (parameter.get("state") != null) {
                    WHERE("state=#{state}");
                }
                if (parameter.get("beginCreateTime") != null) {
                    WHERE("create_time>=#{beginCreateTime}");
                }

                if (parameter.get("endCreateTime") != null) {
                    WHERE("create_time<=#{endCreateTime}");
                }
			}
		}.toString();

	}

	public String getUpdateSql(PointRecord record) {

        return new SQL() {
			{
				UPDATE("t_point_record");

                
                if (record.getTakePhotoId() != null) {
                    SET("take_photo_id=#{takePhotoId}");
                }
                if (record.getImageId() != null) {
                    SET("image_id=#{imageId}");
                }
                if (StringUtil.isNotBlank(record.getSpeed())) {
                    SET("speed = #{speed}");
                }
                if (record.getPointXmax() != null) {
                    SET("point_xmax=#{pointXmax}");
                }
                if (record.getPointYmax() != null) {
                    SET("point_ymax=#{pointYmax}");
                }
                if (record.getPointXmin() != null) {
                    SET("point_xmin=#{pointXmin}");
                }
                if (record.getPointYmin() != null) {
                    SET("point_ymin=#{pointYmin}");
                }
                if (record.getPointXcenter() != null) {
                    SET("point_xcenter=#{pointXcenter}");
                }
                if (record.getPointYcenter() != null) {
                    SET("point_ycenter=#{pointYcenter}");
                }
                if (record.getState() != null) {
                    SET("state=#{state}");
                }
                if (record.getIsDel() != null) {
                    SET("is_del=#{isDel}");
                }
                if (record.getCreateTime() != null) {
                    SET("create_time=#{createTime}");
                }
                if (record.getUpdateTime() != null) {
                    SET("update_time=#{updateTime}");
                }
                WHERE("point_id=#{pointId}");
			}
		}.toString();

	}

}
