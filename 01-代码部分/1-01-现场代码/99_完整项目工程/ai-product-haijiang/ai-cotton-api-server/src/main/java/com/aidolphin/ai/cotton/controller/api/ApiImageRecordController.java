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
import com.aidolphin.ai.cotton.mapper.ImageRecord;
import com.aidolphin.ai.cotton.service.ImageRecordService;

@Controller
@Scope("singleton")
@RequestMapping("/api/db_cotton_local/imageRecord")
public class ApiImageRecordController {
    private static final int DEFAULT_PAGE_SIZE = 25;

    @Autowired
    private ImageRecordService imageRecordService;

    @RequestMapping(value = "/list")
    @ResponseBody
    public ResponseDataListTBase<ImageRecord> list(
      
            @RequestParam(value="imageId", required=false) Long imageId ,
            
            @RequestParam(value="takePhotoId", required=false) Long takePhotoId ,
            
            @RequestParam(value="beginPhotoBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginPhotoBeginTime ,
            
            @RequestParam(value="endPhotoBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endPhotoBeginTime ,
            
            @RequestParam(value="beginCallAiBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginCallAiBeginTime ,
            
            @RequestParam(value="endCallAiBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endCallAiBeginTime ,
            
            @RequestParam(value="beginCreateTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginCreateTime ,
            
            @RequestParam(value="endCreateTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endCreateTime ,
            
      @RequestParam(value = "currentPage", required = true, defaultValue = "1") Integer currentPage,
      @RequestParam(value = "pageSize", required = false) Integer pageSize) {
      ResponseDataListTBase<ImageRecord> ret = new ResponseDataListTBase<ImageRecord>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if ((pageSize == null) || (pageSize <= 0)) {
        pageSize = DEFAULT_PAGE_SIZE;
      }

      // 查询参数
      Map<String, Object> whereParams = new HashMap<String, Object>(0);

      
        if (imageId != null) {
            whereParams.put("imageId", imageId);
        }
            
        if (takePhotoId != null) {
            whereParams.put("takePhotoId", takePhotoId);
        }
            
        if (beginPhotoBeginTime != null) {
            whereParams.put("beginPhotoBeginTime", beginPhotoBeginTime);
        }

        if (endPhotoBeginTime != null) {
            whereParams.put("endPhotoBeginTime", endPhotoBeginTime);
        }
            
        if (beginCallAiBeginTime != null) {
            whereParams.put("beginCallAiBeginTime", beginCallAiBeginTime);
        }

        if (endCallAiBeginTime != null) {
            whereParams.put("endCallAiBeginTime", endCallAiBeginTime);
        }
            
        if (beginCreateTime != null) {
            whereParams.put("beginCreateTime", beginCreateTime);
        }

        if (endCreateTime != null) {
            whereParams.put("endCreateTime", endCreateTime);
        }
            
      int beginIndex = (currentPage - 1) * pageSize;
      List<ImageRecord> resultList = this.imageRecordService.findRecordsByMap(whereParams, beginIndex, pageSize);
      ret.setData(resultList);
      return ret;
    }

    @RequestMapping(value = "/count")
    @ResponseBody
    public ResponseDataTBase<Integer> count(
      
            @RequestParam(value="imageId", required=false) Long imageId ,
            
            @RequestParam(value="takePhotoId", required=false) Long takePhotoId ,
            
            @RequestParam(value="beginPhotoBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginPhotoBeginTime ,
            
            @RequestParam(value="endPhotoBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endPhotoBeginTime ,
            
            @RequestParam(value="beginCallAiBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date beginCallAiBeginTime ,
            
            @RequestParam(value="endCallAiBeginTime", required=false)
             @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") 
                Date endCallAiBeginTime ,
            
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

      
        if (imageId != null) {
            whereParams.put("imageId", imageId);
        }
            
        if (takePhotoId != null) {
            whereParams.put("takePhotoId", takePhotoId);
        }
            
        if (beginPhotoBeginTime != null) {
            whereParams.put("beginPhotoBeginTime", beginPhotoBeginTime);
        }

        if (endPhotoBeginTime != null) {
            whereParams.put("endPhotoBeginTime", endPhotoBeginTime);
        }
            
        if (beginCallAiBeginTime != null) {
            whereParams.put("beginCallAiBeginTime", beginCallAiBeginTime);
        }

        if (endCallAiBeginTime != null) {
            whereParams.put("endCallAiBeginTime", endCallAiBeginTime);
        }
            
        if (beginCreateTime != null) {
            whereParams.put("beginCreateTime", beginCreateTime);
        }

        if (endCreateTime != null) {
            whereParams.put("endCreateTime", endCreateTime);
        }
                  int count = this.imageRecordService.findRecordCount(whereParams);
      ret.setData(count);
      return ret;
    }

    @RequestMapping(value = "/detail")
    @ResponseBody
    public ResponseDataTBase<ImageRecord> detail(@RequestParam(value = "imageId", required = false) Long imageId) {
      ResponseDataTBase<ImageRecord> ret = new ResponseDataTBase<ImageRecord>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      if (imageId == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  imageId!");
        return ret;
      }
      ImageRecord record = this.imageRecordService.findRecordByKey(imageId);
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
    public ResponseBase add(ImageRecord record) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  imageId!");
        return ret;
      }

      this.imageRecordService.addRecord(record);
      return ret;
    }

    @RequestMapping(value = "/upd")
    @ResponseBody
    public ResponseBase upd(ImageRecord record) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  imageId!");
        return ret;
      }

      if (record.getImageId() == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  imageId!");
        return ret;
      }

      this.imageRecordService.updateRecord(record);
      return ret;
    }

    @RequestMapping(value = "/del")
    @ResponseBody
    public ResponseBase del(@RequestParam(value = "imageId", required = false) Long imageId) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      this.imageRecordService.deleteRecord(imageId);
      return ret;
    }

    @RequestMapping(value = "/delRecords")
    @ResponseBody
    public ResponseBase delRecords(Long[] delIds, Model model) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      if (delIds != null) {
        for (int i = 0; i < delIds.length; i++) {
          if (delIds[i] != null) {
            this.imageRecordService.deleteRecord(delIds[i]);
          }
        }
      }
      return ret;
    }

}

