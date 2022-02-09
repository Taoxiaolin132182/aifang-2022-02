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

public interface TakePhotoRecordMapper {
	@Select("select * from t_take_photo_record where take_photo_id=#{takePhotoId} limit 1 ")
	@Results(value={

        @Result(property="takePhotoId", column="take_photo_id")
    ,
        @Result(property="batchNo", column="batch_no")
    ,
        @Result(property="photoBeginTime", column="photo_begin_time")
    ,
        @Result(property="photoEndTime", column="photo_end_time")
    ,
        @Result(property="callAiBeginTime", column="call_ai_begin_time")
    ,
        @Result(property="callAiEndTime", column="call_ai_end_time")
    ,
        @Result(property="createTime", column="create_time")
    ,
        @Result(property="updateTime", column="update_time")
    ,
        @Result(property="state", column="state")
    	})
	public TakePhotoRecord findRecordByKey(@Param("takePhotoId") Long takePhotoId);

	@SelectProvider(method="getSelectRecordSql",type=TakePhotoRecordSqlProvider.class)
	@Results(value={

        @Result(property="takePhotoId", column="take_photo_id")
    ,
        @Result(property="batchNo", column="batch_no")
    ,
        @Result(property="photoBeginTime", column="photo_begin_time")
    ,
        @Result(property="photoEndTime", column="photo_end_time")
    ,
        @Result(property="callAiBeginTime", column="call_ai_begin_time")
    ,
        @Result(property="callAiEndTime", column="call_ai_end_time")
    ,
        @Result(property="createTime", column="create_time")
    ,
        @Result(property="updateTime", column="update_time")
    ,
        @Result(property="state", column="state")
    	})
	public List<TakePhotoRecord> findSelectRecordByMap(Map<String, Object> whereParams);

	@SelectProvider(type = TakePhotoRecordSqlProvider.class, method = "getSelectCountSql")
	public int findRecordsCount(Map<String, Object> whereParams);

	@Insert("INSERT INTO t_take_photo_record  ( "
+ " batch_no ,  photo_begin_time ,  photo_end_time ,  call_ai_begin_time ,  call_ai_end_time ,  create_time ,  update_time ,  state "			+ " )"
			+ " VALUES ( "
+ " #{batchNo} ,  #{photoBeginTime} ,  #{photoEndTime} ,  #{callAiBeginTime} ,  #{callAiEndTime} ,  #{createTime} ,  #{updateTime} ,  #{state} "			+ ")"
	)

    @Options(useGeneratedKeys = true, keyProperty = "takePhotoId")
        	public void addRecord(TakePhotoRecord record);

	@UpdateProvider(type = TakePhotoRecordSqlProvider.class, method = "getUpdateSql")
	public void updRecord(TakePhotoRecord record);

	@Delete("delete from t_take_photo_record where take_photo_id=#{takePhotoId}")
	public void delRecord(@Param("takePhotoId") Long takePhotoId);
}
