package com.aidolphin.ai.cotton.mapper;

import java.util.Map;

import org.apache.ibatis.jdbc.SQL;

import com.gmm.common.StringUtil;

public class TakePhotoRecordSqlProvider {
	public String getSelectRecordSql(Map<String, Object> parameter) {

        return new SQL() {
			{
				SELECT("*");
				FROM("t_take_photo_record");
                
                if (parameter.get("takePhotoId") != null) {
                    WHERE("take_photo_id=#{takePhotoId}");
                }
                if ( (parameter.get("batchNo") != null)
                        && (StringUtil.isNotBlank(parameter.get("batchNo").toString())) ) {
                    WHERE("batch_no=#{batchNo}");
                }
                if (parameter.get("beginPhotoBeginTime") != null) {
                    WHERE("photo_begin_time>=#{beginPhotoBeginTime}");
                }
                if (parameter.get("endPhotoBeginTime") != null) {
                    WHERE("photo_begin_time<=#{endPhotoBeginTime}");
                }
                if (parameter.get("beginCallAiBeginTime") != null) {
                    WHERE("call_ai_begin_time>=#{beginCallAiBeginTime}");
                }
                if (parameter.get("endCallAiBeginTime") != null) {
                    WHERE("call_ai_begin_time<=#{endCallAiBeginTime}");
                }
                if (parameter.get("beginCreateTime") != null) {
                    WHERE("create_time>=#{beginCreateTime}");
                }
                if (parameter.get("endCreateTime") != null) {
                    WHERE("create_time<=#{endCreateTime}");
                }
                ORDER_BY("take_photo_id desc");
                        
			}
		}.toString() + " limit #{beginIndex}, #{maxCount}";

	}

	public String getSelectCountSql(Map<String, Object> parameter) {

        return new SQL() {
			{
				SELECT("count(*)");
				FROM("t_take_photo_record");
                
                if (parameter.get("takePhotoId") != null) {
                    WHERE("take_photo_id=#{takePhotoId}");
                }
                if ( (parameter.get("batchNo") != null)
                        && (StringUtil.isNotBlank(parameter.get("batchNo").toString())) ) {
                    WHERE("batch_no=#{batchNo}");
                }
                if (parameter.get("beginPhotoBeginTime") != null) {
                    WHERE("photo_begin_time>=#{beginPhotoBeginTime}");
                }

                if (parameter.get("endPhotoBeginTime") != null) {
                    WHERE("photo_begin_time<=#{endPhotoBeginTime}");
                }
                if (parameter.get("beginCallAiBeginTime") != null) {
                    WHERE("call_ai_begin_time>=#{beginCallAiBeginTime}");
                }

                if (parameter.get("endCallAiBeginTime") != null) {
                    WHERE("call_ai_begin_time<=#{endCallAiBeginTime}");
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

	public String getUpdateSql(TakePhotoRecord record) {

        return new SQL() {
			{
				UPDATE("t_take_photo_record");

                
                if (StringUtil.isNotBlank(record.getBatchNo())) {
                    SET("batch_no = #{batchNo}");
                }
                if (record.getPhotoBeginTime() != null) {
                    SET("photo_begin_time=#{photoBeginTime}");
                }
                if (record.getPhotoEndTime() != null) {
                    SET("photo_end_time=#{photoEndTime}");
                }
                if (record.getCallAiBeginTime() != null) {
                    SET("call_ai_begin_time=#{callAiBeginTime}");
                }
                if (record.getCallAiEndTime() != null) {
                    SET("call_ai_end_time=#{callAiEndTime}");
                }
                if (record.getCreateTime() != null) {
                    SET("create_time=#{createTime}");
                }
                if (record.getUpdateTime() != null) {
                    SET("update_time=#{updateTime}");
                }
                if (record.getState() != null) {
                    SET("state=#{state}");
                }
                WHERE("take_photo_id=#{takePhotoId}");
			}
		}.toString();

	}

}
