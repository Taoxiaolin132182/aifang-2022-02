var Util = {
	
}

/**
 * 翻页 
 * @param frm 表单
 * @param toPageNo 页码(整型)
 */
Util.turnPage = function(frm, toPageNo) {
	frm.currentPage.value = toPageNo;
	frm.submit();
}

/**
 * 全部选中
 * @param p_objForm 表单
 */
Util.selectAllCheckbox = function(p_objForm){
    for (var i = 0; i < p_objForm.elements.length; i++) {
    	if (p_objForm.elements[i].type == 'checkbox') {
        	p_objForm.elements[i].checked = true;
        	p_objForm.elements[i].parentNode.className = 'checkbox-pretty inline checked';
        }
    }
}

/**
 * 全部取消
 * @param p_objForm 表单
 */
Util.cancelAllCheckbox = function(p_objForm) {
    for (var i = 0; i < p_objForm.elements.length; i++) {
        if (p_objForm.elements[i].type == 'checkbox') {
        	p_objForm.elements[i].checked = false;
        	p_objForm.elements[i].parentNode.className = 'checkbox-pretty inline';
        }
    }
}

/**
 * 检查并修正全选checkBox的状态
 * @param p_objForm 表单
 * @param name_checkAll 全选checkbox的id
 */
Util.verifyCheckAll = function(p_objForm, name_checkAll) {
	var checkAll = document.getElementById(name_checkAll); 
	if (checkAll == null) {
		return;
	}
    if (checkAll.checked) {
        for (var i = 0; i < p_objForm.elements.length; i++) {
        	if ((p_objForm.elements[i].name != checkAll.name)
        		&& (p_objForm.elements[i].type == 'checkbox')
        		&& (p_objForm.elements[i].checked == false)) {
        		checkAll.checked = false;
        		checkAll.parentNode.className = 'checkbox-pretty inline';
        		break;
        	}
        }
    } else {
    	var bAllChecked = true;
    	for (var i = 0; i < p_objForm.elements.length; i++) {
        	if ((p_objForm.elements[i].name != checkAll.name)
        		&& (p_objForm.elements[i].type == 'checkbox')) {
        		bAllChecked = bAllChecked && p_objForm.elements[i].checked; 
        	}
        }
        checkAll.checked = bAllChecked;
        checkAll.parentNode.className = 'checkbox-pretty inline' + (bAllChecked ? ' checked' : '');
    }
}

/**
 * 验证是否选中一个复选框
 * @param p_objForm 表单
 * @param name_skip 需要忽略的checkbox的id
 * @param p_objForm 如果没有选择复选框的提示信息
 * @param p_objForm 确认信息
 * @returns true or false
 */
Util.confirmSelectedCheckboxes = function(p_objForm, name_skip) {
	var delForm = document.getElementById(p_objForm);
	var skip = document.getElementById(name_skip);
	
    var bCanSub = 0;
    for (var i = 0; i < delForm.elements.length; i++) {
    	if ((delForm.elements[i].name != skip.name)
    	 	&& (delForm.elements[i].type == 'checkbox') 
    	 	&& (delForm.elements[i].checked)) {
			bCanSub = 1;
        }
    }
    if (bCanSub == 0) {
    	$.alert({
    		title: '请勾选',
    		okBtn : '好',
    		body: '<div class="sui-msg msg-large msg-block msg-info"><div class="msg-con">请选择要删除的记录信息</div><s class="msg-icon"></s></div>'
    	});
        return false;
    } else {
    	$.confirm({
    		title: '确认删除',
    		body: '<div class="sui-msg msg-large msg-block msg-question"><div class="msg-con">确认要删除这些记录信息吗？</div><s class="msg-icon"></s></div>',
    		okBtn: '确定',
    		cancelBtn: '取消',
    		okHide: function (e) {
    			delForm.submit();
    			return true;
    		}
    	});
    }
}

/**
 * 用户确认框
 * @param p_sConfirmInfo 确认信息
 * @returns true or false
 */
Util.windowConfirm = function(p_sConfirmInfo) {
	if (window.confirm(p_sConfirmInfo))	{
   		return true;	
   	} else	{
   		return false;	
   	}
}


/**
 * 去掉字符串中的空格
 * @param p_str
 * @returns string
 */
Util.trim = function(p_str) {
	return p_str.replace(/^\s*/, "").replace(/\s*$/, "");
}

/**
 * 根据表单id属性提交该表单
 * @param formId
 * @return
 */
Util.submitFormById = function(formId){
	var formObj = document.getElementById(formId); 
	if (formObj != null) {
		formObj.submit();
	}
}

/**
 * 格式化金额
 * @param s 金额
 * @param n 小数点位数
 * @return
 */
