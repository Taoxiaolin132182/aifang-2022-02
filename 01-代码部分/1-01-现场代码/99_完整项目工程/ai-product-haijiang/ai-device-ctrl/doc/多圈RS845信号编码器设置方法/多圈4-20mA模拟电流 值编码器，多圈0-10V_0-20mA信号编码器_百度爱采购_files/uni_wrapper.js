function isSingleInstanceProd(s){var i=["mn","ma","im_hi"];return("|"+i.join("|")+"|").indexOf("|"+s+"|")>-1}function isLoginInstance(s){return s=s||"login",s+""=="login"}function saveInitInstance(s){window._pass_popinit_instance=s}function getInitInstance(){return window._pass_popinit_instance}var passport=passport||window.passport||{};passport._modulePool=passport._modulePool||{},passport._define=passport._define||function(s,i){passport._modulePool[s]=i&&i()},passport._getModule=passport._getModule||function(s){return passport._modulePool[s]};var passport=window.passport||{};passport.pop=passport.pop||{},passport.pop.insertScript=passport.pop.insertScript||function(s,i){var n=document,a=n.createElement("SCRIPT");a.type="text/javascript",a.charset="UTF-8",a.readyState?a.onreadystatechange=function(){("loaded"===a.readyState||"complete"===a.readyState)&&(a.onreadystatechange=null,i&&i())}:a.onload=function(){i&&i()},a.src=s,n.getElementsByTagName("head")[0].appendChild(a)},passport.ieVersion=function(){var s,i=navigator.userAgent.toLowerCase(),n=i.indexOf("msie")>-1;return n&&(s=i.match(/msie ([\d.]+)/)[1]),s},passport.pop.init=passport.pop.init||function(s){var i={"http:":"http://passport.bdimg.com","https:":"https://passport.bdimg.com"};if(passport.ieVersion()<=8&&(i={"http:":"http://passport.baidu.com","https:":"https://passport.baidu.com"}),isSingleInstanceProd(s.apiOpt.product)&&isLoginInstance(s.type)&&getInitInstance())return getInitInstance();var n;n=s&&"https"===s.protocol?"https:":window.location?window.location.protocol.toLowerCase():document.location.protocol.toLowerCase();var a=["pp","mn","wk","cmovie","translate","baidugushitong","ik","exp","waimai","jn","im","do","yuedu","hao123","tb","netdisk","developer","newdev","image_eco","zbsc","bpit_hcm","defensor","study","bizcrm","sjhlexus_all"],e=s&&s.apiOpt&&s.apiOpt.product||"",t=("|"+a.join("|")+"|").indexOf("|"+e+"|")>-1||"v4"===(s&&s.loginVersion),p=t?"/passApi/js/uni_loginv4_0d1ad52.js":"/passApi/js/uni_login_f101ef0.js",c=t?"/passApi/js/uni_loginv4_tangram_16b93c8.js":"/passApi/js/uni_login_tangram_007946a.js",o=t?"/passApi/css/uni_loginv4_35dda7d.css":"/passApi/css/uni_login_new_5b1f23c.css",_={uni_login:p,uni_login_tangram:c,uni_loginPad:"/passApi/js/uni_loginPad_b3e27bb.js",uni_loginPad_tangram:"/passApi/js/uni_loginPad_tangram_62f96a8.js",uni_smsloginEn:"/passApi/js/uni_smsloginEn_e2c86c4.js",uni_smsloginEn_tangram:"/passApi/js/uni_smsloginEn_tangram_1a9d3fa.js",uni_loginWap:"/passApi/js/uni_loginWap_9fde5bb.js",uni_loginWap_tangram:"/passApi/js/uni_loginWap_9fde5bb.js",uni_accConnect:"/passApi/js/uni_accConnect_bed20d3.js",uni_accConnect_tangram:"/passApi/js/uni_accConnect_tangram_4968da3.js",uni_accRealName:"/passApi/js/uni_accRealName_d94b1d9.js",uni_accRealName_tangram:"/passApi/js/uni_accRealName_tangram_8634f99.js",uni_checkPhone:"/passApi/js/uni_checkPhone_bd8449d.js",uni_checkPhone_tangram:"/passApi/js/uni_checkPhone_tangram_0d81b2e.js",uni_checkIDcard:"/passApi/js/uni_checkIDcard_20c58cd.js",uni_checkIDcard_tangram:"/passApi/js/uni_checkIDcard_tangram_7f833fa.js",uni_accSetPwd:"/passApi/js/uni_accSetPwd_d746e9e.js",uni_accSetPwd_tangram:"/passApi/js/uni_accSetPwd_tangram_09beb84.js",uni_IDCertify:"/passApi/js/uni_IDCertify_1e65f2f.js",uni_IDCertify_tangram:"/passApi/js/uni_IDCertify_tangram_6d7ec8a.js",uni_travelComplete:"/passApi/js/uni_travelComplete_6e07ac8.js",uni_travelComplete_tangram:"/passApi/js/uni_travelComplete_tangram_85cd194.js",uni_bindGuide:"/passApi/js/uni_bindGuide_689b3e5.js",uni_bindGuide_tangram:"/passApi/js/uni_bindGuide_tangram_7e90bca.js",uni_fillUserName:"/passApi/js/uni_fillUserName_fe8ee80.js",uni_fillUserName_tangram:"/passApi/js/uni_fillUserName_tangram_e0567b5.js",uni_IDCertifyQrcode:"/passApi/js/uni_IDCertifyQrcode_6c378ab.js",uni_IDCertifyQrcode_tangram:"/passApi/js/uni_IDCertifyQrcode_tangram_7bd35c8.js",uni_loadingApi:"/passApi/js/uni_loadingApi_84284d2.js",uni_loadingApi_tangram:"/passApi/js/uni_loadingApi_tangram_c676792.js",uni_secondCardList:"/passApi/js/uni_secondCardList_8b8ee4a.js",uni_secondCardList_tangram:"/passApi/js/uni_secondCardList_tangram_ae01263.js",uni_secondCardVerify:"/passApi/js/uni_secondCardVerify_052f736.js",uni_secondCardVerify_tangram:"/passApi/js/uni_secondCardVerify_tangram_c93a879.js",uni_multiBind:"/passApi/js/uni_multiBind_eeaaad8.js",uni_multiBind_tangram:"/passApi/js/uni_multiBind_tangram_80f48b4.js",uni_multiUnbind:"/passApi/js/uni_multiUnbind_f5914f6.js",uni_multiUnbind_tangram:"/passApi/js/uni_multiUnbind_tangram_f47638f.js",uni_changeUser:"/passApi/js/uni_changeUser_30e3b1b.js",uni_changeUser_tangram:"/passApi/js/uni_changeUser_tangram_9683785.js",uni_loginMultichoice:"/passApi/js/uni_loginMultichoice_5732e38.js",uni_loginMultichoice_tangram:"/passApi/js/uni_loginMultichoice_tangram_2ec31c0.js",uni_confirmWidget:"/passApi/js/uni_confirmWidget_a32fbae.js",uni_confirmWidget_tangram:"/passApi/js/uni_confirmWidget_tangram_b119966.js"},r={login:o,loginWap:"/passApi/css/uni_loginWap_f57424a.css",smsloginEn:"/passApi/css/uni_smsloginEn_eef0a6a.css",accConnect:"/passApi/css/uni_accConnect_ab6dda9.css",accRealName:"/passApi/css/uni_accRealName_a224a37.css",secondCardVerify:"/passApi/css/uni_secondCardVerify_1a69328.css",secondCardList:"/passApi/css/uni_secondCardList_94f229c.css",checkPhone:"/passApi/css/uni_checkPhone_cd7c7a0.css",checkIDcard:"/passApi/css/uni_checkIDcard_be79680.css",accSetPwd:"/passApi/css/uni_accSetPwd_926540f.css",IDCertify:"/passApi/css/uni_IDCertify_36e091b.css",IDCertifyQrcode:"/passApi/css/uni_IDCertifyQrcode_1e8827b.css",loadingApi:"/passApi/css/uni_loadingApi_f8732c0.css",loginPad:"/passApi/css/uni_loginPad_ab36627.css",multiBind:"/passApi/css/uni_multiBind_e8d24e4.css",multiUnbind:"/passApi/css/uni_multiUnbind_21428a6.css",changeUser:"/passApi/css/uni_changeUser_c7ae7b4.css",loginMultichoice:"/passApi/css/uni_loginMultichoice_289d3a0.css",confirmWidget:"/passApi/css/uni_confirmWidget_035fb81.css",uni_rebindGuide:"/passApi/css/uni_rebindGuide_347ecf2.css",travelComplete:"/passApi/css/uni_travelComplete_b06b013.css",bindGuide:"/passApi/css/uni_bindGuide_35d4a06.css",fillUserName:"/passApi/css/uni_fillUserName_931cb17.css"},u=i[n]||i["https:"];s=s||{},s.type=s.type||"login";var d,l=document,m=("_PassUni"+(new Date).getTime(),u+r[s.type]);s.cssUrlWrapper&&(m=cssUrlWrapper.join(t?"uni_loginv4.css":"uni_login.css")),d={show:function(){return d.loadPass(s.apiOpt),d.willShow=!0,d},setSubpro:function(i){return s.apiOpt&&(s.apiOpt.subpro=i),d},setMakeText:function(i){return s.apiOpt&&(s.apiOpt.makeText=i),d},loadPass:function(){var i=l.createElement("link");i.rel="stylesheet",i.type="text/css",i.href=m,i.disabled=!1,i.setAttribute("data-for","result"),l.getElementsByTagName("head")[0].appendChild(i),d.show=function(){return d.willShow=!0,d},s.plugCss&&(i=l.createElement("link"),i.rel="stylesheet",i.type="text/css",i.href=s.plugCss,i.disabled=!1,i.setAttribute("data-for","result"),l.getElementsByTagName("head")[0].appendChild(i)),d.passCallback(),delete d.loadPass},passCallback:function(){passport.pop.insertScript("https://wappass.baidu.com/static/waplib/moonshad.js?tt="+(new Date).getTime(),function(){d.components.length>0?passport.pop.insertScript(d.components.shift(),d.passCallback):(passport.pop[s.type](s,d,function(){d.willShow&&d.show(),s&&s.onRender&&s.onRender()}),delete d.passCallback,delete d.components)})},components:[]};var g="uni_"+s.type;return s.tangram&&(g+="_tangram"),s.apiOpt&&s.apiOpt.product+""=="ik"&&Math.random()<.3&&(d.components.push(u+"/passApi/js/uni/passhunt.js"),s.hunter=!0),d.components.push(u+_[g]),s.cache&&d.loadPass(s.apiOpt),s.id&&l.getElementById(s.id)&&(l.getElementById(s.id).onclick=function(){d.show()}),isSingleInstanceProd(s.apiOpt.product)&&isLoginInstance(s.type)&&saveInitInstance(d),d};