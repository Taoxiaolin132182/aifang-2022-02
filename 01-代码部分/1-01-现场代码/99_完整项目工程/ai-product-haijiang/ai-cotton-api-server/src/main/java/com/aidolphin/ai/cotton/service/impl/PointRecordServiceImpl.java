package com.aidolphin.ai.cotton.service.impl;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.aidolphin.ai.cotton.mapper.PointRecord;
import com.aidolphin.ai.cotton.mapper.PointRecordMapper;
import com.aidolphin.ai.cotton.service.PointRecordService;

@Service
public class PointRecordServiceImpl implements PointRecordService {
	@Autowired
	private PointRecordMapper pointRecordMapper;

	public void addRecord(PointRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();

        record.setCreateTime(now);
        
        record.setUpdateTime(now);
        
		pointRecordMapper.addRecord(record);
	}

	public List<PointRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount) {
		if(whereParams==null){
			whereParams=new HashMap<String, Object>(0);
		}

		whereParams.put("beginIndex", beginIndex);
		whereParams.put("maxCount", maxCount);

		return pointRecordMapper.findSelectRecordByMap(whereParams);
	}

	public void updateRecord(PointRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();


        record.setUpdateTime(now);
        
		pointRecordMapper.updRecord(record);
	}

	public void deleteRecord(Long pointId) {
		if (pointId == null) {
			return;
		}

		pointRecordMapper.delRecord(pointId);
	}

	public int findRecordCount(Map<String, Object> whereParams) {
		return pointRecordMapper.findRecordsCount(whereParams);
	}

	public PointRecord findRecordByKey(Long pointId) {
		if (pointId == null) {
			return null;
		}

		return pointRecordMapper.findRecordByKey(pointId);
	}

}
