package com.aidolphin.ai.cotton.service;

import java.util.List;
import java.util.Map;

import com.aidolphin.ai.cotton.mapper.PointRecord;

public interface PointRecordService {

	public void addRecord(PointRecord record);

	public List<PointRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount);

	public void updateRecord(PointRecord record);

	public void deleteRecord(Long pointId);

	public int findRecordCount(Map<String, Object> whereParams);

	public PointRecord findRecordByKey(Long pointId);

}
