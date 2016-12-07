var rects = {};

const DRAW_TYPE_PEN = 1;
const DRAW_TYPE_RECT = 2;
const DRAW_MODE_ADD = 1;
const DRAW_MODE_REMOVE = 2;
const RECT_SIZE = 5;
const MOTION_BLOCK_REGEX = new RegExp("([0-9]+),([0-9]+)");

var penStrength = 40;
var drawType = DRAW_TYPE_PEN;
var drawMode = DRAW_MODE_ADD;
var startX = 0, startY = 0, endX = 0, endY = 0;
var active = false;
var grid = $('.grid');
var blacklist = document.getElementById('blacklist');
var ctx = blacklist.getContext('2d');
ctx.fillStyle = 'rgba(255, 0, 0, 1)';


refreshImage();
prepareData();
displayCurrentBlacklist();
watchPenStrengthChanges();
watchMarkerTypeChanges();
watchMarkerModeChanges();
watchKeyInputs();
watchMouseEvents();
generateBlacklistOnFormSubmit();


function displayCurrentBlacklist() {
    let blacklist = $('#blacklist');
    let currentBlacklist = blacklist.data('current');
    let hasBlacklist = blacklist.data('exists');
    if (!hasBlacklist || currentBlacklist === '') {
        $.map(rects, function (rect) {
            rect.active = false;
        })
        return;
    }
    currentBlacklist.split(', ').forEach((el) => {
        let match = MOTION_BLOCK_REGEX.exec(el);
        if (match) {
            let y = match[1];
            let x = match[2];
            let key = keyName(x, y);
            rects[key].active = false;
        }
    });
    drawBlacklist();
}

function prepareData() {
    for (var x = 0; x < 960 / RECT_SIZE; x++) {
        for (var y = 0; y < 540 / RECT_SIZE; y++) {
            rects[keyName(x, y)] = {
                'active': true,
                'x': x,
                'y': y
            }
        }
    }
}

function keyName(x, y) {
    return `(${y},${x})`;
}

function refreshImage() {
    $.getJSON('live.php').then(function (data) {
        $('.image').css('background-image', `url(${data.url})`);
    })
}

function watchPenStrengthChanges() {
    $('input[name=pen-strength]').change(function () {
        penStrength = $(this).val() * RECT_SIZE;
    });
}

function watchMarkerTypeChanges() {
    $('input[name=marker-type]').change(function () {
        drawType = parseInt($(this).val());
        if (drawType === DRAW_TYPE_RECT) {
            $('.pen-settings').hide();
        } else if (drawType === DRAW_TYPE_PEN) {
            $('.pen-settings').show();
        }
    });
}

function watchMarkerModeChanges() {
    $('input[name=marker-mode]').change(function () {
        drawMode = parseInt($(this).val());
    });
}

function watchKeyInputs() {
    $('body').on('keypress', function (e) {
        if (e.keyCode === 109) {
            $('input[name=marker-mode]:not(:checked)').prop('checked', true).trigger('change');
        } else if (e.keyCode === 116) {
            $('input[name=marker-type]:not(:checked)').prop('checked', true).trigger('change');
        }
    })
}

function generateBlacklistOnFormSubmit() {
    $('#create-blacklist').click(function () {
        let result = Object.keys(rects).map(function (key) {
            return rects[key];
        }).filter(el => !el.active).map(el => keyName(el.x, el.y)).join(', ');
        $('input[name=motionblocks]').val(result);
    });
}

function drawRect(startX, startY, endX, endY, finish) {
    var x = calcPoint(startX), x2 = calcPoint(endX);
    var y = calcPoint(startY), y2 = calcPoint(endY);

    var w = x2 - x;
    var h = y2 - y;

    w += w > 0 ? RECT_SIZE : -RECT_SIZE;
    h += h > 0 ? RECT_SIZE : -RECT_SIZE;

    if (w < 0) {
        x += w;
        w *= -1;
    }
    if (h < 0) {
        y += h;
        h *= -1;
    }

    if (finish) {
        drawRects(x, y, w / RECT_SIZE, h / RECT_SIZE)
    } else {
        drawBlacklist();
        if (DRAW_MODE_ADD === drawMode) {
            ctx.fillRect(x, y, w, h);
        } else if (DRAW_MODE_REMOVE === drawMode) {
            ctx.clearRect(x, y, w, h);
        }
    }
}

function calcPoint(point) {
    return parseInt(point / RECT_SIZE) * RECT_SIZE;
}

function drawPen(startX, startY) {
    let x = calcPoint(startX);
    let y = calcPoint(startY);
    let count = penStrength / RECT_SIZE;
    drawRects(x, y, count, count);
}

function drawRects(x, y, xCount, yCount) {
    for (var xOffset = 0; xOffset < xCount; xOffset++) {
        for (var yOffset = 0; yOffset < yCount; yOffset++) {
            let motionBlock = {
                'x': x + (xOffset * RECT_SIZE),
                'y': y + (yOffset * RECT_SIZE)
            };
            let index = keyName(x / RECT_SIZE + xOffset, y / RECT_SIZE + yOffset);
            let rect = rects[index];
            if (rect === undefined) {
                continue;
            }
            let isActive = rect.active;
            if (drawMode === DRAW_MODE_REMOVE && isActive) {
                ctx.clearRect(motionBlock.x, motionBlock.y, RECT_SIZE, RECT_SIZE);
                rects[index].active = false;
            } else if (drawMode === DRAW_MODE_ADD && !isActive) {
                ctx.fillRect(motionBlock.x, motionBlock.y, RECT_SIZE, RECT_SIZE);
                rects[index].active = true;
            }
        }
    }
    drawBlacklist();
}

function drawBlacklist() {
    ctx.clearRect(0, 0, 960, 540);
    Object.keys(rects)
        .map(key => rects[key])
        .filter(el => el.active)
        .forEach(el => ctx.fillRect(el.x * RECT_SIZE, el.y * RECT_SIZE, RECT_SIZE, RECT_SIZE));
}

function draw(startX, startY, endX, endY, finish) {
    if (drawType == DRAW_TYPE_PEN) {
        drawPen(startX, startY);
    } else if (drawType === DRAW_TYPE_RECT) {
        drawRect(startX, startY, endX, endY, finish);
    }
}

function watchMouseEvents() {
    grid.mousedown(function (e) {
        active = true;
        startX = e.offsetX;
        startY = e.offsetY;
    });

    grid.mouseup(function (e) {
        active = false;
        endX = e.offsetX;
        endY = e.offsetY;
        draw(startX, startY, endX, endY, true);
    });

    grid.mouseout(function (e) {
        if (active) {
            active = false;
            if (drawType == DRAW_TYPE_RECT) {
                endX = e.offsetX;
                endY = e.offsetY;
                draw(startX, startY, endX, endY, true);
            }
        }
    });

    grid.mousemove(function (e) {
        if (!active) {
            return;
        }
        if (drawType === DRAW_TYPE_PEN) {
            startX = e.offsetX;
            startY = e.offsetY;
        } else {
            endX = e.offsetX;
            endY = e.offsetY;
        }
        draw(startX, startY, endX, endY, false);
    });
}