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

public interface PointRecordMapper {
	@Select("select * from t_point_record where point_id=#{pointId} limit 1 ")
	@Results(value={

        @Result(property="pointId", column="point_id")
    ,
        @Result(property="takePhotoId", column="take_photo_id")
    ,
        @Result(property="imageId", column="image_id")
    ,
        @Result(property="speed", column="speed")
    ,
        @Result(property="pointXmax", column="point_xmax")
    ,
        @Result(property="pointYmax", column="point_ymax")
    ,
        @Result(property="pointXmin", column="point_xmin")
    ,
        @Result(property="pointYmin", column="point_ymin")
    ,
        @Result(property="pointXcenter", column="point_xcenter")
    ,
        @Result(property="pointYcenter", column="point_ycenter")
    ,
        @Result(property="state", column="state")
    ,
        @Result(property="isDel", column="is_del")
    ,
        @Result(property="createTime", column="create_time")
    ,
        @Result(property="updateTime", column="update_time")
    	})
	public PointRecord findRecordByKey(@Param("pointId") Long pointId);

	@SelectProvider(method="getSelectRecordSql",type=PointRecordSqlProvider.class)
	@Results(value={

        @Result(property="pointId", column="point_id")
    ,
        @Result(property="takePhotoId", column="take_photo_id")
    ,
        @Result(property="imageId", column="image_id")
    ,
        @Result(property="speed", column="speed")
    ,
        @Result(property="pointXmax", column="point_xmax")
    ,
        @Result(property="pointYmax", column="point_ymax")
    ,
        @Result(property="pointXmin", column="point_xmin")
    ,
        @Result(property="pointYmin", column="point_ymin")
    ,
        @Result(property="pointXcenter", column="point_xcenter")
    ,
        @Result(property="pointYcenter", column="point_ycenter")
    ,
        @Result(property="state", column="state")
    ,
        @Result(property="isDel", column="is_del")
    ,
        @Result(property="createTime", column="create_time")
    ,
        @Result(property="updateTime", column="update_time")
    	})
	public List<PointRecord> findSelectRecordByMap(Map<String, Object> whereParams);

	@SelectProvider(type = PointRecordSqlProvider.class, method = "getSelectCountSql")
	public int findRecordsCount(Map<String, Object> whereParams);

	@Insert("INSERT INTO t_point_record  ( "
+ " take_photo_id ,  image_id ,  speed ,  point_xmax ,  point_ymax ,  point_xmin ,  point_ymin ,  point_xcenter ,  point_ycenter ,  state ,  is_del ,  create_time ,  update_time "			+ " )"
			+ " VALUES ( "
+ " #{takePhotoId} ,  #{imageId} ,  #{speed} ,  #{pointXmax} ,  #{pointYmax} ,  #{pointXmin} ,  #{pointYmin} ,  #{pointXcenter} ,  #{pointYcenter} ,  #{state} ,  #{isDel} ,  #{createTime} ,  #{updateTime} "			+ ")"
	)

    @Options(useGeneratedKeys = true, keyProperty = "pointId")
        	public void addRecord(PointRecord record);

	@UpdateProvider(type = PointRecordSqlProvider.class, method = "getUpdateSql")
	public void updRecord(PointRecord record);

	@Delete("delete from t_point_record where point_id=#{pointId}")
	public void delRecord(@Param("pointId") Long pointId);
}
