package com.aidolphin.ai.cotton.controller.api;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Scope;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import com.gmm.common.StringUtil;
import com.gmm.common.api.ResponseBase;
import com.gmm.common.api.ResponseDataListTBase;
import com.gmm.common.api.ResponseDataTBase;
import com.gmm.common.constants.CommonErrorCodeConstants;
import com.aidolphin.ai.cotton.mapper.PointRecord;
import com.aidolphin.ai.cotton.service.PointRecordService;

@Controller
@Scope("singleton")
@RequestMapping("/api/db_cotton_local/pointRecord")
public class ApiPointRecordController {
    private static final int DEFAULT_PAGE_SIZE = 25;

    @Autowired
    private PointRecordService pointRecordService;

    @RequestMapping(value = "/list")
    @ResponseBody
    public ResponseDataListTBase<PointRecord> list(
      
            @RequestParam(value="pointId", required=false) Long pointId ,
            
            @RequestParam(value="takePhotoId", required=false) Long takePhotoId ,
            
            @RequestParam(value="imageId", required=false) Long imageId ,
            
            @RequestParam(value="state", required=false) Integer state ,
            
            @RequestParam(value="beginCreateTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginCreateTime ,
            
            @RequestParam(value="endCreateTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endCreateTime ,
            
      @RequestParam(value = "currentPage", required = true, defaultValue = "1") Integer currentPage,
      @RequestParam(value = "pageSize", required = false) Integer pageSize) {
      ResponseDataListTBase<PointRecord> ret = new ResponseDataListTBase<PointRecord>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if ((pageSize == null) || (pageSize <= 0)) {
        pageSize = DEFAULT_PAGE_SIZE;
      }

      // 查询参数
      Map<String, Object> whereParams = new HashMap<String, Object>(0);

      
        if (pointId != null) {
            whereParams.put("pointId", pointId);
        }
            
        if (takePhotoId != null) {
            whereParams.put("takePhotoId", takePhotoId);
        }
            
        if (imageId != null) {
            whereParams.put("imageId", imageId);
        }
            
        if (state != null) {
            whereParams.put("state", state);
        }
            
        if (beginCreateTime != null) {
            whereParams.put("beginCreateTime", beginCreateTime);
        }

        if (endCreateTime != null) {
            whereParams.put("endCreateTime", endCreateTime);
        }
            
      int beginIndex = (currentPage - 1) * pageSize;
      List<PointRecord> resultList = this.pointRecordService.findRecordsByMap(whereParams, beginIndex, pageSize);
      ret.setData(resultList);
      return ret;
    }

    @RequestMapping(value = "/count")
    @ResponseBody
    public ResponseDataTBase<Integer> count(
      
            @RequestParam(value="pointId", required=false) Long pointId ,
            
            @RequestParam(value="takePhotoId", required=false) Long takePhotoId ,
            
            @RequestParam(value="imageId", required=false) Long imageId ,
            
            @RequestParam(value="state", required=false) Integer state ,
            
            @RequestParam(value="beginCreateTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginCreateTime ,
            
            @RequestParam(value="endCreateTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endCreateTime ,
                  @RequestParam(value = "currentPage", required = true, defaultValue = "1") Integer currentPage) {
      ResponseDataTBase<Integer> ret = new ResponseDataTBase<Integer>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      // 查询参数
      Map<String, Object> whereParams = new HashMap<String, Object>(0);

      
        if (pointId != null) {
            whereParams.put("pointId", pointId);
        }
            
        if (takePhotoId != null) {
            whereParams.put("takePhotoId", takePhotoId);
        }
            
        if (imageId != null) {
            whereParams.put("imageId", imageId);
        }
            
        if (state != null) {
            whereParams.put("state", state);
        }
            
        if (beginCreateTime != null) {
            whereParams.put("beginCreateTime", beginCreateTime);
        }

        if (endCreateTime != null) {
            whereParams.put("endCreateTime", endCreateTime);
        }
                  int count = this.pointRecordService.findRecordCount(whereParams);
      ret.setData(count);
      return ret;
    }

    @RequestMapping(value = "/detail")
    @ResponseBody
    public ResponseDataTBase<PointRecord> detail(@RequestParam(value = "pointId", required = false) Long pointId) {
      ResponseDataTBase<PointRecord> ret = new ResponseDataTBase<PointRecord>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      if (pointId == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  pointId!");
        return ret;
      }
      PointRecord record = this.pointRecordService.findRecordByKey(pointId);
      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_RECORD_NOT_EXIST);
        ret.setReturn_message(CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_RECORD_NOT_EXIST));
        return ret;
      }

      ret.setData(record);

      return ret;
    }

    @RequestMapping(value = "/add")
    @ResponseBody
    public ResponseBase add(PointRecord record) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  pointId!");
        return ret;
      }

      this.pointRecordService.addRecord(record);
      return ret;
    }

    @RequestMapping(value = "/upd")
    @ResponseBody
    public ResponseBase upd(PointRecord record) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  pointId!");
        return ret;
      }

      if (record.getPointId() == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  pointId!");
        return ret;
      }

      this.pointRecordService.updateRecord(record);
      return ret;
    }

    @RequestMapping(value = "/del")
    @ResponseBody
    public ResponseBase del(@RequestParam(value = "pointId", required = false) Long pointId) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      this.pointRecordService.deleteRecord(pointId);
      return ret;
    }

    @RequestMapping(value = "/delRecords")
    @ResponseBody
    public ResponseBase delRecords(Long[] delIds, Model model) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      if (delIds != null) {
        for (int i = 0; i < delIds.length; i++) {
          if (delIds[i] != null) {
            this.pointRecordService.deleteRecord(delIds[i]);
          }
        }
      }
      return ret;
    }

}

