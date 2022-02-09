package com.aidolphin.ai.cotton.service;

import java.util.List;
import java.util.Map;

import com.aidolphin.ai.cotton.mapper.TakePhotoRecord;

public interface TakePhotoRecordService {

	public void addRecord(TakePhotoRecord record);

	public List<TakePhotoRecord> findRecordsByMap(Map<String, Object> whereParams, int beginIndex, int maxCount);

	public void updateRecord(TakePhotoRecord record);

	public void deleteRecord(Long takePhotoId);

	public int findRecordCount(Map<String, Object> whereParams);

	public TakePhotoRecord findRecordByKey(Long takePhotoId);

}
