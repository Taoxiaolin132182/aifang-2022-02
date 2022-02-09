package com.aidolphin.ai.cotton.service;

import java.util.List;
import java.util.Map;

import com.aidolphin.ai.cotton.mapper.ErrRecord;

public interface ErrRecordService {

	public void addRecord(ErrRecord record);

	public List<ErrRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount);

	public void updateRecord(ErrRecord record);

	public void deleteRecord(Long id);

	public int findRecordCount(Map<String, Object> whereParams);

	public ErrRecord findRecordByKey(Long id);

}
