SOLIB	= 

#-lopencv_imgproc -lopencv_saliency -lopencv_highgui -lopencv_stitching -lopencv_video \
#			-lopencv_ml -lopencv_shape -lopencv_core -lopencv_calib3d \
#			-lopencv_ccalib -lopencv_bgsegm -lopencv_reg -lopencv_fuzzy \
#			-lopencv_imgcodecs -lopencv_superres -lopencv_features2d \
#			-lopencv_flann -lopencv_freetype \
#			-lopencv_surface_matching -lopencv_line_descriptor -lopencv_plot -lopencv_text \
#			-lopencv_datasets -lopencv_stereo -lopencv_face -lopencv_objdetect \
#			-lopencv_ximgproc -lopencv_videostab -lopencv_phase_unwrapping \
#			-lopencv_hdf -lopencv_photo \
#			-lopencv_optflow -lopencv_aruco -lopencv_structured_light -lopencv_dpm \
#			-lopencv_xphoto -lopencv_videoio -lopencv_bioinspired -lopencv_rgbd -lopencv_xobjdetect \
#			-lMvCameraControl

#-lopencv_xfeatures2d -lopencv_quality -lopencv_hfs -lopencv_tracking -lopencv_dnn -lopencv_gapi -lopencv_dnn_objdetect -lopencv_img_hash

CMP_FILE = AIDeviceCtrl.cpp ./libbmp/CPP/libbmp.cpp
CXXFLAG	= -std=c++17 -O3 -march=native -DNDEBUG -g -fPIC -rdynamic -pthread -shared

#LDPATH = -Wl,-rpath=$(MVCAM_COMMON_RUNENV)/64 -L$(MVCAM_COMMON_RUNENV)/64 
LDPATH = 
LDFLAGS = -lpthread $(SOLIB) $(LDPATH)

#INCLUDEPATH = -I/usr/include -I/opt/MVS/include
INCLUDEPATH = -I./libbmp/CPP/
CXX	= g++

MVSCtrlAll:
	$(CXX) $(CXXFLAG) -o ../python/AIDeviceCtrl/libAIDeviceCtrl.so $(CMP_FILE) -DCOMP_FOR_SO $(INCLUDEPATH) $(LDFLAGS)

clean:
	rm ../python/AIDeviceCtrl/libAIDeviceCtrl.so
	rm *.o

