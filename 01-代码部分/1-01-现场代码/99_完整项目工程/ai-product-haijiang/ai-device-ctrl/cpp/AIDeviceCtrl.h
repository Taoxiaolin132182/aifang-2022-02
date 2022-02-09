#pragma once

#if defined(_WINDOWS)
#	include "stdafx.h"
#else
#	include <unistd.h>
#	include <pthread.h>
#endif

#include <stdint.h>

#if defined(_WINDOWS)
#	ifdef CTRLDLL_EXPORTS
#		define CTRLDLL_API __declspec(dllexport)
#	else
#		define CTRLDLL_API __declspec(dllimport)
#	endif
#else
#	define CTRLDLL_API
#endif

#if defined(_WINDOWS) && defined(USE_STDCALL)
#	define STDCALL __stdcall
#else
#	define STDCALL
#endif

extern "C"
{
	CTRLDLL_API void STDCALL cc_use_cpu();
	CTRLDLL_API void STDCALL cc_call_python(void (*python_fn)());

	/** 计算bmp黑白颜色值 */
	CTRLDLL_API bool STDCALL ai_calc_bmp_color(const char * astrFilePath, int * aiBlackNum, int * aiWhiteNum);
};
