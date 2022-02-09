package com.aidolphin.ai.cotton.mapper;

import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Result;
import org.apache.ibatis.annotations.Results;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.SelectProvider;
import org.apache.ibatis.annotations.UpdateProvider;

public interface ErrRecordMapper {
	@Select("select * from t_err_record where id=#{id} limit 1 ")
	@Results(value={

        @Result(property="id", column="id")
    ,
        @Result(property="errCode", column="err_code")
    ,
        @Result(property="errTime", column="err_time")
    ,
        @Result(property="createTime", column="create_time")
    ,
        @Result(property="updateTime", column="update_time")
    ,
        @Result(property="errInstructions", column="err_instructions")
    	})
	public ErrRecord findRecordByKey(@Param("id") Long id);

	@SelectProvider(method="getSelectRecordSql",type=ErrRecordSqlProvider.class)
	@Results(value={

        @Result(property="id", column="id")
    ,
        @Result(property="errCode", column="err_code")
    ,
        @Result(property="errTime", column="err_time")
    ,
        @Result(property="createTime", column="create_time")
    ,
        @Result(property="updateTime", column="update_time")
    ,
        @Result(property="errInstructions", column="err_instructions")
    	})
	public List<ErrRecord> findSelectRecordByMap(Map<String, Object> whereParams);

	@SelectProvider(type = ErrRecordSqlProvider.class, method = "getSelectCountSql")
	public int findRecordsCount(Map<String, Object> whereParams);

	@Insert("INSERT INTO t_err_record  ( "
+ " err_code ,  err_time ,  create_time ,  update_time ,  err_instructions "			+ " )"
			+ " VALUES ( "
+ " #{errCode} ,  #{errTime} ,  #{createTime} ,  #{updateTime} ,  #{errInstructions} "			+ ")"
	)

    @Options(useGeneratedKeys = true, keyProperty = "id")
        	public void addRecord(ErrRecord record);

	@UpdateProvider(type = ErrRecordSqlProvider.class, method = "getUpdateSql")
	public void updRecord(ErrRecord record);

	@Delete("delete from t_err_record where id=#{id}")
	public void delRecord(@Param("id") Long id);
}
