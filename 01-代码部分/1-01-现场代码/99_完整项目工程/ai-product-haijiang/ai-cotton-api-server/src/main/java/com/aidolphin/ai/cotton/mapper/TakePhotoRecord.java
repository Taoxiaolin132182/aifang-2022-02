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

public class TakePhotoRecord implements Serializable {
	private static final long serialVersionUID = 1L;

	private static Log LOGGER = LogFactory.getLog(TakePhotoRecord.class);


    private Long takePhotoId;
    
    private String batchNo;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date photoBeginTime;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date photoEndTime;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date callAiBeginTime;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date callAiEndTime;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date createTime;
    
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
            
    private Date updateTime;
    
    private Integer state;
    
    public Long getTakePhotoId() {
		return takePhotoId;
	}

	public void setTakePhotoId(Long takePhotoId) {
		this.takePhotoId = takePhotoId;
	}
    
    public String getBatchNo() {
		return batchNo;
	}

	public void setBatchNo(String batchNo) {
		this.batchNo = batchNo;
	}
    
    public Date getPhotoBeginTime() {
		return photoBeginTime;
	}

	public void setPhotoBeginTime(Date photoBeginTime) {
		this.photoBeginTime = photoBeginTime;
	}
    
    public Date getPhotoEndTime() {
		return photoEndTime;
	}

	public void setPhotoEndTime(Date photoEndTime) {
		this.photoEndTime = photoEndTime;
	}
    
    public Date getCallAiBeginTime() {
		return callAiBeginTime;
	}

	public void setCallAiBeginTime(Date callAiBeginTime) {
		this.callAiBeginTime = callAiBeginTime;
	}
    
    public Date getCallAiEndTime() {
		return callAiEndTime;
	}

	public void setCallAiEndTime(Date callAiEndTime) {
		this.callAiEndTime = callAiEndTime;
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
    
    public Integer getState() {
		return state;
	}

	public void setState(Integer state) {
		this.state = state;
	}
    
}
