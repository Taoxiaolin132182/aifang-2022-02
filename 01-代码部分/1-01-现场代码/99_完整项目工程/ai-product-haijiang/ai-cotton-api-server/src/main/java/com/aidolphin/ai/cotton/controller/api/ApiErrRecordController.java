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
import com.aidolphin.ai.cotton.mapper.ErrRecord;
import com.aidolphin.ai.cotton.service.ErrRecordService;

@Controller
@Scope("singleton")
@RequestMapping("/api/db_cotton_local/errRecord")
public class ApiErrRecordController {
    private static final int DEFAULT_PAGE_SIZE = 25;

    @Autowired
    private ErrRecordService errRecordService;

    @RequestMapping(value = "/list")
    @ResponseBody
    public ResponseDataListTBase<ErrRecord> list(
      
            @RequestParam(value="id", required=false) Long id ,
            
      @RequestParam(value = "currentPage", required = true, defaultValue = "1") Integer currentPage,
      @RequestParam(value = "pageSize", required = false) Integer pageSize) {
      ResponseDataListTBase<ErrRecord> ret = new ResponseDataListTBase<ErrRecord>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if ((pageSize == null) || (pageSize <= 0)) {
        pageSize = DEFAULT_PAGE_SIZE;
      }

      // 查询参数
      Map<String, Object> whereParams = new HashMap<String, Object>(0);

      
        if (id != null) {
            whereParams.put("id", id);
        }
            
      int beginIndex = (currentPage - 1) * pageSize;
      List<ErrRecord> resultList = this.errRecordService.findRecordsByMap(whereParams, beginIndex, pageSize);
      ret.setData(resultList);
      return ret;
    }

    @RequestMapping(value = "/count")
    @ResponseBody
    public ResponseDataTBase<Integer> count(
      
            @RequestParam(value="id", required=false) Long id ,
                  @RequestParam(value = "currentPage", required = true, defaultValue = "1") Integer currentPage) {
      ResponseDataTBase<Integer> ret = new ResponseDataTBase<Integer>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      // 查询参数
      Map<String, Object> whereParams = new HashMap<String, Object>(0);

      
        if (id != null) {
            whereParams.put("id", id);
        }
                  int count = this.errRecordService.findRecordCount(whereParams);
      ret.setData(count);
      return ret;
    }

    @RequestMapping(value = "/detail")
    @ResponseBody
    public ResponseDataTBase<ErrRecord> detail(@RequestParam(value = "id", required = false) Long id) {
      ResponseDataTBase<ErrRecord> ret = new ResponseDataTBase<ErrRecord>(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      if (id == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  id!");
        return ret;
      }
      ErrRecord record = this.errRecordService.findRecordByKey(id);
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
    public ResponseBase add(ErrRecord record) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  id!");
        return ret;
      }

      this.errRecordService.addRecord(record);
      return ret;
    }

    @RequestMapping(value = "/upd")
    @ResponseBody
    public ResponseBase upd(ErrRecord record) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));

      if (record == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  id!");
        return ret;
      }

      if (record.getId() == null) {
        ret.setReturn_code(CommonErrorCodeConstants.ERR_CODE_LACK_PARAM);
        ret.setReturn_message("缺少参数:  id!");
        return ret;
      }

      this.errRecordService.updateRecord(record);
      return ret;
    }

    @RequestMapping(value = "/del")
    @ResponseBody
    public ResponseBase del(@RequestParam(value = "id", required = false) Long id) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      this.errRecordService.deleteRecord(id);
      return ret;
    }

    @RequestMapping(value = "/delRecords")
    @ResponseBody
    public ResponseBase delRecords(Long[] delIds, Model model) {
      ResponseBase ret = new ResponseBase(CommonErrorCodeConstants.ERR_CODE_SUCCESS, CommonErrorCodeConstants.MAP_ERR_CODE_MSG.get(CommonErrorCodeConstants.ERR_CODE_SUCCESS));
      if (delIds != null) {
        for (int i = 0; i < delIds.length; i++) {
          if (delIds[i] != null) {
            this.errRecordService.deleteRecord(delIds[i]);
          }
        }
      }
      return ret;
    }

}

