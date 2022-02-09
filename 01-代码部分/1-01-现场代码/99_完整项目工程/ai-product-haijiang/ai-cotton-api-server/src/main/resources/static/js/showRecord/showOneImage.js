let imageId = parseInt(Tool.getQueryStringByName ('imageId'));
let canvas = new fabric.Canvas(document.getElementById("canvas"));
let gImageScallingRatio = 1;
let imagePath;
let aiResultJson;
let dataArray = [];
 
init();
function init(){
	getAnnotation (imageId).then (res => {
		aiResultJson = res.data.aiResultJson;
		imagePath = res.data.imageAddress;
//		imagePath = "http://t9.baidu.com/it/u=583874135,70653437&fm=79&app=86&f=JPEG?w=3607&h=2408"
		let boxes = JSON.parse(aiResultJson.replace(/\'/g,'\"')).data.boxes;
		let labels = JSON.parse(aiResultJson.replace(/\'/g,'\"')).data.labels;
		boxes.forEach((itm, index) =>{
			let label_type = "" +labels[index];
			dataArray[index] = {"leftTopX":itm[0],"leftTopY":itm[1],"rightBottomX":itm[2],"rightBottomY":itm[3],"labelType":label_type};
		})
        fabricRenderArr (imagePath,dataArray);
    });
}
function getAnnotation (imageId) {
    return Tool.HTTPUtil.get ('/api/aicottonlocal/imageRecord/showOneImage', {
    	imageId: imageId,
    });
}
function fabricRenderArr (imagePath,dataArray){
	drawImg(imagePath).then(()=>{
		if(dataArray != null){
			renderGroupArray(dataArray);
		}
	})
}
function drawImg(imagePath){
	return new Promise (function (resolve){
//		let img = imagePath;
		let img = "/api/aicottonlocal/imageRecord/getImage?imagePath=" + imagePath;
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
function renderGroupArray (array){
	array.forEach(_element => {
		if(_element.leftTopX){
			text = drawText(_element);
		    rect = drawRect(_element);
		    canvas.add(rect);
		    canvas.add(text);
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
