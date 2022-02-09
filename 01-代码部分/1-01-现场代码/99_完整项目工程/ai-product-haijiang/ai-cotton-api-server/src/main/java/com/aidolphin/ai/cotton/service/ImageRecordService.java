package com.aidolphin.ai.cotton.service;

import java.util.List;
import java.util.Map;

import com.aidolphin.ai.cotton.mapper.ImageRecord;

public interface ImageRecordService {

	public void addRecord(ImageRecord record);

	public List<ImageRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount);

	public void updateRecord(ImageRecord record);

	public void deleteRecord(Long imageId);

	public int findRecordCount(Map<String, Object> whereParams);

	public ImageRecord findRecordByKey(Long imageId);

}
