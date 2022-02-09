package com.aidolphin.ai.cotton.controller;

import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@Scope("singleton")
@RequestMapping("/")
public class IndexController {
//	private static final Logger LOGGER = LoggerFactory.getLogger(UserInfoController.class);

	@RequestMapping(value = "/")
	public String index() {
		return "/index";
	}

}