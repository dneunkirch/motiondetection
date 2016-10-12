<?php
header('Content-type: application/json; charset=UTF-8');
$previewImageSize = $_GET['previewImageSize'];
if(empty($previewImageSize)) {
	$previewImageSize = "640x360";
}
$cachefile = "events_$previewImageSize.cache";
if(file_exists($cachefile)) {
	include($cachefile);
	exit;
}
ob_start();
$files = scandir("events",1);
$json = "";
$data = [];
$uri = $_SERVER['REQUEST_URI'];
$file = basename($_SERVER["SCRIPT_FILENAME"]);
$segments = parse_url($uri);
$path = preg_replace('/'.$file.'$/', '', $segments['path']);
if (substr($path, -1) != '/' ) {
  $path = "$path/";
}
foreach ( $files as $i => $file) {
	if ( pathinfo($file, PATHINFO_EXTENSION) != "mp4" ) {
		continue;
	}
	$regex = "/^(.*)_(\d*).mp4/";
	preg_match($regex, $file, $result);
	$prefix = $result[1];


	$datetime = date_create_from_format('Y-m-d_H-i-s' ,$prefix);

	$date = date_format($datetime, 'd.m.y - H:i:s');
	$video = $path."events/$file";
	$image = $path."events/".$prefix."_".$previewImageSize.".jpg";
	$videoSize = filesize("events/$file");
	$videoLength = intval($result[2]);

	$entry = array("date" => $date, "video" => $video, "image" => $image, "size" => $videoSize, "duration" => $videoLength);
	array_push($data, $entry);
}
echo json_encode($data);
$fp = fopen($cachefile, 'w');
fwrite($fp, ob_get_contents());
fclose($fp);
ob_end_flush();
?>
