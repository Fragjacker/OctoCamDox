function camGrid(width, height, infoList, currentSelectedLayer, GCodeCoordinates, cameraCoordinates, canvas){
		var self = this;

		var _camBoxWidth = width;
    var _camBoxHeight= height;
		var _currentSelectedLayer = currentSelectedLayer;
		var _centerX = infoList[_currentSelectedLayer][4];
		var _centerY = infoList[_currentSelectedLayer][5];
		var _minX = infoList[_currentSelectedLayer][1];
		var _minY = infoList[_currentSelectedLayer][3];
		var _maxX = infoList[_currentSelectedLayer][0];
		var _maxY = infoList[_currentSelectedLayer][2];
		var _GCodeCoordinates = GCodeCoordinates;
		var _cameraCoordinates = cameraCoordinates;
		var _trayCanvas = canvas;


    self.erase = function() {
        _drawWhiteBox();
				_drawRectangularGrid();
    };

		self.drawGCodeLines = function() {
			// Draw the GCode coordinates on the canvas
			_drawLinesOnCanvas(_GCodeCoordinates,_currentSelectedLayer,0.25,"black");
		}

		self.drawAllGridCenters = function () {
			_drawAllGridCenters(_cameraCoordinates,_currentSelectedLayer);
		}

		self.drawCameraPathLines = function(){
			_drawLinesOnCanvas(_cameraCoordinates,_currentSelectedLayer,0.5,"rgb(255,0,0)");
		}

		self.drawCameragrid = function() {
			// Draw the Camera tile grid on the canvas
			_drawCamGrid(_currentSelectedLayer);
		}

		self.arrangeObjects = function() {
			_zoomDrawnObjects();
		}

		self.setCurrentLayer = function(inputLayer) {
			_currentSelectedLayer = inputLayer;
			// Now update all values dependant on it
			_centerX = infoList[_currentSelectedLayer][4];
			_centerY = infoList[_currentSelectedLayer][5];
			_minX = infoList[_currentSelectedLayer][1];
			_minY = infoList[_currentSelectedLayer][3];
			_maxX = infoList[_currentSelectedLayer][0];
			_maxY = infoList[_currentSelectedLayer][2];
		}

	function _drawLinesOnCanvas(inputList,inputLayer,linewidth,color) {
		var ctx = _trayCanvas.getContext("2d");
		if (_trayCanvas && _trayCanvas.getContext) {
				for (var i = 0 ; i < inputList[inputLayer].length-1 ; ++i){
					ctx.save();
					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;
					ctx.translate(-_centerX, -_centerY);
					ctx.translate(x, y);

					ctx.strokeStyle = color;
					ctx.lineWidth = linewidth;
					ctx.beginPath();
					ctx.moveTo(inputList[inputLayer][i][0], inputList[inputLayer][i][1]);
					ctx.lineTo(inputList[inputLayer][i+1][0], inputList[inputLayer][i+1][1]);
					ctx.stroke();
					ctx.restore();
			}
		}
	}

	function _drawWhiteBox() {
		if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
                var size_x = ctx.canvas.width;
                var size_y = ctx.canvas.height;
                var canvasBoxSize = _getCanvasBoxSize();

                //initialize white tray
                ctx.fillStyle = "white";
                ctx.fillRect(0,0,size_x,size_y);
                // ctx.strokeRect (0,0,size_x,size_y);
							}
					}
	}

    // draw a single grid box
    function _drawGridBox(x, y) {
        if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
								ctx.save();
								var posx = ctx.canvas.width/2;
								var posy = ctx.canvas.height/2;
								ctx.translate(-_centerX, -_centerY);
								ctx.translate(posx, posy);

                ctx.lineWidth = 0.5;
                ctx.strokeStyle = "green";
                ctx.strokeRect (x-(_camBoxWidth/2),y-(_camBoxHeight/2),_camBoxWidth,_camBoxHeight);
								ctx.restore();
            }
        }
    }

		function _drawCamGrid(inputLayer) {
			for (var i = 0 ; i < _cameraCoordinates[inputLayer].length ; ++i){
				// Don't draw coordinate boxes with the mode set to "walk"
				if(_cameraCoordinates[inputLayer][i][2] != "walk"){
					_drawGridBox(_cameraCoordinates[inputLayer][i][0], _cameraCoordinates[inputLayer][i][1]);
				}
			}
		}

    // returns the box size to use the available canvas-space in an optimal way
    function _getCanvasBoxSize() {
        var boxSize = 0;
        if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
                var size_x = ctx.canvas.width;
                var size_y = ctx.canvas.height;
                boxSize = Math.min((size_x-4)/_camBoxWidth, (size_y-4)/_camBoxHeight);
            }
        }
        return Math.floor(boxSize);
    }

		function _centerDrawnObjects(){
			if (_trayCanvas && _trayCanvas.getContext) {
					var ctx = _trayCanvas.getContext("2d");
					// Move object into center of Canvas
					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;

					ctx.translate(-centerX, -centerY);
					ctx.translate(x, y);
			}
		}

		function _zoomDrawnObjects(){
			if (_trayCanvas && _trayCanvas.getContext) {
					var ctx = _trayCanvas.getContext("2d");

					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;

					// Reset the transformation matrix back to default
					ctx.setTransform(1,0,0,1,0,0);
					// Zoom object
					ctx.translate(x, y);

					// Make the necessary transformations for the zoom
					var width = _maxX - _minX;
					var length = _maxY - _minY;
					var scaleF = width > length ? (x - _camBoxWidth) / width : (y - _camBoxHeight) / length;
					var factor = scaleF;
					ctx.scale(factor,factor);

					ctx.translate(-x, -y);
				}
		}

		function _drawAllGridCenters(inputList,inputLayer) {
			var ctx = _trayCanvas.getContext("2d");
			if (_trayCanvas && _trayCanvas.getContext) {
					// Draw start circle
					_drawCircle(inputList[inputLayer][0][0], inputList[inputLayer][0][1],2,"rgb(0,255,0)");
					for (var i = 1 ; i < inputList[inputLayer].length-1 ; ++i){
						_drawCircle(inputList[inputLayer][i][0], inputList[inputLayer][i][1],1,"rgb(255,170,0)");
				}
					_drawCircle(inputList[inputLayer][inputList[inputLayer].length-1][0],
					inputList[inputLayer][inputList[inputLayer].length-1][1],2,"rgb(255,0,0)");
			}
		}

		function _drawCircle(posX,posY,radius,color){
			if (_trayCanvas && _trayCanvas.getContext) {
					var ctx = _trayCanvas.getContext("2d");

					ctx.save();
					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;
					ctx.translate(-_centerX, -_centerY);
					ctx.translate(x, y);

					ctx.beginPath();
					ctx.fillStyle = color;
					ctx.arc(posX,posY,radius,0,(Math.PI*2),true);
					ctx.fill();
					// ctx.stroke();
					ctx.restore();
				}
		}

		function _drawRectangularGrid(){
			if (_trayCanvas && _trayCanvas.getContext) {
				var ctx = _trayCanvas.getContext("2d");

				var gridStep = 10;
				var minY = 0;
				var minX = 0;
				var maxX = ctx.canvas.width;
				var maxY = ctx.canvas.height;
				var zoomFactor = 1;

				ctx.fillStyle = "#dcdcdc";
        ctx.lineWidth = 0.1;

        //~~ grid starting from origin
        ctx.beginPath();
        for (x = 0; x <= maxX; x += gridStep) {
            ctx.moveTo(x * zoomFactor, -1 * minY * zoomFactor);
            ctx.lineTo(x * zoomFactor, maxY * zoomFactor);
        }
        ctx.stroke();

        ctx.beginPath();
        for (y = 0; y <= maxY; y += gridStep) {
            ctx.moveTo(minX * zoomFactor, y * zoomFactor);
            ctx.lineTo(maxX * zoomFactor, y * zoomFactor);
        }
        ctx.stroke();
			}
    }
}
