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
import com.aidolphin.ai.cotton.mapper.ErrRecord;
import com.aidolphin.ai.cotton.service.ErrRecordService;

@Controller
@Scope("singleton")
@RequestMapping("/bs/errRecord")
public class ErrRecordController {
//	private static final Logger LOGGER = LoggerFactory.getLogger(UserInfoController.class);

    private static final int DEFAULT_PAGE_SIZE = 25;
    private static final int EXPORT_RECORD_MAX_SIZE = 50000;

    @Autowired
    private ErrRecordService errRecordService;

    @RequestMapping(value = "/list")
    public String list(
        
            @RequestParam(value="id", required=false) Long id ,
            			@RequestParam(value = "currentPage", required = true, defaultValue = "1") Integer currentPage,
			@RequestParam(value = "pageSize", required = false) Integer pageSize,
            ModelMap model) {
		PageData<ErrRecord> pageData = new PageData<ErrRecord>();
		pageData.setCurrentPage(currentPage);
		if ((pageSize == null) || (pageSize <= 0)) {
			pageSize = DEFAULT_PAGE_SIZE;
		}
		pageData.setPageSize(pageSize);

		// 查询参数
		Map<String, Object> whereParams = new HashMap<String, Object>(0);

        
        if (id != null) {
            whereParams.put("id", id);
        }
            
		int count = this.errRecordService.findRecordCount(whereParams);
		pageData.setTotalCount(count);

		int beginIndex = (currentPage - 1) * pageSize;
		List<ErrRecord> resultList = this.errRecordService.findRecordsByMap(whereParams, beginIndex, pageSize);
		pageData.setResultList(resultList);
        
        model.addAttribute("id", id);
                    model.addAttribute("pageData", pageData);

		return "/bs/errRecord/list";
	}

    @RequestMapping(value = "/show")
	public String show(@RequestParam(value = "id", required = true) Long id, Model model) {
		if (id == null) {
			return "/common/error";
		}
		ErrRecord record = this.errRecordService.findRecordByKey(id);
		model.addAttribute("record", record);
		if (record == null) {
			model.addAttribute("errMsg", "未查到到记录");
			return "/common/error";
		}
		return "/bs/errRecord/show";
	}

    @RequestMapping(value = "/showAdd")
	public String showAdd(@RequestParam(value = "id", required = false)
	Long id, Model model) {
		ErrRecord record = null;
		if (id != null) {
			record = this.errRecordService.findRecordByKey(id);
		}

		if (record == null) {
			record = new ErrRecord();
		}

		model.addAttribute("record", record);
		return "/bs/errRecord/showAdd";
	}

    @RequestMapping(value = "/add")
	public String add(@Valid ErrRecord record, BindingResult result, Model model) {
		this.errRecordService.addRecord(record);
		return "redirect:/bs/errRecord/show?id=" + record.getId();
	}


    @RequestMapping(value = "/showUpd")
	public String showUpd(@RequestParam(value = "id", required = true)
	Long id,
    Model model) {
		if (id == null) {
			return "/common/error";
		}
		ErrRecord record = this.errRecordService.findRecordByKey(id);
		if (record == null) {
			model.addAttribute("errMsg", "未查到到记录");
			return "/common/error";
		}
		model.addAttribute("record", record);
		return "/bs/errRecord/showUpd";
	}

	@RequestMapping(value = "/upd")
	public String upd(@Valid ErrRecord record, BindingResult result, Model model) {
		if (result.hasErrors()) {
			model.addAttribute("record", record);
			return "/bs/errRecord/showUpd";
		}

		this.errRecordService.updateRecord(record);
		return "redirect:/bs/errRecord/show?id=" + record.getId();
	}

    @RequestMapping(value = "/del")
	public String del(@RequestParam(value = "id", required = true, defaultValue = "0") Long id,
			Model model) {
		this.errRecordService.deleteRecord(id);
		return "/bs/errRecord/delOk";
	}

	@RequestMapping(value = "/delRecords")
	public String delRecords(Long[] delIds, Model model) {
		if (delIds != null) {
			for (int i = 0; i < delIds.length; i++) {
				if (delIds[i] != null) {
					this.errRecordService.deleteRecord(delIds[i]);
				}
			}
		}
		return "redirect:/bs/errRecord/list";
	}

}