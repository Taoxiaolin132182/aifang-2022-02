package com.aidolphin.ai.cotton.service.impl;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.aidolphin.ai.cotton.mapper.ImageRecord;
import com.aidolphin.ai.cotton.mapper.ImageRecordMapper;
import com.aidolphin.ai.cotton.service.ImageRecordService;

@Service
public class ImageRecordServiceImpl implements ImageRecordService {
	@Autowired
	private ImageRecordMapper imageRecordMapper;

	public void addRecord(ImageRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();

        record.setCreateTime(now);
        
        record.setUpdateTime(now);
        
		imageRecordMapper.addRecord(record);
	}

	public List<ImageRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount) {
		if(whereParams==null){
			whereParams=new HashMap<String, Object>(0);
		}

		whereParams.put("beginIndex", beginIndex);
		whereParams.put("maxCount", maxCount);

		return imageRecordMapper.findSelectRecordByMap(whereParams);
	}

	public void updateRecord(ImageRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();


        record.setUpdateTime(now);
        
		imageRecordMapper.updRecord(record);
	}

	public void deleteRecord(Long imageId) {
		if (imageId == null) {
			return;
		}

		imageRecordMapper.delRecord(imageId);
	}

	public int findRecordCount(Map<String, Object> whereParams) {
		return imageRecordMapper.findRecordsCount(whereParams);
	}

	public ImageRecord findRecordByKey(Long imageId) {
		if (imageId == null) {
			return null;
		}

		return imageRecordMapper.findRecordByKey(imageId);
	}

}
