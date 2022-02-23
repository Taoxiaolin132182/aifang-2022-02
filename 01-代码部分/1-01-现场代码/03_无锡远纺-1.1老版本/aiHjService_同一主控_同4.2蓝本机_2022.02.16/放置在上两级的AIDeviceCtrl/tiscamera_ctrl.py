import logging
import sys
import numpy
import cv2
import gi
import time

from collections import namedtuple

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "0.1")

from gi.repository import Tcam, Gst, GLib, GObject

logger = logging.getLogger('main')
DeviceInfo = namedtuple("DeviceInfo", "status name identifier connection_type")
CameraProperty = namedtuple("CameraProperty", "status value min max default step type flags category group")

#Gst.init(sys.argv)  # init gstreamer
Gst.init([])


class TISCallbackData:
    ''' class for user data passed to the on new image callback function
    '''

    def __init__(self):
        self.busy = False
        self.serial = ""
        self.ctrl = None #最终的回调实例
#end class


class TIS:
    'The Imaging Source Camera'

    def __init__(self,serial, width, height, framerate, color):
        ''' Constructor
        :param serial: Serial number of the camera to be used.
        :param width: Width of the wanted video format
        :param height: Height of the wanted video format
        :param framerate: Numerator of the frame rate. /1 is added automatically
        :param color: True = 8 bit color, False = 8 bit mono. ToDo: Y16
        :return: none
        '''
        #Gst.init([])
        self.height = height
        self.width = width
        self.sample = None
        self.samplelocked = False
        self.newsample = False
        self.img_mat = None
        self.ImageCallback = None

        pixelformat = "BGRx"
        if color is False:
            pixelformat="GRAY8"

        p = 'tcambin serial="%s" name=source ! video/x-raw,format=%s,width=%d,height=%d,framerate=%d/1' % (serial,pixelformat,width,height,framerate,)
        p += ' ! videoconvert ! appsink name=sink'
        # p += ' ! appsink name=sink'

        print(p)
        try:
            self.pipeline = Gst.parse_launch(p)
        except GLib.Error as err:
            print("Error creating pipeline: {0}".format(err))
            raise

        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
        # Query a pointer to our source, so we can set properties.
        self.source = self.pipeline.get_by_name("source")

        # Query a pointer to the appsink, so we can assign the callback function.
        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.set_property("max-buffers", 1) #5
        self.appsink.set_property("drop",1)
        self.appsink.set_property("emit-signals",1)
        self.appsink.connect('new-sample', self.on_new_buffer)

    def on_new_buffer(self, appsink):
        self.newsample = True
        if self.samplelocked is False:
            try:
                self.sample = appsink.get_property('last-sample')
                if self.ImageCallback is not None:
                    self.__convert_sample_to_numpy()
                    self.ImageCallback(self, *self.ImageCallbackData);

            except GLib.Error as err:
                logger.error("Error on_new_buffer pipeline: {0}".format(err))
                raise
        return False

    def Start_pipeline(self):
        try:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

        except GLib.Error as err:
            logger.error("Error starting pipeline: {0}".format(err))
            raise

    def __convert_sample_to_numpy(self):
        ''' Convert a GStreamer sample to a numpy array
            Sample code from https://gist.github.com/cbenhagen/76b24573fa63e7492fb6#file-gst-appsink-opencv-py-L34
            The result is in self.img_mat.
        :return:
        '''
        self.samplelocked = True
        buf = self.sample.get_buffer()
        caps = self.sample.get_caps()
        bpp = 4;
        dtype = numpy.uint8
        iUseHeight = caps.get_structure(0).get_value('height')
        iUseWidth = caps.get_structure(0).get_value('width')
        bNeedResize = False
        if( caps.get_structure(0).get_value('format') == "BGRx" ):
            bpp = 4
            bNeedResize = True
        #end if

        if(caps.get_structure(0).get_value('format') == "GRAY8" ):
            bpp = 1;

        if(caps.get_structure(0).get_value('format') == "GRAY16_LE" ):
            bpp = 1;
            dtype = numpy.uint16

        img_mat = numpy.ndarray(
            (iUseHeight,
             iUseWidth,
             bpp),
            buffer=buf.extract_dup(0, buf.get_size()),
            dtype=dtype)
        
        #我们现在这个格式是BGRx，陈红要的是BGR，需要再转换一下
        if bNeedResize: 
            #img_mat = numpy.resize(img_mat, (iUseHeight, iUseWidth, 3))
            img_mat = cv2.cvtColor(img_mat, cv2.COLOR_BGRA2BGR)
        #end if
        self.img_mat = img_mat

        self.newsample = False
        self.samplelocked = False

    def wait_for_image(self,timeout):
        ''' Wait for a new image with timeout
        :param timeout: wait time in second, should be a float number
        :return:
        '''
        tries = 10;
        while tries > 0 and not self.newsample:
            tries -= 1
            time.sleep(float(timeout) / 10.0)

    def Snap_image(self, timeout):
        '''
        Snap an image from stream using a timeout.
        :param timeout: wait time in second, should be a float number. Not used
        :return: bool: True, if we got a new image, otherwise false.
        '''
        if self.ImageCallback is not None:
            logger.info("Snap_image can not be called, if a callback is set.")
            return False

        self.wait_for_image(timeout)
        if( self.sample != None and self.newsample == True):
            self.__convert_sample_to_numpy()
            return True
        return False

    def Get_image(self):
        return self.img_mat

    def Stop_pipeline(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.set_state(Gst.State.NULL)

    def List_Properties(self):
        for name in self.source.get_tcam_property_names():
            print( name )

    def Get_Property(self, PropertyName):
        try:
            return CameraProperty(*self.source.get_tcam_property(PropertyName))
        except GLib.Error as err:
            logger.error("Error get Property {}: {}".format(PropertyName, err))
            raise

    def Set_Property(self, PropertyName, value):
        try:
            self.source.set_tcam_property(PropertyName,GObject.Value(type(value),value))
        except GLib.Error as err:
            logger.error("Error set Property {}: {}".format(PropertyName, err))
            raise

    def Set_Image_Callback(self, function, *data):
        self.ImageCallback = function
        self.ImageCallbackData = data
        
#end class

#触发回调
def s_on_new_image(tis, userdata):
    '''
    Callback function, which will be called by the TIS class
    :param tis: the camera TIS class, that calls this callback
    :param userdata: This is a class with user data, filled by this call.
    :return:
    '''
    # Avoid being called, while the callback is busy
    if userdata.busy:
        logger.info("s_on_new_image: userdata.busy is True")
        return
    #end if

    userdata.busy = True
    
    try:
        # logger.info('----@@@---camera_callback {}'.format(userdata.serial))
        userdata.ctrl.on_new_image(userdata.serial, tis.Get_image())
    except Exception as e:
        logger.error(f"camera callback err---+++++++: {e}")
    #end try
    
    userdata.busy = False
#end def


#控制英美金的摄像头类
class tiscamera_ctrl:
    #构造
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fps = 12
        self.__tis = None
        
        #try:
            #self.__tis = Gst.ElementFactory.make("tcambin")
        #except Exception as e:
            #self.__tis = None
            #print(e)
        ##end try
    #end def
    
    #获取设备列表
    def get_device_list(self):
        oResult = []
        try:
            source = Gst.ElementFactory.make("tcambin")
            oSerials = source.get_device_serials()
            for oItem in oSerials:
                # This returns someting like:
                # (True,
                #  name='DFK Z12GP031',
                #  identifier='The Imaging Source Europe GmbH-11410533',
                #  connection_type='aravis')
                # The identifier is the name given by the backend
                # The connection_type identifies the backend that is used.
                #     Currently 'aravis', 'v4l2', 'libusb' and 'unknown' exist            
                (return_value, model, identifier, connection_type) = source.get_device_info(oItem)
                if return_value:
                    oResult.append((model, str(oItem), connection_type))
                #end if
            #end for
            del source
        except Exception as e:
            logger.error(f"get device list err---+++++++: {e}")
        #end try
        return oResult
    #end def
    
    #打开设备, 若astrSerial为None，则打开默认设备
    def open_device(self, astrSerial, aoCallback):
        try:
            #if astrSerial:
                ## This is gstreamer set_property
                #self.__tis.set_property("serial", astrSerial)
            ##end if
            ## in the READY state the camera will always be initialized
            #self.__tis.set_state(Gst.State.READY)
            #return True

            #video/x-raw,format=BGR,width=2448,height=2048,framerate={1/1,2/1,3/1,4/1,5/1,6/1,7/1,8/1};
            tis = TIS(astrSerial, self.width, self.height, self.fps, True)
            callbackData = TISCallbackData()
            callbackData.serial = astrSerial
            callbackData.ctrl = aoCallback
            tis.Set_Image_Callback(s_on_new_image, callbackData)
            #需要先关闭触发模式
            tis.Set_Property("Trigger Mode", "Off")  #Use this line for GigE cameras
            
            # Avoid, that we handle image, while we are in the pipeline start phase
            callbackData.busy = True
            
            self.__tis = tis
            
            return True
        
        except Exception as e:
            logger.error(f"open device err---+++++++: {e}")
        #end try
            return False
    #end def
    
    #开始抓取图像
    def start_capture(self):
        try:
            if self.__tis is None: return False

            #需要先关闭触发模式
            self.__tis.Set_Property("Trigger Mode", "Off")  #Use this line for GigE cameras
            # Avoid, that we handle image, while we are in the pipeline start phase
            self.__tis.ImageCallbackData[0].busy = True
            
            #start pipeline
            self.__tis.Start_pipeline()
            
            #然后再开启触发
            self.__tis.Set_Property("Trigger Mode", "On") # Use this line for GigE cameras
            #可能在Trigger Mode开启前已经来了一帧，先放过这一帧
            time.sleep(0.1)
            
            # Now the callback function does something on a trigger
            self.__tis.ImageCallbackData[0].busy = False
            
            
            return True
        
        except Exception as e:
            logger.error(f"start capture err---+++++++: {e}")
            self.stop_capture()
        #end try
        
        return False
    #end def
    
    #关闭抓取图像
    def stop_capture(self):
        try:
            if self.__tis is None: return
        
            self.__tis.Stop_pipeline()
        
        except Exception as e:
            logger.error(f"stop capture err---+++++++: {e}")
        #end try
    #end def
    
    #关闭设备
    def close_device(self):
        try:
            # cleanup, reset state
            #self.__tis.set_state(Gst.State.NULL)
            
            if self.__tis is None: return            
            
            self.stop_capture()
            
            #显式地清理，避免循环引用
            self.__tis.Set_Image_Callback(None, None)
            self.__tis = None
            
        except Exception as e:
            logger.error(f"close device err---+++++++: {e}")
        #end try
    #end def
    
    #软触发
    def software_trigger(self):
        if self.__tis is None: return False
    
        try:
            # Send a software trigger
            self.__tis.Set_Property("Software Trigger", 1)
            return True
        except Exception as e:
            print(e)
        #end try
        return False
    #end def
    
    #获取属性
    def get_property(self, astrPropName):
        if self.__tis is None: return None
        
        try:
            #(ret, value,
            #min_value, max_value,
            #default_value, step_size,
            #value_type, flags,
            #category, group) = self.__tis.get_tcam_property(astrPropName)
            #return value if ret else None
            
            '''
            CameraProperty(status=True, value=3.1, min=0.0, max=1000000.0, default=3.1, 
            step=0.001, type='double', flags=0, category='Special', group='Trigger Mode')
            '''
            return self.__tis.Get_Property(astrPropName).value
         
        except Exception as e:
            print(e)
        #end try
        return None
    #end def
    
    #设置属性
    def set_property(self, astrPropName, astrValue):
        try:
            #self.__tis.set_tcam_property(astrPropName, astrValue)

            self.__tis.Set_Property(astrPropName, astrValue)
            return True
         
        except Exception as e:
            logger.error(f"set property err---+++++++: {e}")
        #end try
        
        return False
    #end def

#end class
