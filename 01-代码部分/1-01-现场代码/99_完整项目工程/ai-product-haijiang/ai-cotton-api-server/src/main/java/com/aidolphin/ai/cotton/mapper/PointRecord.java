package com.aidolphin.ai.cotton.mapper;

import java.io.Serializable;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.format.annotation.DateTimeFormat;

import com.fasterxml.jackson.annotation.JsonFormat;

import com.gmm.common.StringUtil;

public class PointRecord implements Serializable {
	private static final long serialVersionUID = 1L;

	private static Log LOGGER = LogFactory.getLog(PointRecord.class);


    private Long pointId;
    
    private Long takePhotoId;
    
    private Long imageId;
    
    private String speed;
    
    private Integer pointXmax;
    
    private Integer pointYmax;
    
    private Integer pointXmin;
    
    private Integer pointYmin;
    
    private Integer pointXcenter;
    
    private Integer pointYcenter;
    
    private Integer state;
    
    private Integer isDel;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date createTime;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date updateTime;
    
    public Long getPointId() {
		return pointId;
	}

	public void setPointId(Long pointId) {
		this.pointId = pointId;
	}
    
    public Long getTakePhotoId() {
		return takePhotoId;
	}

	public void setTakePhotoId(Long takePhotoId) {
		this.takePhotoId = takePhotoId;
	}
    
    public Long getImageId() {
		return imageId;
	}

	public void setImageId(Long imageId) {
		this.imageId = imageId;
	}
    
    public String getSpeed() {
		return speed;
	}

	public void setSpeed(String speed) {
		this.speed = speed;
	}
    
    public Integer getPointXmax() {
		return pointXmax;
	}

	public void setPointXmax(Integer pointXmax) {
		this.pointXmax = pointXmax;
	}
    
    public Integer getPointYmax() {
		return pointYmax;
	}

	public void setPointYmax(Integer pointYmax) {
		this.pointYmax = pointYmax;
	}
    
    public Integer getPointXmin() {
		return pointXmin;
	}

	public void setPointXmin(Integer pointXmin) {
		this.pointXmin = pointXmin;
	}
    
    public Integer getPointYmin() {
		return pointYmin;
	}

	public void setPointYmin(Integer pointYmin) {
		this.pointYmin = pointYmin;
	}
    
    public Integer getPointXcenter() {
		return pointXcenter;
	}

	public void setPointXcenter(Integer pointXcenter) {
		this.pointXcenter = pointXcenter;
	}
    
    public Integer getPointYcenter() {
		return pointYcenter;
	}

	public void setPointYcenter(Integer pointYcenter) {
		this.pointYcenter = pointYcenter;
	}
    
    public Integer getState() {
		return state;
	}

	public void setState(Integer state) {
		this.state = state;
	}
    
    public Integer getIsDel() {
		return isDel;
	}

	public void setIsDel(Integer isDel) {
		this.isDel = isDel;
	}
    
    public Date getCreateTime() {
		return createTime;
	}

	public void setCreateTime(Date createTime) {
		this.createTime = createTime;
	}
    
    public Date getUpdateTime() {
		return updateTime;
	}

	public void setUpdateTime(Date updateTime) {
		this.updateTime = updateTime;
	}
    
}
