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

public interface ImageRecordMapper {
	@Select("select * from t_image_record where image_id=#{imageId} limit 1 ")
	@Results(value={

        @Result(property="imageId", column="image_id")
    ,
        @Result(property="takePhotoId", column="take_photo_id")
    ,
        @Result(property="imagePath", column="image_path")
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
	public ImageRecord findRecordByKey(@Param("imageId") Long imageId);

	@SelectProvider(method="getSelectRecordSql",type=ImageRecordSqlProvider.class)
	@Results(value={

        @Result(property="imageId", column="image_id")
    ,
        @Result(property="takePhotoId", column="take_photo_id")
    ,
        @Result(property="imagePath", column="image_path")
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
	public List<ImageRecord> findSelectRecordByMap(Map<String, Object> whereParams);

	@SelectProvider(type = ImageRecordSqlProvider.class, method = "getSelectCountSql")
	public int findRecordsCount(Map<String, Object> whereParams);

	@Insert("INSERT INTO t_image_record  ( "
+ " take_photo_id ,  image_path ,  photo_begin_time ,  photo_end_time ,  call_ai_begin_time ,  call_ai_end_time ,  create_time ,  update_time ,  state "			+ " )"
			+ " VALUES ( "
+ " #{takePhotoId} ,  #{imagePath} ,  #{photoBeginTime} ,  #{photoEndTime} ,  #{callAiBeginTime} ,  #{callAiEndTime} ,  #{createTime} ,  #{updateTime} ,  #{state} "			+ ")"
	)

    @Options(useGeneratedKeys = true, keyProperty = "imageId")
        	public void addRecord(ImageRecord record);

	@UpdateProvider(type = ImageRecordSqlProvider.class, method = "getUpdateSql")
	public void updRecord(ImageRecord record);

	@Delete("delete from t_image_record where image_id=#{imageId}")
	public void delRecord(@Param("imageId") Long imageId);
}
