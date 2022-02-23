import os
import sys
import ctypes
import time
from . import util

_hAIDeviceCtrl = None  #调用AIDeviceCtrlDll和libAIDeviceCtrl动态库


'''
@return 获取AIDeviceCtrlDll和libAIDeviceCtrl动态库唯一实例
'''
def get_ai_device_ctrl_lib():
    global _hAIDeviceCtrl
    if _hAIDeviceCtrl is None:
        #确保取到真正的脚本目录，不要用sys.path[0]
        TASK_PY_PATH = os.path.split(os.path.realpath(__file__))[0]

        strLoadLib = ""
        if util.isWindows():
            strLoadLib = "%s\\AIDeviceCtrlDll.dll" % TASK_PY_PATH
        else:
            strLoadLib = "%s/libAIDeviceCtrl.so" % TASK_PY_PATH
        #end if

        hLib = None
        try:
            hLib = ctypes.cdll.LoadLibrary(strLoadLib)
        except Exception as e:            
            util.addLog("LoadLibrary %s err: %s" % (strLoadLib, str(e)))
            return None
        #end try
        
        #/** 计算bmp黑白颜色值 */
	    #CTRLDLL_API bool STDCALL ai_calc_bmp_color(const char * astrFilePath, int * aiBlackNum, int * aiWhiteNum);
        hLib.ai_calc_bmp_color.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        hLib.ai_calc_bmp_color.restype = ctypes.c_int
        
        _hAIDeviceCtrl = hLib
    #end if

    return _hAIDeviceCtrl
#end def


'''
计算bmp黑白颜色值
@param astrFilePath bmp文件路径
@return 成功返回(黑色数量, 白色数量)，失败返回(-1, -1)
'''
def ai_calc_bmp_color(astrFilePath):
    try:
        iBlackNum = ctypes.c_int(-1)
        iWhiteNum = ctypes.c_int(-1)
        pstrFilePath = bytes(astrFilePath, encoding = "utf-8")
        iRet = get_ai_device_ctrl_lib().ai_calc_bmp_color(pstrFilePath, ctypes.byref(iBlackNum), ctypes.byref(iWhiteNum))
        if iRet == 0:
            return (-1, -1)
        else:
            return (iBlackNum.value, iWhiteNum.value)
        #end if
    except Exception as e:            
        util.addLog("ai_calc_bmp_color err: %s" % (str(e)))
        return (-1, -1)
    #end try
#end def

