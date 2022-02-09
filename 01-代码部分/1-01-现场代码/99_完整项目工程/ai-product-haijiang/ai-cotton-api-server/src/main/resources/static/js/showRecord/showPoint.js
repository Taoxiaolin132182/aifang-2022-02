let roundId = parseInt(Tool.getQueryStringByName ('roundId'));
let writeTakePhotoTimes = parseInt(Tool.getQueryStringByName ('writeTakePhotoTimes'));
let realTakePhotoTimes = parseInt(Tool.getQueryStringByName ('realTakePhotoTimes'));
let jCurrentMessage = document.querySelector ('.j-message');
let succCountAllTotal = 0;
let totalCountAllTotal = 0;
let calPointData = [[],[],[],[],[]]; //写入拍摄点的数据
let realPointData = [[],[],[],[],[]];  //实际拍摄点的数据
let line, circle, text;
const canvasGroup ={};
const step = 8000;
for (let i = 1; i <= 5; i ++) {
	let keyName = "canvas" + i;
	canvasGroup[i] = new fabric.Canvas(document.getElementById(keyName))
}
let cameraWidth = 550;
let directionText = {'left':50, 'textTop': 10, 'text':''}; //方向文字数据

init();
function init(){
	renderLine().then(()=>{
        getAnnotation (roundId).then (res => {
            let data = res.data;
            if(data[0].forwardDirection == 1){
                directionText.text = '正向';
            }else {
                directionText.text = '反向';
            }
            let direction = drawText(directionText);
            canvasGroup[1].add(direction);
            data.forEach((item, index) => {
            	succCountAllTotal = succCountAllTotal + item.succCount;
            	totalCountAllTotal = totalCountAllTotal + item.totalCount;
                let key = Math.floor(item.calculatePhotoLocation / step);
                if(key > 4) return;
                let calLeft = 50 + (item.calculatePhotoLocation - step * key) / 4;
                calPointData[key].push({'left': calLeft, 'top': 75, 'color': 'green', 'takePhotoId': item.takePhotoId});
                let realLeft = 50 + (item.photoMachineLocation - step * key) / 4;
                let totalText = "" + item.totalCount;
                let succText = "" + item.succCount;
                realPointData[key][index] = {'left': realLeft, 'top': 110, 'color': 'blue', 'takePhotoId': item.takePhotoId, 'totalText': totalText, 'totalTextTop': 135, 'succText': succText, 'succTextTop': 160};
            })
    //		for(let i = 1; i < realPointData.length; i++){
    //			let point = realPointData[i].left - cameraWidth;
    //			if(realPointData[i-1].left != point){
    //				realPointData[i].color = 'red';
    //			}
    //		}
            let content = `<h2>写入拍照次数：${writeTakePhotoTimes}</h2>
            			   <h2>实际拍照次数：${realTakePhotoTimes}</h2>
            			   <h2>异纤总数：${totalCountAllTotal}</h2>
            			   <h2>异纤抓取数量：${succCountAllTotal}</h2>`
            jCurrentMessage.innerHTML = content;
            for(var i = 0; i < calPointData.length; i ++){
                renderCircleArray (calPointData[i], canvasGroup[i+1]);
                renderCircleArray (realPointData[i], canvasGroup[i+1]);
            }
        })
    })
}
function renderLine(){
    return new Promise (function (resolve){
        for (var prop in canvasGroup){
            canvasGroup[prop].setWidth(2500);
            canvasGroup[prop].setHeight(300);
            canvasGroup[prop].renderAll();
            canvasGroup[prop].selection = false;

            let lineDate = [50, 100, 2050, 100];
            line = drawLine(lineDate);
            canvasGroup[prop].add(line);
        }
        resolve();
    })
}
function getAnnotation (roundId) {
    return Tool.HTTPUtil.get ('/api/aicottonlocal/detailOperateDate/list', {
    	roundId: roundId
    });
}
function renderCircleArray (array, canvas){
	array.forEach(_element => {
		if(_element.left){
			let group;
			let groupArr = [];
			circle = drawCircle(_element);
			if(_element.totalText){
				let totalNum = drawTotalText(_element);
				let succNum = drawSuccText (_element);
				groupArr = [circle, totalNum, succNum];
			}else{
				groupArr = [circle];
			}
			group = drawGroup(groupArr, _element);
			canvas.add(group);
		}
	});
}
function drawLine(_element){
    var line = new fabric.Line(_element,{
        fill:'black',
        stroke: "black",
        strokeWidth: 2,
        selectable: false
    });
    return line;
}
function drawCircle (_element){
	var circle = new fabric.Circle({
		left: _element.left,
	    top: _element.top,
	    radius: 8,
	    fill: _element.color
    });
	return circle;
}
function drawText (_element){
	var text = new fabric.Text(_element.text, {
        fontFamily: 'Comic Sans',
        fontSize: 16,
        fill: 'black',
        left: _element.left,
        top: _element.textTop,
        selectable: false
    });
	return text;
}
function drawTotalText (_element){
	var text = new fabric.Text(_element.totalText, {
        fontFamily: 'Comic Sans',
        fontSize: 16,
        fill: 'black',
        left: _element.left + 3,
        top: _element.totalTextTop,
        selectable: false
    });
	return text;
}
function drawSuccText (_element){
	var text = new fabric.Text(_element.succText, {
        fontFamily: 'Comic Sans',
        fontSize: 16,
        fill: 'red',
        left: _element.left + 3,
        top: _element.succTextTop,
        selectable: false
    });
	return text;
}
function drawGroup(groupArr, _element) {
    var group = new fabric.Group(groupArr, {
        strokeUniform: true,
        lockScalingFlip: true,
        hasControls: false,
        strokeWidthUnscaled: 1,
        padding: -1.8,
        rotatingPointOffset: 8,
	    takePhotoId: _element.takePhotoId
    });
    return group;
}

for (var prop in canvasGroup){
	canvasGroup[prop].on('mouse:up', function (e) {
	    let currentCanvasArr = e.target.canvas.getActiveObject();
	    if(currentCanvasArr){
	    	let takePhotoId = currentCanvasArr.takePhotoId;
    	    window.open('/foreignFiberDetectionRecord/list?takePhotoId=' + takePhotoId);
	    }
	})
}