Util.formatMoney = function(s, n) {
   n = n > 0 && n <= 20 ? n : 2;
   s = parseFloat((s + "").replace(/[^\d\.-]/g, "")).toFixed(n) + "";
   var l = s.split(".")[0].split("").reverse(),
   r = s.split(".")[1];
   t = "";
   for(i = 0; i < l.length; i ++ )
   {
      t += l[i] + ((i + 1) % 3 == 0 && (i + 1) != l.length ? "," : "");
   }
   return t.split("").reverse().join("") + "." + r;
}

/**
 * 读取cookie值
 * @param cookieName
 * @return
 */
Util.readCookie = function(cookieName) {
	cookie_array = document.cookie.split ("; ");
	for (x=0; x < cookie_array.length; x++) {
		cookieParts_array = cookie_array[x].split("=");
		if (cookieParts_array[0] == cookieName)	{
			return cookieParts_array[1];
		}
	}
	return null;
}

/**
 * 写入cookie
 * @param cookieName
 * @param cookieValue
 * @return
 */
Util.writeCookie = function(cookieName, cookieValue) {
	document.cookie = cookieName + "=" + cookieValue + ";";
}

/**
 * 居中弹出浮层
 * 依赖jquery
 * @param divId 浮层的id
 */
Util.popupCenter = function(divId){
	var divObj = $('#' + divId)
	var _scrollHeight = $(document).scrollTop(),//获取当前窗口距离页面顶部高度
	_windowHeight = $(window).height(),//获取当前窗口高度
	_windowWidth = $(window).width(),//获取当前窗口宽度
	_popup_styleHeight = divObj.height(),//获取弹出层高度
	_popup_styleWeight = divObj.width();//获取弹出层宽度
	_posiTop = (_windowHeight - _popup_styleHeight)/2 + _scrollHeight;
	_posiLeft = (_windowWidth - _popup_styleWeight)/2;
	divObj.css({"left": _posiLeft + "px","top":_posiTop + "px"});//设置position
	$('#' + divId).show();
}

/**
 * 居中弹出浮层,浮层中包含标题和iframe
 * @param divId
 * @param width
 * @param height
 * @param titleId
 * @param title
 * @param iframeId
 * @param iframeSrc
 */
Util.popupIframeCenter = function(divId, width, height, titleId, title, iframeId, iframeSrc) {
	$('#' + divId).css({"width": width + "px","height":height + "px"});
	
	$('#' + titleId).text(title);
	
	$('#' + iframeId).attr("src", iframeSrc);
	$('#' + iframeId).css({"width": (width - 50) + "px","height":(height - 50) + "px"});
	
	Util.popupCenter(divId);
}

/**
 * 获取鼠标在页面上的位置
 * @param ev		触发的事件
 * @return			x:鼠标在页面上的横向位置, y:鼠标在页面上的纵向位置
 */
Util.getMousePoint = function(ev) {
	// 定义鼠标在视窗中的位置
	var point = {
		x:0,
		y:0
	};
 
	// 如果浏览器支持 pageYOffset, 通过 pageXOffset 和 pageYOffset 获取页面和视窗之间的距离
	if(typeof window.pageYOffset != 'undefined') {
		point.x = window.pageXOffset;
		point.y = window.pageYOffset;
	}
	// 如果浏览器支持 compatMode, 并且指定了 DOCTYPE, 通过 documentElement 获取滚动距离作为页面和视窗间的距离
	// IE 中, 当页面指定 DOCTYPE, compatMode 的值是 CSS1Compat, 否则 compatMode 的值是 BackCompat
	else if(typeof document.compatMode != 'undefined' && document.compatMode != 'BackCompat') {
		point.x = document.documentElement.scrollLeft;
		point.y = document.documentElement.scrollTop;
	}
	// 如果浏览器支持 document.body, 可以通过 document.body 来获取滚动高度
	else if(typeof document.body != 'undefined') {
		point.x = document.body.scrollLeft;
		point.y = document.body.scrollTop;
	}
 
	// 加上鼠标在视窗中的位置
	point.x += ev.clientX;
	point.y += ev.clientY;
 
	// 返回鼠标在视窗中的位置
	return point;
}

/**
 * 获取网页被卷去的高
 */
Util.getBodyScrollTop = function() {
	var bodyTop = 0; 
	if (typeof window.pageYOffset != 'undefined') { 
		bodyTop = window.pageYOffset; 
	} else if (typeof document.compatMode != 'undefined' && document.compatMode != 'BackCompat') { 
		bodyTop = document.documentElement.scrollTop; 
	} else if (typeof document.body != 'undefined') { 
		bodyTop = document.body.scrollTop; 
	} else {
		bodyTop = document.body.scrollTop;
	}
	return bodyTop;
}

