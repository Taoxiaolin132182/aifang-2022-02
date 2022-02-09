let takePhotoId = parseInt(Tool.getQueryStringByName ('takePhotoId'));
const canvasGroup ={};
for (let i = 1; i <= 4; i ++) {
	let keyName = "canvas" + i;
	canvasGroup[keyName] = new fabric.Canvas(document.getElementById(keyName))
}
let gImageScallingRatio = 1;
let imageArr = [];
let dataArray = [];
 
init();
function init(){
	getAnnotation (takePhotoId).then (res => {
		dataArray = res.data.ForeignFiberDetectionRecord;
		imageArr = res.data.ImageRecord;
        fabricRenderArr (imageArr,dataArray);
    });
}
function getAnnotation (takePhotoId) {
    return Tool.HTTPUtil.get ('/api/aicottonlocal/imageRecord/showImage', {
    	takePhotoId: takePhotoId,
    });
}
function fabricRenderArr (imageArr,dataArray){
	imageArr.forEach((item, index) => {
    	let canvasIndex = index + 1;
        var canvasName = "canvas" + canvasIndex;
		drawImg(item, index, canvasGroup[canvasName]).then(()=>{
			for(var prop in dataArray){
				if(item.imageId == prop){
					renderGroupArray(dataArray[prop], canvasGroup[canvasName]);
				}
			}
		})
	})
}
function drawImg(imagePath, index, canvas){
	return new Promise (function (resolve){
		let img = "/api/aicottonlocal/imageRecord/getImage?imagePath=" + imagePath.imageAddress;
        fabric.Image.fromURL(img, (img) => {
            renderImg(img, canvas);
            resolve();
        })
    })
}
function renderImg(img, currentCanvas){
    const imageNaturealWidth = img.width;
    const imageNaturealHeight = img.height;
    gImageScallingRatio = imageNaturealWidth / currentCanvas.width; //图片与画布的比例
    const imgShowHeight = imageNaturealHeight / gImageScallingRatio; //图片在画布中应该显示的高度
    currentCanvas.setHeight(imgShowHeight); //图片宽度与画布宽度一致，高度与缩小后的图片一致。
    img.set({
        // 通过scale来设置图片大小，这里设置和画布一样大
        scaleX: currentCanvas.width / img.width,
        scaleY: currentCanvas.height / img.height,
    });
    // 设置背景
    currentCanvas.setBackgroundImage(img, currentCanvas.renderAll.bind(currentCanvas));
    currentCanvas.renderAll();
    currentCanvas.selection = false;
}
function renderGroupArray (array, currentCanvas){
	array.forEach(_element => {
		if(_element.leftTopX){
			text = drawText(_element);
		    rect = drawRect(_element);
		    currentCanvas.add(rect);
		    currentCanvas.add(text);
			rect.selectable = false;
			text.selectable = false;
		}
	});
}
function drawRect (_element){
    var rect = new fabric.Rect({
        top : Math.round(_element.leftTopY/gImageScallingRatio),
        left : Math.round(_element.leftTopX/gImageScallingRatio),
        width : Math.round((_element.rightBottomX - _element.leftTopX)/gImageScallingRatio),
        height : Math.round((_element.rightBottomY - _element.leftTopY)/gImageScallingRatio),
        fill:'transparent',
        stroke: "red",
        strokeWidth: 2,
        strokeUniform: true
    });
    return rect;
}
function drawText (_element){
	var text = new fabric.Text(_element.labelType, {
        fontFamily: 'Comic Sans',
        fontSize: 12,
        fill: 'red',
        left: _element.rightBottomX/gImageScallingRatio,
        top: _element.rightBottomY/gImageScallingRatio
    });
	return text;
}
