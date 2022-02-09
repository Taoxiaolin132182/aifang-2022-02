package com.aidolphin.ai.cotton.controller.bs;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Scope;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.ui.ModelMap;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.gmm.common.web.ExportCsvUtil;
import com.gmm.common.web.PageData;
import com.gmm.common.StringUtil;
import com.aidolphin.ai.cotton.mapper.PointRecord;
import com.aidolphin.ai.cotton.service.PointRecordService;

@Controller
@Scope("singleton")
@RequestMapping("/bs/pointRecord")
public class PointRecordController {
//	private static final Logger LOGGER = LoggerFactory.getLogger(UserInfoController.class);

    private static final int DEFAULT_PAGE_SIZE = 25;
    private static final int EXPORT_RECORD_MAX_SIZE = 50000;

    @Autowired
    private PointRecordService pointRecordService;

    @RequestMapping(value = "/list")
    public String list(
        
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
			@RequestParam(value = "pageSize", required = false) Integer pageSize,
            ModelMap model) {
		PageData<PointRecord> pageData = new PageData<PointRecord>();
		pageData.setCurrentPage(currentPage);
		if ((pageSize == null) || (pageSize <= 0)) {
			pageSize = DEFAULT_PAGE_SIZE;
		}
		pageData.setPageSize(pageSize);

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
		pageData.setTotalCount(count);

		int beginIndex = (currentPage - 1) * pageSize;
		List<PointRecord> resultList = this.pointRecordService.findRecordsByMap(whereParams, beginIndex, pageSize);
		pageData.setResultList(resultList);
        
        model.addAttribute("pointId", pointId);
            
        model.addAttribute("takePhotoId", takePhotoId);
            
        model.addAttribute("imageId", imageId);
            
        model.addAttribute("state", state);
            
        if (beginCreateTime != null) {
            model.addAttribute("beginCreateTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(beginCreateTime));
        }

        if (endCreateTime != null) {
            model.addAttribute("endCreateTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(endCreateTime));
        }
                    model.addAttribute("pageData", pageData);

		return "/bs/pointRecord/list";
	}




	@RequestMapping(value = "/countByTime")
	public String countByTime(
			@RequestParam(value="beginCreateTime", required=false)
			@DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
					Date beginCreateTime ,

			@RequestParam(value="endCreateTime", required=false)
			@DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
					Date endCreateTime ,
			ModelMap model) {
		// 查询参数
		Map<String, Object> whereParams = new HashMap<String, Object>(0);
		int countAll = 0;
		int countSuccess = 0;
		int countFail = 0;

		if (beginCreateTime != null) {
			whereParams.put("beginCreateTime", beginCreateTime);
		}

		if (endCreateTime != null) {
			whereParams.put("endCreateTime", endCreateTime);
		}

		if (beginCreateTime !=null && endCreateTime !=null){
			countAll = this.pointRecordService.findRecordCount(whereParams);
			whereParams.put("state",4);
			countSuccess = this.pointRecordService.findRecordCount(whereParams);
			whereParams.put("state",5);
			countFail = this.pointRecordService.findRecordCount(whereParams);
		}

		model.addAttribute("countAll", countAll);

		model.addAttribute("countSuccess", countSuccess);

		model.addAttribute("countFail", countFail);

		if (beginCreateTime != null) {
			model.addAttribute("beginCreateTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(beginCreateTime));
		}

		if (endCreateTime != null) {
			model.addAttribute("endCreateTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(endCreateTime));
		}
		return "/bs/pointRecord/countByTime";
	}

    @RequestMapping(value = "/show")
	public String show(@RequestParam(value = "pointId", required = true) Long pointId, Model model) {
		if (pointId == null) {
			return "/common/error";
		}
		PointRecord record = this.pointRecordService.findRecordByKey(pointId);
		model.addAttribute("record", record);
		if (record == null) {
			model.addAttribute("errMsg", "未查到到记录");
			return "/common/error";
		}
		return "/bs/pointRecord/show";
	}

    @RequestMapping(value = "/showAdd")
	public String showAdd(@RequestParam(value = "pointId", required = false)
	Long pointId, Model model) {
		PointRecord record = null;
		if (pointId != null) {
			record = this.pointRecordService.findRecordByKey(pointId);
		}

		if (record == null) {
			record = new PointRecord();
		}

		model.addAttribute("record", record);
		return "/bs/pointRecord/showAdd";
	}

    @RequestMapping(value = "/add")
	public String add(@Valid PointRecord record, BindingResult result, Model model) {
		this.pointRecordService.addRecord(record);
		return "redirect:/bs/pointRecord/show?pointId=" + record.getPointId();
	}


    @RequestMapping(value = "/showUpd")
	public String showUpd(@RequestParam(value = "pointId", required = true)
	Long pointId,
    Model model) {
		if (pointId == null) {
			return "/common/error";
		}
		PointRecord record = this.pointRecordService.findRecordByKey(pointId);
		if (record == null) {
			model.addAttribute("errMsg", "未查到到记录");
			return "/common/error";
		}
		model.addAttribute("record", record);
		return "/bs/pointRecord/showUpd";
	}

	@RequestMapping(value = "/upd")
	public String upd(@Valid PointRecord record, BindingResult result, Model model) {
		if (result.hasErrors()) {
			model.addAttribute("record", record);
			return "/bs/pointRecord/showUpd";
		}

		this.pointRecordService.updateRecord(record);
		return "redirect:/bs/pointRecord/show?pointId=" + record.getPointId();
	}

    @RequestMapping(value = "/del")
	public String del(@RequestParam(value = "pointId", required = true, defaultValue = "0") Long pointId,
			Model model) {
		this.pointRecordService.deleteRecord(pointId);
		return "/bs/pointRecord/delOk";
	}

	@RequestMapping(value = "/delRecords")
	public String delRecords(Long[] delIds, Model model) {
		if (delIds != null) {
			for (int i = 0; i < delIds.length; i++) {
				if (delIds[i] != null) {
					this.pointRecordService.deleteRecord(delIds[i]);
				}
			}
		}
		return "redirect:/bs/pointRecord/list";
	}

}