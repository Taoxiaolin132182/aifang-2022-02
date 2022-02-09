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
import com.aidolphin.ai.cotton.mapper.ImageRecord;
import com.aidolphin.ai.cotton.service.ImageRecordService;

@Controller
@Scope("singleton")
@RequestMapping("/bs/imageRecord")
public class ImageRecordController {
//	private static final Logger LOGGER = LoggerFactory.getLogger(UserInfoController.class);

    private static final int DEFAULT_PAGE_SIZE = 25;
    private static final int EXPORT_RECORD_MAX_SIZE = 50000;

    @Autowired
    private ImageRecordService imageRecordService;

    @RequestMapping(value = "/list")
    public String list(
        
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
			@RequestParam(value = "pageSize", required = false) Integer pageSize,
            ModelMap model) {
		PageData<ImageRecord> pageData = new PageData<ImageRecord>();
		pageData.setCurrentPage(currentPage);
		if ((pageSize == null) || (pageSize <= 0)) {
			pageSize = DEFAULT_PAGE_SIZE;
		}
		pageData.setPageSize(pageSize);

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
		pageData.setTotalCount(count);

		int beginIndex = (currentPage - 1) * pageSize;
		List<ImageRecord> resultList = this.imageRecordService.findRecordsByMap(whereParams, beginIndex, pageSize);
		pageData.setResultList(resultList);
        
        model.addAttribute("imageId", imageId);
            
        model.addAttribute("takePhotoId", takePhotoId);
            
        if (beginPhotoBeginTime != null) {
            model.addAttribute("beginPhotoBeginTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(beginPhotoBeginTime));
        }

        if (endPhotoBeginTime != null) {
            model.addAttribute("endPhotoBeginTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(endPhotoBeginTime));
        }
            
        if (beginCallAiBeginTime != null) {
            model.addAttribute("beginCallAiBeginTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(beginCallAiBeginTime));
        }

        if (endCallAiBeginTime != null) {
            model.addAttribute("endCallAiBeginTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(endCallAiBeginTime));
        }
            
        if (beginCreateTime != null) {
            model.addAttribute("beginCreateTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(beginCreateTime));
        }

        if (endCreateTime != null) {
            model.addAttribute("endCreateTime", (new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")).format(endCreateTime));
        }
                    model.addAttribute("pageData", pageData);

		return "/bs/imageRecord/list";
	}

    @RequestMapping(value = "/show")
	public String show(@RequestParam(value = "imageId", required = true) Long imageId, Model model) {
		if (imageId == null) {
			return "/common/error";
		}
		ImageRecord record = this.imageRecordService.findRecordByKey(imageId);
		model.addAttribute("record", record);
		if (record == null) {
			model.addAttribute("errMsg", "未查到到记录");
			return "/common/error";
		}
		return "/bs/imageRecord/show";
	}

    @RequestMapping(value = "/showAdd")
	public String showAdd(@RequestParam(value = "imageId", required = false)
	Long imageId, Model model) {
		ImageRecord record = null;
		if (imageId != null) {
			record = this.imageRecordService.findRecordByKey(imageId);
		}

		if (record == null) {
			record = new ImageRecord();
		}

		model.addAttribute("record", record);
		return "/bs/imageRecord/showAdd";
	}

    @RequestMapping(value = "/add")
	public String add(@Valid ImageRecord record, BindingResult result, Model model) {
		this.imageRecordService.addRecord(record);
		return "redirect:/bs/imageRecord/show?imageId=" + record.getImageId();
	}


    @RequestMapping(value = "/showUpd")
	public String showUpd(@RequestParam(value = "imageId", required = true)
	Long imageId,
    Model model) {
		if (imageId == null) {
			return "/common/error";
		}
		ImageRecord record = this.imageRecordService.findRecordByKey(imageId);
		if (record == null) {
			model.addAttribute("errMsg", "未查到到记录");
			return "/common/error";
		}
		model.addAttribute("record", record);
		return "/bs/imageRecord/showUpd";
	}

	@RequestMapping(value = "/upd")
	public String upd(@Valid ImageRecord record, BindingResult result, Model model) {
		if (result.hasErrors()) {
			model.addAttribute("record", record);
			return "/bs/imageRecord/showUpd";
		}

		this.imageRecordService.updateRecord(record);
		return "redirect:/bs/imageRecord/show?imageId=" + record.getImageId();
	}

    @RequestMapping(value = "/del")
	public String del(@RequestParam(value = "imageId", required = true, defaultValue = "0") Long imageId,
			Model model) {
		this.imageRecordService.deleteRecord(imageId);
		return "/bs/imageRecord/delOk";
	}

	@RequestMapping(value = "/delRecords")
	public String delRecords(Long[] delIds, Model model) {
		if (delIds != null) {
			for (int i = 0; i < delIds.length; i++) {
				if (delIds[i] != null) {
					this.imageRecordService.deleteRecord(delIds[i]);
				}
			}
		}
		return "redirect:/bs/imageRecord/list";
	}

}