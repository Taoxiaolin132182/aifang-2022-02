package com.aidolphin.ai.cotton.mapper;

import java.util.Map;

import org.apache.ibatis.jdbc.SQL;

import com.gmm.common.StringUtil;

public class ErrRecordSqlProvider {
	public String getSelectRecordSql(Map<String, Object> parameter) {

        return new SQL() {
			{
				SELECT("*");
				FROM("t_err_record");
                
                if (parameter.get("id") != null) {
                    WHERE("id=#{id}");
                }
                ORDER_BY("id desc");
                        
			}
		}.toString() + " limit #{beginIndex}, #{maxCount}";

	}

	public String getSelectCountSql(Map<String, Object> parameter) {

        return new SQL() {
			{
				SELECT("count(*)");
				FROM("t_err_record");
                
                if (parameter.get("id") != null) {
                    WHERE("id=#{id}");
                }
			}
		}.toString();

	}

	public String getUpdateSql(ErrRecord record) {

        return new SQL() {
			{
				UPDATE("t_err_record");

                
                if (record.getErrCode() != null) {
                    SET("err_code=#{errCode}");
                }
                if (record.getErrTime() != null) {
                    SET("err_time=#{errTime}");
                }
                if (record.getCreateTime() != null) {
                    SET("create_time=#{createTime}");
                }
                if (record.getUpdateTime() != null) {
                    SET("update_time=#{updateTime}");
                }
                if (StringUtil.isNotBlank(record.getErrInstructions())) {
                    SET("err_instructions = #{errInstructions}");
                }
                WHERE("id=#{id}");
			}
		}.toString();

	}

}
