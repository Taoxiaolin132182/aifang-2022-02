package com.aidolphin.ai.cotton.service.impl;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.aidolphin.ai.cotton.mapper.TakePhotoRecord;
import com.aidolphin.ai.cotton.mapper.TakePhotoRecordMapper;
import com.aidolphin.ai.cotton.service.TakePhotoRecordService;

@Service
public class TakePhotoRecordServiceImpl implements TakePhotoRecordService {
	@Autowired
	private TakePhotoRecordMapper takePhotoRecordMapper;

	public void addRecord(TakePhotoRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();

        record.setCreateTime(now);
        
        record.setUpdateTime(now);
        
		takePhotoRecordMapper.addRecord(record);
	}

	public List<TakePhotoRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount) {
		if(whereParams==null){
			whereParams=new HashMap<String, Object>(0);
		}

		whereParams.put("beginIndex", beginIndex);
		whereParams.put("maxCount", maxCount);

		return takePhotoRecordMapper.findSelectRecordByMap(whereParams);
	}

	public void updateRecord(TakePhotoRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();


        record.setUpdateTime(now);
        
		takePhotoRecordMapper.updRecord(record);
	}

	public void deleteRecord(Long takePhotoId) {
		if (takePhotoId == null) {
			return;
		}

		takePhotoRecordMapper.delRecord(takePhotoId);
	}

	public int findRecordCount(Map<String, Object> whereParams) {
		return takePhotoRecordMapper.findRecordsCount(whereParams);
	}

	public TakePhotoRecord findRecordByKey(Long takePhotoId) {
		if (takePhotoId == null) {
			return null;
		}

		return takePhotoRecordMapper.findRecordByKey(takePhotoId);
	}

}
