package com.aidolphin.ai.cotton.service.impl;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.aidolphin.ai.cotton.mapper.ErrRecord;
import com.aidolphin.ai.cotton.mapper.ErrRecordMapper;
import com.aidolphin.ai.cotton.service.ErrRecordService;

@Service
public class ErrRecordServiceImpl implements ErrRecordService {
	@Autowired
	private ErrRecordMapper errRecordMapper;

	public void addRecord(ErrRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();

        record.setCreateTime(now);
        
        record.setUpdateTime(now);
        
		errRecordMapper.addRecord(record);
	}

	public List<ErrRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount) {
		if(whereParams==null){
			whereParams=new HashMap<String, Object>(0);
		}

		whereParams.put("beginIndex", beginIndex);
		whereParams.put("maxCount", maxCount);

		return errRecordMapper.findSelectRecordByMap(whereParams);
	}

	public void updateRecord(ErrRecord record) {
		if (record == null) {
			return;
		}

		Date now = new Date();


        record.setUpdateTime(now);
        
		errRecordMapper.updRecord(record);
	}

	public void deleteRecord(Long id) {
		if (id == null) {
			return;
		}

		errRecordMapper.delRecord(id);
	}

	public int findRecordCount(Map<String, Object> whereParams) {
		return errRecordMapper.findRecordsCount(whereParams);
	}

	public ErrRecord findRecordByKey(Long id) {
		if (id == null) {
			return null;
		}

		return errRecordMapper.findRecordByKey(id);
	}

}
