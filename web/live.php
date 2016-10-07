<?php
header('Content-type: application/json; charset=UTF-8');
$filesystemFolder = "/run/shm/live";
$urlPrefix = "/motion/live";
$files = scandir($filesystemFolder, 1);
$date = "";
$filename = "";
$dateformat = "d.m.y - H:i:s";
foreach ( $files as $i => $file ) {
	if ( pathinfo($file, PATHINFO_EXTENSION) != "jpg" ) {
		continue;
	}
	$filename = "$urlPrefix/$file";
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