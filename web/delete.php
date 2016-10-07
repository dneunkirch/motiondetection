<?php
function endsWith($haystack, $needle) {
	return $needle === "" || strpos($haystack, $needle, strlen($haystack) - strlen($needle)) !== FALSE;
}
$file = urldecode($_GET["file"]);
if(!isset($file) || !endsWith($file, ".mp4")) {
	exit;
}
$file = getcwd() . "$file";
if(!file_exists($file)) {
	exit;
}
$prefix = substr($file, 0, -strlen(strrchr($file, "_"))). "*";
array_map('unlink', glob($prefix));
$resetCache = "rm " . getcwd() . "/events_*.cache";
exec($resetCache);
?>