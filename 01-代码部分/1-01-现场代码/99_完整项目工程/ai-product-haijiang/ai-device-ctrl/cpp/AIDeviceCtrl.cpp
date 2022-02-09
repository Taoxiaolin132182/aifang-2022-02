#include <stdio.h>
#include <stdlib.h>
#include <memory.h>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <cassert>
#include <thread>

#include "AIDeviceCtrl.h"
#include "libbmp/CPP/libbmp.h"

using namespace std;


extern "C" {
// 以下给python调用，数据类型保持简单平凡
//------------------------------------------------------------------------

/** 计算bmp黑白颜色值 */
bool ai_calc_bmp_color(const char * astrFilePath, int * aiBlackNum, int * aiWhiteNum)
{
//Gray = (R*299 + G*587 + B*114 + 500) / 1000
//#define LGray(rgb) (uint32_t(rgb[2])*299 + uint32_t(rgb[1])*587 + uint32_t(rgb[0])*114)

// Gray = (R*306 + G*601 + B*117) >> 10
#define LGray(rgb) (uint32_t(rgb[2])*306 + uint32_t(rgb[1])*601 + uint32_t(rgb[0])*117)

/* ITU-R Recommendation 601-2 (assuming nonlinear RGB) */
//#define L(rgb)\
//    ((INT32) (rgb)[0]*299 + (INT32) (rgb)[1]*587 + (INT32) (rgb)[2]*114)
#define CLIP(v) ((v) <= 0 ? 0 : (v) >= 255 ? 255 : (v))

	if ( astrFilePath == nullptr || aiBlackNum == nullptr || aiWhiteNum == nullptr )
	{
		printf("astrFilePath == nullptr || aiBlackNum == nullptr || aiWhiteNum == nullptr\n");
		return false;
	}

	BmpImg img;	
	auto const eResult = img.read(astrFilePath);
	if ( BMP_OK != eResult )
	{
		printf("open file: '%s' failed(%d)\n", astrFilePath, eResult);
		return false;
	}

	const auto iWidth = img.get_width();
	const auto iHeight = img.get_height();
	const auto uRowLen = img.get_len_row();
	const auto uPixelLen = img.get_len_pixel();
	//printf("v8 read: %d * %d, uRowLen = %llu, uPixelLen = %llu\n", iWidth, iHeight, uRowLen, uPixelLen);
	if ( uPixelLen != 3 )
	{
		printf("uPixelLen error: %d\n", (int)uPixelLen);
		return false;
	}

	/*
	算法摘录自PIL的c实现，如有错误与本人无关，仅确保实现和python一致
	*/

	const auto & oData = img.get_data();
	const unsigned char * ptr = &oData[0];
	int iBlack = 0, iWhite = 0;
	int* errors = new int[iWidth + 1];
	memset(errors, 0, sizeof(int) * (iWidth + 1));

	if ( img.get_padding() )
	{
		for ( int y = 0; y < iHeight; ++y )
		{
			int l, l0, l1, l2, d2;
			uint8_t * in = (uint8_t *)(ptr + y * uRowLen);

			l = l0 = l1 = 0;

			for ( int x = 0; x < iWidth; ++x )
			{
				/* pick closest colour */
				uint8_t uColor = LGray(in) >> 10; //LGray(in) / 1000;
				in += uPixelLen;
				l = CLIP(/*in[x]*/uColor + (l + errors[x + 1]) / 16);
				auto out_x = (l > 128) ? 255 : 0;
				if ( out_x == 0 )
				{
					++iBlack;
				}
				else
				{
					++iWhite;
				}

				/* propagate errors */
				l -= (int)out_x;
				l2 = l; d2 = l + l; l += d2; errors[x] = l + l0;
				l += d2; l0 = l + l1; l1 = l2; l += d2;
			}

			errors[iWidth] = l0;
		}
	}
	else
	{
		for ( int y = iHeight - 1; y >= 0; --y )
		{
			int l, l0, l1, l2, d2;
			uint8_t * in = (uint8_t *)(ptr + y * uRowLen);

			l = l0 = l1 = 0;

			for ( int x = 0; x < iWidth; ++x )
			{
				/* pick closest colour */
				uint8_t uColor = LGray(in) >> 10; //LGray(in) / 1000;
				in += uPixelLen;
				l = CLIP(/*in[x]*/uColor + (l + errors[x + 1]) / 16);
				auto out_x = (l > 128) ? 255 : 0;
				if ( out_x == 0 )
				{
					++iBlack;
				}
				else
				{
					++iWhite;
				}

				/* propagate errors */
				l -= (int)out_x;
				l2 = l; d2 = l + l; l += d2; errors[x] = l + l0;
				l += d2; l0 = l + l1; l1 = l2; l += d2;
			}

			errors[iWidth] = l0;
		}
	}

	delete[] errors;

	// 到此成功
	*aiBlackNum = iBlack;
	*aiWhiteNum = iWhite;

	//printf("iBlack = %d, iWhite = %d, total = %d, time = %d\n", iBlack, iWhite, iBlack + iWhite, uEndTime - uBeginTime);

	return true;
}

void cc_use_cpu()
{
#if 1

#else
			for ( int i = 0; i < iHeight; ++i )
			{
				// for row
				//printf("read row...\n");
				auto ptrCurLine = ptr;
				for ( int i = 0; i < iWidth; ++i )
				{
					// for col
					if ( LGray(ptrCurLine) >= 128000 )
					{
						++iWhite;
					}
					else
					{
						++iBlack;
					}
					ptrCurLine += uPixelLen;
				}

				ptr += uRowLen;
			}			
#endif

	for ( ;;);
}

void cc_call_python(void (*python_fn)())
{
	/*** ！！！严重警告：仅用于测试python多线程性能代码，有泄露不可实际使用！！！ ***/
	auto t = new thread ([=] {
		if ( python_fn ) python_fn();
	});
	t->detach();
}

//------------------------------------------------------------------------
}

//#if !defined(COMP_FOR_SO) && !defined(CTRLDLL_EXPORTS)
//
//int main(int argc, char * argv[])
//{
//	return 0;
//}
//
//#endif
