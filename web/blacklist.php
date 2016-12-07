<?php
    $motionblocks = $_POST['motionblocks'];
    if( isset($motionblocks) ) {
       $file = fopen("roi.txt", "w");
       fwrite($file, $motionblocks);
       fclose($file);
       header('Location: blacklist.php');
    }
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Motion Detection Blacklist</title>
    <link rel="stylesheet" href="static/blacklist.css"/>
</head>
<body>

<div class="container">
    <div class="image"></div>
    <canvas id="blacklist" width="960" height="540" data-exists='<?= file_exists("roi.txt"); ?>' data-current='<?= file_get_contents("roi.txt"); ?>'></canvas>
    <div class="grid"></div>
</div>

<div class="container">

    <div class="control">
        Type (Key: T):<br/>
        Pen: <input type="radio" name="marker-type" value="1" checked/><br/>
        Rect: <input type="radio" name="marker-type" value="2"/><br/>

        <div class="pen-settings">
            Pen strength: <input name="pen-strength" type="range" min="1" max="10" value="5"/><br/><br/>
        </div>

        Mode (Key: M):<br/>
        Add to blacklist: <input type="radio" name="marker-mode" value="1" checked/><br/>
        Remove from blacklist: <input type="radio" name="marker-mode" value="2"/><br/>

        <form method="POST">


             <input type="hidden" value="" name="motionblocks"/>
            <button id="create-blacklist">save</button>
        </form>
    </div>
</div>

<script src="static/jquery-3.1.1.min.js"></script>
<script src="static/blacklist.js"></script>


</body>
</html>