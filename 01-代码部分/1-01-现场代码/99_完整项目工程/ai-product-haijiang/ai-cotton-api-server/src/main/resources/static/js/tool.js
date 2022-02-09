var cookie = {
  set: function (key, val) {
    // 设置cookie方法
    document.cookie = key + '=' + val; // 设置cookie
  },
  get: function (key) {
    // 获取cookie方法
    /* 获取cookie参数 */
    var getCookie = document.cookie.replace (/[ ]/g, ''); // 获取cookie，并且将获得的cookie格式化，去掉空格字符
    var arrCookie = getCookie.split (';'); // 将获得的cookie以"分号"为标识
    // 将cookie保存到arrCookie的数组中
    var tips; // 声明变量tips
    for (var i = 0; i < arrCookie.length; i++) {
      // 使用for循环查找cookie中的tips变量
      var arr = arrCookie[i].split ('='); // 将单条cookie用"等号"为标识，将单条cookie保存为arr数组
      if (key == arr[0]) {
        // 匹配变量名称，其中arr[0]是指的cookie名称，如果该条变量为tips则执行判断语句中的赋值操作
        tips = arr[1]; // 将cookie的值赋给变量tips
        break; // 终止for循环遍历
      }
    }
    return tips;
  },
};

const Tool = (() => {
  let REGEXP_TYPES = /\s([a-zA-Z]+)/;
  let REGEXP_SPACES = /\s+/;
  let REGEXP_TRIM = /^\s+(.*)\s+^/;
  function isString (str) {
    return typeof str === 'string';
  }
  function typeOf (obj) {
    return toString.call (obj).match (REGEXP_TYPES)[1].toLowerCase ();
  }
  function isFunction (fn) {
    return typeOf (fn) === 'function';
  }
  function each (obj, callback) {
    var length;
    var i;

    if (obj && isFunction (callback)) {
      if (isArray (obj) || isNumber (obj.length) /* array-like */) {
        for ((i = 0), (length = obj.length); i < length; i++) {
          if (callback.call (obj, obj[i], i, obj) === false) {
            break;
          }
        }
      } else if (isObject (obj)) {
        for (i in obj) {
          if (hasOwnProperty.call (obj, i)) {
            if (callback.call (obj, obj[i], i, obj) === false) {
              break;
            }
          }
        }
      }
    }

    return obj;
  }
  function trim (str) {
    if (!isString (str)) {
      str = String (str);
    }

    if (str.trim) {
      str = str.trim ();
    } else {
      str = str.replace (REGEXP_TRIM, '$1');
    }

    return str;
  }
  function addListener (element, type, handler) {
    var types;

    if (!isFunction (handler)) {
      return;
    }

    types = trim (type).split (REGEXP_SPACES);

    if (types.length > 1) {
      return each (types, function (type) {
        addListener (element, type, handler);
      });
    }

    if (element.addEventListener) {
      element.addEventListener (type, handler, false);
    } else if (element.attachEvent) {
      element.attachEvent ('on' + type, handler);
    }
  }

  function query (el) {
    if (typeof el === 'string') {
      var selected = document.querySelector (el);
      if (!selected) {
        warn ('Cannot find element: ' + el);
        return document.createElement ('div');
      }
      return selected;
    } else {
      return el;
    }
  }
  function getQueryStringByName (paramName) {
    var result = location.search.match (
      new RegExp ('[\?\&]' + paramName + '=([^\&]+)', 'i')
    );
    if (result == null || result.length < 1) {
      return '';
    }
    return result[1];
  }
  var HTTPUtil = {};
  HTTPUtil.get = function (url, params) {
    if (params) {
      let paramsArray = [];
      //encodeURIComponent
      Object.keys (params).forEach (key =>
        paramsArray.push (key + '=' + params[key])
      );
      if (url.search (/\?/) === -1) {
        url += '?' + paramsArray.join ('&');
      } else {
        url += '&' + paramsArray.join ('&');
      }
    }
    return new Promise (function (resolve, reject) {
      fetch (url, {
        method: 'GET',
        credentials: 'include'
      })
        .then (response => {
          if (response.ok) {
            return response.json ();
          } else {
            reject ({status: response.status});
          }
        })
        .then (response => {
          resolve (response);
        })
        .catch (err => {
          reject ({status: -1});
        });
    });
  };

  /** 
 * 基于 fetch 封装的 POST请求  FormData 表单数据 
 * @param url 
 * @param formData   
 * @param  
 * @returns {Promise} 
 */

  HTTPUtil.post = function (url, formData) {
    return new Promise (function (resolve, reject) {
      fetch (url, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })
        .then (response => {
          if (response.ok) {
            return response.json ();
          } else {
            reject ({status: response.status});
          }
        })
        .then (response => {
          resolve (response);
        })
        .catch (err => {
          reject ({status: -1});
        });
    });
  };

  return {
    addListener: addListener,
    query: query,
    getQueryStringByName: getQueryStringByName,
    HTTPUtil:HTTPUtil
  };
}) ();
