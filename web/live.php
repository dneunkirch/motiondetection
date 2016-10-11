<?php
header('Content-type: application/json; charset=UTF-8');
$filesystemFolder = "/run/shm/live";
$files = scandir($filesystemFolder, 1);
$date = "";
$filename = "";
$dateformat = "d.m.y - H:i:s";

$uri = $_SERVER['REQUEST_URI'];
$file = basename($_SERVER["SCRIPT_FILENAME"]);
$path = preg_replace('/'.$file.'$/', '', $uri);
if (substr($path, -1) != '/' ) {
  $path = "$path/";
}

foreach ( $files as $i => $file ) {
	if ( pathinfo($file, PATHINFO_EXTENSION) != "jpg" ) {
		continue;
	}
	$filename = $path."live/$file";
	$dateTimestamp = filemtime("$filesystemFolder/$file");
	$date = date($dateformat, $dateTimestamp);
	break;
}
if ( $filename == "" ) {
  $filename = "/static/offline.jpg";
  $date = date($dateformat);
}
$entry = array(
		"url" => $filename,
		"date" => $date
	      );
echo json_encode($entry);
?>